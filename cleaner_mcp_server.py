#!/usr/bin/env python3
"""
Mac Disk Big File Cleaner - Model Context Protocol (MCP) Server
Allows AI models (Claude, Cursor, Antigravity, etc.) to inspect disk space,
scan for large files/AI models, reveal files in Finder, and safely clean up disk space.
"""

import os
import sys
import time
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any
from mcp.server.mcpserver import MCPServer

# Initialize MCP Server
mcp = MCPServer("mac-disk-cleaner")

PROTECTED_PATHS = {
    "/", "/System", "/bin", "/sbin", "/usr", "/etc", "/var",
    "/Applications", "/Library", os.path.expanduser("~")
}

def is_safe_to_delete(path_str: str) -> bool:
    try:
        resolved = Path(path_str).resolve()
        if str(resolved) in PROTECTED_PATHS:
            return False
        parts = resolved.parts
        if len(parts) <= 2:
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

def get_file_category(ext: str) -> str:
    ext = ext.lower()
    categories = {
        "AI_Model": [".bin", ".safetensors", ".gguf", ".pt", ".pth", ".onnx", ".ckpt", ".h5"],
        "Video": [".mp4", ".mov", ".mkv", ".avi", ".wmv", ".flv", ".webm", ".m4v"],
        "Archive_DiskImage": [".zip", ".tar", ".gz", ".7z", ".rar", ".bz2", ".xz", ".dmg", ".iso", ".pkg"],
        "Audio": [".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg"],
        "Image": [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff", ".psd", ".raw"],
        "Document": [".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"],
    }
    for cat, exts in categories.items():
        if ext in exts:
            return cat
    return "Other"

@mcp.tool()
def get_disk_space_overview() -> Dict[str, Any]:
    """Get the current macOS disk usage overview (total, used, free space, percentage) and key target paths for cleaning."""
    home = os.path.expanduser("~")
    usage = shutil.disk_usage(home)
    total = usage.total
    used = usage.used
    free = usage.free
    percent = round((used / total) * 100, 1)

    key_directories = [
        {"name": "Downloads", "path": os.path.join(home, "Downloads"), "desc": "Downloaded files and installers"},
        {"name": "AI/Model Cache", "path": os.path.join(home, ".cache"), "desc": "HuggingFace, ModelScope, Torch model weights"},
        {"name": "Ollama Models", "path": os.path.join(home, ".ollama"), "desc": "Local Ollama LLM model weights"},
        {"name": "App Caches", "path": os.path.join(home, "Library/Caches"), "desc": "Application cache directory"},
        {"name": "WeChat Cache", "path": os.path.join(home, "Library/Containers/com.tencent.xinWeChat/Data/Library/Application Support/com.tencent.xinWeChat"), "desc": "WeChat chat media cache"},
        {"name": "Desktop", "path": os.path.join(home, "Desktop"), "desc": "Desktop files"},
        {"name": "Current Workspace", "path": str(Path(__file__).parent.resolve()), "desc": "Current Antigravity workspace"},
    ]

    available_dirs = []
    for d in key_directories:
        p = d["path"]
        if os.path.exists(p):
            available_dirs.append({
                "name": d["name"],
                "path": p,
                "description": d["desc"]
            })

    return {
        "disk": {
            "total_bytes": total,
            "used_bytes": used,
            "free_bytes": free,
            "used_percent": percent,
            "total_formatted": format_size(total),
            "used_formatted": format_size(used),
            "free_formatted": format_size(free),
            "status": "CRITICAL (>90% full)" if percent > 90 else ("WARNING (>80% full)" if percent > 80 else "HEALTHY")
        },
        "recommended_scan_locations": available_dirs
    }

@mcp.tool()
def scan_large_files(
    path: str,
    min_size_mb: float = 100.0,
    include_hidden: bool = True,
    max_results: int = 50
) -> Dict[str, Any]:
    """Scan a given directory recursively for files larger than min_size_mb. Returns sorted file list by size descending."""
    root_path = Path(path).expanduser().resolve()
    if not root_path.exists():
        return {"error": f"Path does not exist: {path}"}

    min_size_bytes = int(min_size_mb * 1024 * 1024)
    found_files = []
    total_scanned_files = 0
    start_time = time.time()

    for root, dirs, files in os.walk(str(root_path), followlinks=False):
        if not include_hidden:
            dirs[:] = [d for d in dirs if not d.startswith('.')]

        for f in files:
            if not include_hidden and f.startswith('.'):
                continue

            file_path = os.path.join(root, f)
            total_scanned_files += 1

            try:
                stat = os.lstat(file_path)
                if os.path.islink(file_path):
                    continue

                size = stat.st_size
                if size >= min_size_bytes:
                    ext = os.path.splitext(f)[1]
                    found_files.append({
                        "name": f,
                        "path": file_path,
                        "size_bytes": size,
                        "size_formatted": format_size(size),
                        "category": get_file_category(ext),
                        "extension": ext,
                        "modified_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))
                    })
            except (PermissionError, FileNotFoundError, OSError):
                continue

    found_files.sort(key=lambda x: x["size_bytes"], reverse=True)
    total_found_size = sum(x["size_bytes"] for x in found_files)
    returned_files = found_files[:max_results]

    return {
        "scanned_path": str(root_path),
        "min_size_threshold": f"{min_size_mb} MB",
        "total_scanned_files_count": total_scanned_files,
        "total_found_large_files": len(found_files),
        "total_large_files_size": format_size(total_found_size),
        "elapsed_seconds": round(time.time() - start_time, 2),
        "top_files": returned_files
    }

@mcp.tool()
def scan_ai_models_and_cache(min_size_mb: float = 50.0, max_results: int = 50) -> Dict[str, Any]:
    """Specifically scans popular AI model cache directories (~/.cache, ~/.ollama, HuggingFace, ModelScope) for large weights."""
    home = os.path.expanduser("~")
    search_dirs = [
        os.path.join(home, ".cache/huggingface"),
        os.path.join(home, ".cache/modelscope"),
        os.path.join(home, ".ollama"),
        os.path.join(home, ".cache/torch"),
        str(Path(__file__).parent.resolve())
    ]

    all_results = []
    min_size_bytes = int(min_size_mb * 1024 * 1024)

    for d in search_dirs:
        p = Path(d)
        if not p.exists():
            continue

        for root, dirs, files in os.walk(str(p), followlinks=False):
            for f in files:
                file_path = os.path.join(root, f)
                try:
                    stat = os.lstat(file_path)
                    if os.path.islink(file_path):
                        continue
                    size = stat.st_size
                    if size >= min_size_bytes:
                        ext = os.path.splitext(f)[1]
                        all_results.append({
                            "name": f,
                            "path": file_path,
                            "size_bytes": size,
                            "size_formatted": format_size(size),
                            "category": get_file_category(ext),
                            "extension": ext,
                            "modified_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))
                        })
                except (PermissionError, FileNotFoundError, OSError):
                    continue

    all_results.sort(key=lambda x: x["size_bytes"], reverse=True)
    total_size = sum(x["size_bytes"] for x in all_results)

    return {
        "locations_scanned": [d for d in search_dirs if os.path.exists(d)],
        "found_model_weights_count": len(all_results),
        "total_size": format_size(total_size),
        "files": all_results[:max_results]
    }

@mcp.tool()
def move_files_to_trash(paths: List[str]) -> Dict[str, Any]:
    """Safely move one or more files to the macOS Trash. They can be restored from Trash if needed."""
    success = []
    failed = []
    freed_bytes = 0

    for path_str in paths:
        if not is_safe_to_delete(path_str):
            failed.append({"path": path_str, "error": "Protected system path or unsafe to delete"})
            continue

        if not os.path.exists(path_str):
            failed.append({"path": path_str, "error": "File not found"})
            continue

        try:
            size = os.path.getsize(path_str) if os.path.isfile(path_str) else 0

            # Try AppleScript to move to Trash (Finder integration)
            moved = False
            try:
                script = f'tell application "Finder" to delete POSIX file "{path_str}"'
                res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=5)
                if res.returncode == 0:
                    moved = True
            except Exception:
                pass

            if not moved:
                # Fallback to moving to ~/.Trash
                trash_dir = os.path.expanduser("~/.Trash")
                os.makedirs(trash_dir, exist_ok=True)
                base = os.path.basename(path_str)
                dest = os.path.join(trash_dir, base)
                c = 1
                stem, ext = os.path.splitext(base)
                while os.path.exists(dest):
                    dest = os.path.join(trash_dir, f"{stem}_{c}{ext}")
                    c += 1
                shutil.move(path_str, dest)

            freed_bytes += size
            success.append({"path": path_str, "freed_size": format_size(size)})
        except Exception as e:
            failed.append({"path": path_str, "error": str(e)})

    return {
        "success_count": len(success),
        "freed_total": format_size(freed_bytes),
        "success_files": success,
        "failed_files": failed
    }

