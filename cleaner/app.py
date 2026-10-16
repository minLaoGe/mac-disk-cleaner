import os
import sys
import json
import time
import shutil
import subprocess
import threading
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

CACHE_FILE = Path(__file__).parent / "scan_cache.json"

app = FastAPI(title="Mac Big File Cleaner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 保护列表：严禁删除的关键系统目录
PROTECTED_PATHS = {
    "/", "/System", "/bin", "/sbin", "/usr", "/etc", "/var",
    "/Applications", "/Library", os.path.expanduser("~")
}

def is_safe_to_delete(path_str: str) -> bool:
    try:
        resolved = Path(path_str).resolve()
        if str(resolved) in PROTECTED_PATHS:
            return False
        # 不允许删除系统核心系统根
        parts = resolved.parts
        if len(parts) <= 2:  # 如 / or /System
            return False
        if parts[1] in ["System", "bin", "sbin", "usr", "etc", "var"] and not str(resolved).startswith(os.path.expanduser("~")):
            return False
        return True
    except Exception:
        return False

def format_size(bytes_num: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.1f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} PB"

def format_decimal_size(bytes_num: float) -> str:
    """按 macOS 官方十进制标称 (1000进制) 格式化磁盘容量，与访达/系统设置 100% 对齐"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_num < 1000.0:
            return f"{bytes_num:.1f} {unit}"
        bytes_num /= 1000.0
    return f"{bytes_num:.1f} PB"

def get_file_category(ext: str) -> str:
    ext = ext.lower()
    categories = {
        "model": [".bin", ".safetensors", ".gguf", ".pt", ".pth", ".onnx", ".ckpt", ".h5"],
        "video": [".mp4", ".mov", ".mkv", ".avi", ".wmv", ".flv", ".webm", ".m4v"],
        "archive": [".zip", ".tar", ".gz", ".7z", ".rar", ".bz2", ".xz", ".dmg", ".iso", ".pkg"],
        "audio": [".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg"],
        "image": [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff", ".psd", ".raw"],
        "document": [".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"],
    }
    for cat, exts in categories.items():
        if ext in exts:
            return cat
    return "other"

class ScanManager:
    def __init__(self):
        self.is_scanning = False
        self.stop_requested = False
        self.current_dir = ""
        self.target_path = ""
        self.scanned_files_count = 0
        self.scanned_dirs_count = 0
        self.start_time = 0.0
        self.elapsed_seconds = 0.0
        self.results = []
        self.total_found_size = 0
        self.is_cached = False
        self.cached_at = ""
        self.lock = threading.Lock()
        self.scan_thread: Optional[threading.Thread] = None

        # 服务启动时自动恢复上次扫描缓存
        self.load_cache()

    def load_cache(self):
        try:
            if CACHE_FILE.exists():
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.results = data.get("results", [])
                    self.total_found_size = data.get("total_found_size", 0)
                    self.current_dir = data.get("current_dir", "")
                    self.target_path = data.get("target_path", "")
                    self.scanned_files_count = data.get("scanned_files_count", 0)
                    self.scanned_dirs_count = data.get("scanned_dirs_count", 0)
                    self.elapsed_seconds = data.get("elapsed_seconds", 0.0)
                    self.cached_at = data.get("cached_at", "")
                    self.is_cached = bool(self.results)
        except Exception as e:
            print(f"[MacCleaner] 读取扫描缓存失败: {e}")

    def save_cache(self):
        try:
            data = {
                "cached_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "target_path": self.target_path or self.current_dir,
                "current_dir": self.current_dir,
                "scanned_files_count": self.scanned_files_count,
                "scanned_dirs_count": self.scanned_dirs_count,
                "elapsed_seconds": round(self.elapsed_seconds, 1),
                "total_found_size": self.total_found_size,
                "total_found_size_formatted": format_size(self.total_found_size),
                "found_count": len(self.results),
                "results": self.results
            }
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.is_cached = True
            self.cached_at = data["cached_at"]
        except Exception as e:
            print(f"[MacCleaner] 保存扫描缓存失败: {e}")

    def clear_cache(self):
        with self.lock:
            self.results = []
            self.total_found_size = 0
            self.is_cached = False
            self.cached_at = ""
            self.scanned_files_count = 0
            self.scanned_dirs_count = 0
            self.elapsed_seconds = 0.0
            if CACHE_FILE.exists():
                try:
                    CACHE_FILE.unlink()
                except Exception:
                    pass

    def start(self, target_path: str, min_size_bytes: int, include_hidden: bool, max_depth: Optional[int] = None):
        with self.lock:
            if self.is_scanning:
                return False
            self.is_scanning = True
            self.stop_requested = False
            self.target_path = target_path
            self.current_dir = target_path
            self.scanned_files_count = 0
            self.scanned_dirs_count = 0
            self.start_time = time.time()
            self.elapsed_seconds = 0.0
            self.results = []
            self.total_found_size = 0
            self.is_cached = False

        self.scan_thread = threading.Thread(
            target=self._scan_worker,
            args=(target_path, min_size_bytes, include_hidden, max_depth),
            daemon=True
        )
        self.scan_thread.start()
        return True

    def stop(self):
        with self.lock:
            self.stop_requested = True

    def _scan_worker(self, target_path: str, min_size_bytes: int, include_hidden: bool, max_depth: Optional[int]):
        root_path = Path(target_path).expanduser().resolve()
        root_depth = len(root_path.parts)

        try:
            for root, dirs, files in os.walk(str(root_path), followlinks=False):
                if self.stop_requested:
                    break

                current_p = Path(root)
                current_depth = len(current_p.parts) - root_depth

                if not include_hidden:
                    # 过滤隐藏文件夹
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                else:
                    # 即使包含隐藏文件，也跳过无大文件的依赖库黑洞目录，避免死耗数百万小文件
                    dirs[:] = [d for d in dirs if d not in {".git", ".nvm", ".npm", ".cargo", ".rustup", ".gradle", ".m2", "__pycache__"}]

                # 始终跳过庞大的依赖文件夹
                dirs[:] = [d for d in dirs if d not in {"node_modules", "site-packages"}]
                
                if max_depth is not None and current_depth >= max_depth:
                    dirs[:] = []

                with self.lock:
                    self.current_dir = root
                    self.scanned_dirs_count += 1
                    self.elapsed_seconds = time.time() - self.start_time

                for f in files:
                    if self.stop_requested:
                        break

                    if not include_hidden and f.startswith('.'):
                        continue

                    file_path = os.path.join(root, f)
                    self.scanned_files_count += 1

                    try:
                        stat = os.lstat(file_path)
                        # 跳过符号链接
                        if os.path.islink(file_path):
                            continue

                        size = stat.st_size
                        if size >= min_size_bytes:
                            ext = os.path.splitext(f)[1]
                            item = {
                                "id": f"{stat.st_dev}_{stat.st_ino}",
                                "name": f,
                                "path": file_path,
                                "size": size,
                                "size_formatted": format_size(size),
                                "ext": ext,
                                "category": get_file_category(ext),
                                "mtime": stat.st_mtime,
                                "mtime_formatted": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))
                            }
                            with self.lock:
                                self.results.append(item)
                                self.total_found_size += size
                    except (PermissionError, FileNotFoundError, OSError):
                        continue
        finally:
            with self.lock:
                self.is_scanning = False
                self.elapsed_seconds = time.time() - self.start_time
                # 按大小倒序排序
                self.results.sort(key=lambda x: x["size"], reverse=True)
                # 扫描结束或终止时自动持久化缓存到磁盘
                if self.results:
                    self.save_cache()

    def get_status(self):
        with self.lock:
            if self.is_scanning:
                self.elapsed_seconds = time.time() - self.start_time
            return {
                "is_scanning": self.is_scanning,
                "current_dir": self.current_dir,
                "target_path": self.target_path,
                "scanned_files_count": self.scanned_files_count,
                "scanned_dirs_count": self.scanned_dirs_count,
                "elapsed_seconds": round(self.elapsed_seconds, 1),
                "found_count": len(self.results),
                "total_found_size": self.total_found_size,
                "total_found_size_formatted": format_size(self.total_found_size),
                "is_cached": self.is_cached and not self.is_scanning,
                "cached_at": self.cached_at,
                "results": list(self.results)
            }

    def remove_from_results(self, paths: List[str]):
        path_set = set(paths)
        with self.lock:
            new_results = []
            for item in self.results:
                if item["path"] in path_set:
                    self.total_found_size -= item["size"]
                else:
                    new_results.append(item)
            self.results = new_results
            # 同步更新持久化缓存文件
            self.save_cache()

scanner = ScanManager()

class ScanRequest(BaseModel):
    path: str
    min_size_mb: float = 100.0
    include_hidden: bool = True
    max_depth: Optional[int] = None

class DeleteRequest(BaseModel):
    paths: List[str]
    permanent: bool = False

class RevealRequest(BaseModel):
    path: str

def get_macos_disk_details(home_path: str):
    """
    获取与 macOS 系统设置和访达 (Finder) 100% 对齐的真实可用容量，
    同时提取 APFS 物理未分配空间和系统可清除空间 (Purgeable Space，如本地快照)
    """
    raw_usage = shutil.disk_usage(home_path)
    total = raw_usage.total
    raw_free = raw_usage.free
    available = raw_free
    used = total - available

    # 优先调用 macOS 原生 Finder AppleScript 查询标称可用容量
    try:
        cmd = ["osascript", "-e", 'tell application "Finder" to get {free space, capacity} of startup disk']
        out = subprocess.check_output(cmd, timeout=1.5).decode().strip()
        parts = [float(x.strip()) for x in out.split(',')]
        if len(parts) == 2:
            finder_free = int(parts[0])
            finder_total = int(parts[1])
            if finder_free > 0 and finder_total > 0:
                available = finder_free
                total = finder_total
                used = total - available
    except Exception:
        pass

    percent = round((used / total) * 100, 1)
    purgeable = max(0, available - raw_free)

    # 统计 APFS Time Machine 本地快照数量
    snapshots_count = 0
    try:
        out = subprocess.check_output(["tmutil", "listlocalsnapshots", "/"], timeout=1.0).decode().strip()
        snaps = [line for line in out.splitlines() if line.startswith("com.apple.")]
        snapshots_count = len(snaps)
    except Exception:
        pass

    return {
        "total": total,
        "used": used,
        "free": available,
        "percent": percent,
        "total_formatted": format_decimal_size(total),
        "used_formatted": format_decimal_size(used),
        "free_formatted": format_decimal_size(available),
        "raw_free": raw_free,
        "raw_free_formatted": format_decimal_size(raw_free),
        "purgeable": purgeable,
        "purgeable_formatted": format_decimal_size(purgeable),
        "snapshots_count": snapshots_count,
        "is_apfs_aligned": True
    }

@app.get("/api/system")
def get_system_info():
    home = os.path.expanduser("~")
    disk_info = get_macos_disk_details(home)

    # 常用目录快捷预设
    presets = [
        {"name": "当前项目 (mac-disk-cleaner)", "path": str(Path(__file__).parent.parent.resolve()), "icon": "folder-code"},
        {"name": "个人主目录 (~)", "path": home, "icon": "home"},
        {"name": "下载 (Downloads)", "path": os.path.join(home, "Downloads"), "icon": "download"},
        {"name": "AI/模型缓存 (~/.cache)", "path": os.path.join(home, ".cache"), "icon": "cpu"},
        {"name": "Ollama 模型 (~/.ollama)", "path": os.path.join(home, ".ollama"), "icon": "brain"},
        {"name": "Telegram 媒体缓存", "path": os.path.join(home, "Library/Group Containers/6N38VWS5BX.ru.keepcoder.Telegram"), "icon": "send"},
        {"name": "桌面 (Desktop)", "path": os.path.join(home, "Desktop"), "icon": "monitor"},
        {"name": "用户应用缓存 (Caches)", "path": os.path.join(home, "Library/Caches"), "icon": "database"},
        {"name": "微信聊天数据缓存", "path": os.path.join(home, "Library/Containers/com.tencent.xinWeChat/Data/Library/Application Support/com.tencent.xinWeChat"), "icon": "message-circle"},
        {"name": "系统数据盘 (/System/Volumes/Data)", "path": "/System/Volumes/Data", "icon": "hard-drive"},
        {"name": "系统根目录 (/)", "path": "/", "icon": "folder"}
    ]

    valid_presets = []
    for p in presets:
        expanded = os.path.expanduser(p["path"])
        if os.path.exists(expanded):
            p["exists"] = True
            p["expanded_path"] = expanded
            valid_presets.append(p)

    return {
        "disk": disk_info,
        "presets": valid_presets,
        "home": home
    }

@app.post("/api/scan/start")
def start_scan(req: ScanRequest):
    expanded = os.path.expanduser(req.path)
    if not os.path.exists(expanded):
        raise HTTPException(status_code=400, detail=f"目标路径不存在: {req.path}")
    
    min_bytes = int(req.min_size_mb * 1024 * 1024)
    success = scanner.start(
        target_path=expanded,
        min_size_bytes=min_bytes,
        include_hidden=req.include_hidden,
        max_depth=req.max_depth
    )
    if not success:
        raise HTTPException(status_code=409, detail="已有扫描任务正在运行中")
    return {"status": "ok", "message": "扫描已启动"}

@app.get("/api/scan/status")
def get_scan_status():
    return scanner.get_status()

@app.post("/api/scan/stop")
def stop_scan():
    scanner.stop()
    return {"status": "ok", "message": "已请求停止扫描"}

@app.post("/api/scan/clear-cache")
def clear_scan_cache():
    if scanner.is_scanning:
        raise HTTPException(status_code=400, detail="正在扫描中，无法清除缓存")
    scanner.clear_cache()
    return {"status": "ok", "message": "已成功清除扫描缓存"}

@app.post("/api/file/reveal")
def reveal_in_finder(req: RevealRequest):
    if not os.path.exists(req.path):
        raise HTTPException(status_code=404, detail="文件不存在")
    try:
        subprocess.run(["open", "-R", req.path], check=True)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def move_to_trash(file_path: str):
    """优先使用 AppleScript 移动到废纸篓，安全防误删；如果失败则移动至 ~/.Trash"""
    try:
        # AppleScript call
        script = f'tell application "Finder" to delete POSIX file "{file_path}"'
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            return True
    except Exception:
        pass

    # Fallback to direct move to ~/.Trash
    trash_dir = os.path.expanduser("~/.Trash")
    os.makedirs(trash_dir, exist_ok=True)
    base_name = os.path.basename(file_path)
    dest_path = os.path.join(trash_dir, base_name)
    counter = 1
    stem, ext = os.path.splitext(base_name)
    while os.path.exists(dest_path):
        dest_path = os.path.join(trash_dir, f"{stem}_{counter}{ext}")
        counter += 1
    shutil.move(file_path, dest_path)
    return True

@app.post("/api/file/delete")
def delete_files(req: DeleteRequest):
    success_count = 0
    freed_bytes = 0
    errors = []
    processed_paths = []

    for path_str in req.paths:
        if not is_safe_to_delete(path_str):
            errors.append(f"安全限制，禁止删除关键路径: {path_str}")
            continue

        if not os.path.exists(path_str):
            errors.append(f"文件不存在: {path_str}")
            continue

        try:
            size = os.path.getsize(path_str) if os.path.isfile(path_str) else 0
            if req.permanent:
                if os.path.isdir(path_str):
                    shutil.rmtree(path_str)
                else:
                    os.remove(path_str)
            else:
                move_to_trash(path_str)

            success_count += 1
            freed_bytes += size
            processed_paths.append(path_str)
        except Exception as e:
            errors.append(f"删除失败 ({path_str}): {str(e)}")

    if processed_paths:
        scanner.remove_from_results(processed_paths)

    return {
        "success_count": success_count,
        "freed_bytes": freed_bytes,
        "freed_formatted": format_size(freed_bytes),
        "errors": errors
    }

@app.get("/", response_class=HTMLResponse)
def index_page():
    template_path = Path(__file__).parent / "templates" / "index.html"
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Cleaner UI template not found</h1>"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("cleaner.app:app", host="127.0.0.1", port=8899, reload=False)
