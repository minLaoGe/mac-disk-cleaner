# 🍎 Mac Disk Cleaner

<p align="center">
  <a href="README.md"><strong>简体中文</strong></a> •
  <a href="README.en.md"><strong>English</strong></a> •
  <a href="README.ja.md"><strong>日本語</strong></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-macOS-black?logo=apple" alt="macOS" />
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Protocol-MCP%20Ready-purple" alt="MCP" />
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License" />
</p>

A modern large file inspection, AI model weight cleanup, and cache management tool crafted specifically for **macOS**. It offers an **elegant and intuitive Web visualization dashboard** and natively integrates the **Model Context Protocol (MCP)**. You can freely inspect and clean files in your browser, or manage disk space via natural language dialogues with AI agents like Claude, Cursor, and Antigravity!

---

## 🌟 Key Features

- 🖥️ **Modern & Intuitive Web UI**: Self-contained single-page application with zero frontend build dependencies. Start and use immediately.
- 🌐 **Multilingual Internationalization (i18n)**: Instant switching between 🇨🇳 **Simplified Chinese**, 🇺🇸 **English**, and 🇯🇵 **Japanese (日本語)**, with persistent language preferences.
- 📊 **Real-time System Disk Monitor**: Top dashboard monitors total disk size, usage percentage, and free capacity with color-coded alerts.
- ⚡ **Quick Presets & Deep Inspection**:
  - One-click scan presets: **Home (`~`)**, **Downloads**, **AI Model Caches (`~/.cache`)**, **Ollama Models (`~/.ollama`)**, **Desktop**, **WeChat media cache**, etc.
  - Supports scanning arbitrary custom directories and hidden folders (`.cache`, `.venv`, `.git`, etc.).
- 🎯 **Multi-dimensional Filtering & Dynamic Aggregation**:
  - **Category Tabs**: Auto-classifies files into AI/Model weights (`.safetensors`, `.bin`, `.gguf`, `.pth`), Video media, Archives & disk images (`.dmg`, `.zip`, `.iso`), Audio, and Documents.
  - **Dual Search Inputs**: Dedicated filters for "File Name" and "Full Path / Directory".
  - **Dynamic Directory Aggregation**: Automatically extracts parent folders from current scan results with file counts for instant targeted filtering.
  - **Dynamic Extension Aggregation**: Automatically extracts unique file extensions with item counts.
  - **One-click Filter Reset**: Easily reset all active filters with active filter counters.
- 💾 **Scan Result Persistence & Cache**: Scan results and configurations are cached on both backend and client, surviving page reloads.
- 📂 **Native macOS Finder Integration**: Highlight and reveal any scanned file in Finder with a single click before cleaning.
- 🛡️ **Dual-tier Safe Deletion Architecture**:
  - **Move to Trash (Recommended & Safe)**: Moves files to macOS System Trash; accidentally deleted items can be restored instantly via Finder.
  - **Permanent Deletion**: Permanently wipes files to reclaim disk space immediately.
  - **Protected System Paths**: Strict guardrails prevent deleting core operating system paths (`/System`, `/Library`, `/usr`, etc.).
  - **Floating Batch Action Bar**: Batch select files, review real-time reclaimable space estimation, and proceed with confirmation modals.
- 🤖 **Native MCP Protocol Integration**: Ships 6 standard MCP tools for seamless interaction with AI model assistants.

---

## 📸 Screenshots & UI Preview

### 1. Control Panel & Disk Overview
Monitor real-time disk usage, set minimum file size thresholds, and pick common preset directories:
![Dashboard Overview](docs/screenshots/overview.png)

### 2. Large File Scan Results & Multi-dimension Filtering
Detailed listing of large files with category badges, paths, size highlights, and modification timestamps:
![Scan Results List](docs/screenshots/scanned_list.png)

### 3. Floating Batch Action Bar
Batch selection bar with real-time reclaimable space calculation and safety confirmations:
![Batch Action Bar](docs/screenshots/batch_action.png)

---

## 🚀 Quick Start

### Prerequisites
- macOS 10.15+
- Python 3.10+

### Installation

1. **Clone the repository**:
   ```bash
   git clone git@github.com:minLaoGe/mac-disk-cleaner.git
   cd mac-disk-cleaner
   ```

2. **Install dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Start the Web Dashboard**:
   ```bash
   chmod +x start_cleaner.sh
   ./start_cleaner.sh
   ```
   > The script launches the FastAPI backend (default port `8899`) and automatically opens `http://127.0.0.1:8899` in your default browser.

---

## 🤖 Large Language Model & MCP Interaction

This project comes with a turnkey MCP server [`cleaner_mcp_server.py`](cleaner_mcp_server.py), enabling AI assistants to inspect and clean disks via conversational instructions.

### 1. Register the MCP Server

Add the following snippet to your MCP configuration (such as **Claude Desktop**, **Cursor**, **Windsurf**, or **Antigravity** global config `~/.gemini/config/mcp_config.json`):

```json
{
  "mcpServers": {
    "mac-disk-cleaner": {
      "command": "python3",
      "args": [
        "/Users/YOUR_USERNAME/mac-disk-cleaner/cleaner_mcp_server.py"
      ]
    }
  }
}
```

### 2. Available MCP Tools

| Tool Name | Description | Key Parameters |
| :--- | :--- | :--- |
| `get_disk_space_overview` | Returns disk usage percentage, free capacity, and recommended paths | None |
| `scan_large_files` | Recursively scans directory for large files, sorted descending by size | `path`, `min_size_mb`, `include_hidden`, `max_results` |
| `scan_ai_models_and_cache` | Scans weights from HuggingFace, ModelScope, Ollama, etc. | `min_size_mb`, `max_results` |
| `move_files_to_trash` | Safely moves selected files to macOS system Trash | `paths: list[str]` |
| `delete_files_permanently` | Permanently deletes files from disk (requires explicit confirmation) | `paths: list[str]`, `confirm: bool` |
| `reveal_in_finder` | Reveals and highlights specified file in macOS Finder | `path: str` |

### 3. Example AI Prompts

- *"Check my current free disk space and scan `~/.cache` for AI model files larger than 500MB."*
- *"Find `.dmg` installers in `~/Downloads` over 1GB and move unneeded ones to the Trash."*
- *"Reveal the 20GB video file you just discovered in Finder."*

---

## 🔒 Safety Guardrails

1. **Trash-first Philosophy**: Regular deletion moves files to the native macOS Trash via AppleScript and `~/.Trash`, allowing one-click rollback anytime.
2. **Protected Paths Blacklist**: Root and critical system directories (`/`, `/System`, `/Applications`, `/Library`, `/usr`, `/bin`, etc.) are protected at the lowest level to eliminate accidental system damage.
3. **Mandatory Confirmation**: Permanent file deletion requires explicit secondary confirmation in both the Web UI and MCP tool layers.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