@mcp.tool()
def delete_files_permanently(paths: List[str], confirm: bool = False) -> Dict[str, Any]:
    """Permanently delete files or directories. Cannot be recovered. Must pass confirm=True."""
    if not confirm:
        return {
            "error": "Safety check: You must explicitly provide confirm=True to permanently delete files. Consider using move_files_to_trash instead."
        }

    success = []
    failed = []
    freed_bytes = 0

    for path_str in paths:
        if not is_safe_to_delete(path_str):
            failed.append({"path": path_str, "error": "Protected system path"})
            continue

        if not os.path.exists(path_str):
            failed.append({"path": path_str, "error": "File not found"})
            continue

        try:
            size = os.path.getsize(path_str) if os.path.isfile(path_str) else 0
            if os.path.isdir(path_str):
                shutil.rmtree(path_str)
            else:
                os.remove(path_str)

            freed_bytes += size
            success.append({"path": path_str, "freed_size": format_size(size)})
        except Exception as e:
            failed.append({"path": path_str, "error": str(e)})

    return {
        "success_count": len(success),
        "freed_total": format_size(freed_bytes),
        "success_files": success,
        "failed_files": failed
    }

@mcp.tool()
def reveal_in_finder(path: str) -> Dict[str, Any]:
    """Highlight and select the specified file in macOS Finder."""
    if not os.path.exists(path):
        return {"error": f"Path not found: {path}"}
    try:
        subprocess.run(["open", "-R", path], check=True)
        return {"status": "ok", "message": f"Revealed in Finder: {path}"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    mcp.run(transport="stdio")
