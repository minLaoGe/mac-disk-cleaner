"""Transfer regression tests; all mutations stay inside temporary directories."""
import importlib.util
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

spec = importlib.util.spec_from_file_location('cleaner_app', Path(__file__).parents[1] / 'app.py')
cleaner = importlib.util.module_from_spec(spec)
# Avoid loading or rewriting the user's scan cache during the test module import.
with patch.object(Path, 'exists', return_value=False):
    spec.loader.exec_module(cleaner)


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.dest = self.root / 'destination'
        self.dest.mkdir()
        cleaner.CACHE_FILE = self.root / 'test-cache.json'
        cleaner.scanner = cleaner.ScanManager()

    def transfer(self, source, delete=False, directory=False, destination=None):
        return cleaner.transfer_files(cleaner.TransferRequest(
            paths=[str(source)], destination=str(destination or self.dest),
            delete_original=delete, whole_directory=directory))

    def test_copy_file_keeps_original(self):
        source = self.root / 'file.dat'
        source.write_bytes(b'original bytes')
        result = self.transfer(source)
        self.assertEqual(result['success_count'], 1)
        self.assertEqual(source.read_bytes(), (self.dest / source.name).read_bytes())

    def test_move_directory_includes_hidden_empty_nested_and_symlink(self):
        source = self.root / 'folder'
        (source / 'nested' / 'empty').mkdir(parents=True)
        (source / '.hidden').write_bytes(b'hidden')
        (source / 'nested' / 'small').write_bytes(b'small')
        (source / 'link').symlink_to('nested/small')
        cleaner.scanner.results = [{'path': str(source / '.hidden'), 'size': 6, 'mtime': 0}]
        cleaner.scanner.total_found_size = 6
        result = self.transfer(source, True, True)
        self.assertEqual(result['errors'], [])
        self.assertFalse(source.exists())
        target = self.dest / 'folder'
        self.assertTrue((target / 'nested' / 'empty').is_dir())
        self.assertEqual((target / '.hidden').read_bytes(), b'hidden')
        self.assertTrue((target / 'link').is_symlink())
        self.assertEqual(cleaner.scanner.results, [])

    def test_copy_directory_keeps_source_and_move_file_deletes_source(self):
        source = self.root / 'folder'
        source.mkdir()
        (source / 'file').write_text('payload')
        self.assertEqual(self.transfer(source, directory=True)['success_count'], 1)
        self.assertTrue((source / 'file').exists())
        lone = self.root / 'lone'
        lone.write_text('payload')
        self.assertEqual(self.transfer(lone, delete=True)['success_count'], 1)
        self.assertFalse(lone.exists())

    def test_existing_target_never_overwritten(self):
        source = self.root / 'file'
        source.write_text('new')
        (self.dest / 'file').write_text('existing')
        result = self.transfer(source, True)
        self.assertEqual(result['success_count'], 1)
        self.assertEqual((self.dest / 'file').read_text(), 'existing')
        self.assertEqual((self.dest / 'file (1)').read_text(), 'new')
        self.assertFalse(source.exists())

    def test_batch_same_names_rename_and_delete_only_verified_sources(self):
        sources = []
        for parent, name, payload in [('a', 'model.bin', b'first'), ('b', 'model.bin', b'second'), ('c', 'model (1).bin', b'third'), ('d', 'MODEL.bin', b'fourth')]:
            folder = self.root / parent
            folder.mkdir()
            source = folder / name
            source.write_bytes(payload)
            sources.append(source)
        result = cleaner.transfer_files(cleaner.TransferRequest(
            paths=[str(path) for path in sources], destination=str(self.dest), delete_original=True))
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['success_count'], 4)
        for item, payload in zip(result['results'], [b'first', b'second', b'third', b'fourth']):
            self.assertEqual(Path(item['target']).read_bytes(), payload)
            self.assertFalse(Path(item['source']).exists())
        self.assertEqual((self.dest / 'model (1).bin').read_bytes(), b'third')
        self.assertEqual(len({Path(item['target']).name.casefold() for item in result['results']}), 4)

    def test_directory_name_conflict_renames_without_merging(self):
        source = self.root / 'folder'
        source.mkdir()
        (source / '.hidden').write_text('new')
        (self.dest / 'folder').mkdir()
        (self.dest / 'folder' / 'existing').write_text('keep')
        result = self.transfer(source, True, True)
        self.assertEqual(result['errors'], [])
        self.assertEqual((self.dest / 'folder' / 'existing').read_text(), 'keep')
        self.assertEqual((self.dest / 'folder (1)' / '.hidden').read_text(), 'new')
        self.assertFalse(source.exists())

    def test_reject_self_and_nested_destination(self):
        source = self.root / 'folder'
        (source / 'nested').mkdir(parents=True)
        for destination in (self.root, source / 'nested'):
            with self.assertRaises(HTTPException):
                self.transfer(source, True, True, destination)
        self.assertTrue(source.exists())

    def test_copy_failure_and_verification_failure_keep_original(self):
        source = self.root / 'file'
        source.write_text('payload')
        with patch.object(cleaner, 'copy_transfer_file', side_effect=OSError('disk full')):
            self.assertEqual(self.transfer(source, True)['success_count'], 0)
        self.assertTrue(source.exists())
        if (self.dest / 'file').exists():
            (self.dest / 'file').unlink()
        with patch.object(cleaner, 'transfer_manifest', side_effect=[{'x': 'original'}, {'x': 'corrupt'}]):
            self.assertEqual(self.transfer(source, True)['success_count'], 0)
        self.assertTrue(source.exists())

    def wait_job(self):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            status = cleaner.get_transfer_status()
            if status['status'] != 'running':
                return status
            time.sleep(.01)
        self.fail('Background task did not finish')

    def test_live_chunk_progress_then_verified_delete(self):
        source = self.root / 'large.bin'
        source.write_bytes(b'x' * (9 * 1024 * 1024))
        paused, resume = threading.Event(), threading.Event()
        original_advance = cleaner.TransferProgress.advance
        def observe(progress, path, amount):
            original_advance(progress, path, amount)
            if progress.snapshot()['phase'] == 'copying' and amount > 0 and not paused.is_set():
                paused.set()
                resume.wait(5)
        with patch.object(cleaner.TransferProgress, 'advance', observe):
            cleaner.start_transfer(cleaner.TransferRequest(paths=[str(source)], destination=str(self.dest), delete_original=True))
            try:
                self.assertTrue(paused.wait(3))
                status = cleaner.get_transfer_status()
                self.assertEqual(status['status'], 'running')
                self.assertEqual(status['phase'], 'copying')
                self.assertGreater(status['copied_bytes'], 0)
                self.assertLess(status['copied_bytes'], status['total_bytes'])
                self.assertGreater(status['percent'], 0)
                self.assertLess(status['percent'], 100)
                self.assertEqual(status['items'][0]['status'], 'copying')
                self.assertTrue(source.exists())
                with self.assertRaises(HTTPException):
                    cleaner.start_transfer(cleaner.TransferRequest(paths=[str(source)], destination=str(self.dest)))
            finally:
                resume.set()
            result = self.wait_job()
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['percent'], 100)
        self.assertEqual(result['work_bytes'], result['total_bytes'] * 4)
        self.assertEqual(result['copied_files'], 1)
        self.assertEqual(result['items'][0]['status'], 'completed')
        self.assertFalse(source.exists())
        self.assertFalse(cleaner.transfer_lock.locked())

    def test_background_failure_details_and_lock_release(self):
        source = self.root / 'source'
        source.write_text('keep original')
        with patch.object(cleaner, 'copy_transfer_file', side_effect=OSError('disk full')):
            cleaner.start_transfer(cleaner.TransferRequest(paths=[str(source)], destination=str(self.dest), delete_original=True))
            result = self.wait_job()
        self.assertEqual(result['status'], 'partial')
        self.assertEqual(result['items'][0]['status'], 'failed')
        self.assertIn('disk full', result['items'][0]['error'])
        self.assertTrue(source.exists())
        self.assertFalse(cleaner.transfer_lock.locked())
        cleaner.start_transfer(cleaner.TransferRequest(paths=[str(self.root / 'missing')], destination=str(self.dest)))
        self.assertEqual(self.wait_job()['status'], 'failed')
        self.assertFalse(cleaner.transfer_lock.locked())

    def test_scanning_and_protected_paths_rejected(self):
        cleaner.scanner.is_scanning = True
        with self.assertRaises(HTTPException):
            self.transfer(self.root)
        cleaner.scanner.is_scanning = False
        with self.assertRaises(HTTPException):
            self.transfer(Path.home(), True, True)


if __name__ == '__main__':
    unittest.main()
