# 🍎 Mac 大文件清理助手 (Mac Disk Cleaner)

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

专为 **macOS** 打造的现代化大文件排查、大模型权重清理与应用缓存治理工具。提供 **优雅美观的 Web 可视化管理面板**，并原生支持 **MCP (Model Context Protocol)** 协议，既可以在浏览器中自由勾选清理，也能直接通过 Claude、Cursor、Antigravity 等大模型以自然语言对话管理磁盘！

---

## 🌟 核心特性

- 🖥️ **现代直观的 Web 界面**：自包含单页，无需复杂前端构建环境，启动即开即用。
- 🌐 **多语言国际化 (i18n)**：原生支持 🇨🇳 **简体中文**、🇺🇸 **English**、🇯🇵 **日本語** 一键即时切换，持久化保存用户语言偏好。
- 📊 **系统磁盘实时看板**：顶部实时监控当前磁盘总量、已用比例及可用剩余容量（智能健康度色彩预警）。
- ⚡ **快捷路径预设与全盘检索**：
  - 快速一键定位：**个人主目录 (`~`)**、**下载 (`Downloads`)**、**AI与模型缓存 (`~/.cache`)**、**Ollama 模型 (`~/.ollama`)**、**桌面**、**微信媒体缓存**等。
  - 支持任意自定义路径检索与隐藏目录检索（`.cache`、`.venv`、`.git` 等）。
- 🎯 **多维度精细检索与智能聚合过滤**：
  - **分类标签快速过滤**：自动识别 AI/模型权重 (`.safetensors`/`.bin`/`.gguf`/`.pth`)、视频媒体、压缩包与镜像 (`.dmg`/`.zip`/`.iso`)、音频、设计文档等。
  - **双重搜索**：独立支持“文件名搜索”与“完整路径/所在目录搜索”。
  - **动态聚合目录筛选**：自动从本次扫描结果中提炼出所在父目录列表并统计出现频次，一键筛选特定目录。
  - **动态聚合后缀筛选**：自动从扫描结果中提炼出所有涉及的文件后缀格式及数量统计。
  - **快捷重置**：一键重置当前激活的多重过滤条件并显示实时生效项数。
- 💾 **扫描结果持久化与断点免丢**：扫描数据在服务端与浏览器端双重缓存，刷新页面不丢失，支持一键清空缓存。
- 📂 **访达 (Finder) 深度联动**：列表中一键定位并高亮选中文件，方便清理前双击预览确认。
- 🛡️ **双重安全删除机制**：
  - **移入废纸篓 (推荐安全)**：将文件安全放至 macOS 系统废纸篓，误删可从废纸篓一键还原。
  - **彻底永久删除**：直接从磁盘擦除，立即释放物理空间。
  - **核心系统路径防护**：严格拦截系统核心根目录（`/System`、`/Library`、`/usr` 等），杜绝误伤风险。
  - **批量清理悬浮栏**：支持批量勾选，实时计算预计释放空间，提供二次弹窗确认保护。
- 👯 **大文件重复校验与智能标记**：
  - 基于文件精确字节大小与毫秒级采样 Hash（头/中/尾组合指纹校验），极速比对排查海量重复大文件。
  - 启发式智能推断“原件”（优先保留规范路径、创建更早的文件）与“多余副本”。
  - 提供醒目告警横幅、一键筛选重复项与**“一键勾选所有多余副本”**，原件安全锁定保留，轻松释放浪费空间。
- 🤖 **原生 MCP 服务支持**：提供 7 大标准 MCP 工具，无缝接入大模型助手。

---

## 📸 界面效果预览

### 1. 扫描与控制面板
主界面支持直观查看磁盘已用百分比、设置扫描阈值以及一键选择常用预设：
![控制面板概览](docs/screenshots/overview.png)

### 2. 大文件扫描结果与分类检索
清晰罗列大文件详细信息，展示类型标签、路径、大小高亮与修改时间：
![扫描结果列表](docs/screenshots/scanned_list.png)

### 3. 底部悬浮批量清理操作
勾选文件后底部吸附弹出批量操作栏，实时计算预估释放容量，防止手滑误操作：
![批量操作栏](docs/screenshots/batch_action.png)

---

## 🚀 快速上手

### 环境依赖
- macOS 10.15+
- Python 3.10+

### 安装步骤

1. **克隆项目到本地**：
   ```bash
   git clone git@github.com:minLaoGe/mac-disk-cleaner.git
   cd mac-disk-cleaner
   ```

2. **安装依赖**：
   ```bash
   pip3 install -r requirements.txt
   ```

3. **一键启动 Web 面板**：
   ```bash
   chmod +x start_cleaner.sh
   ./start_cleaner.sh
   ```
   > 脚本执行后将在本地启动 FastAPI 服务（默认端口 `8899`），并自动在你的默认浏览器中打开 `http://127.0.0.1:8899`。

---

## 🤖 大模型 MCP (Model Context Protocol) 交互

本项目附带完整的 MCP 服务器 [`cleaner_mcp_server.py`](cleaner_mcp_server.py)，让你能够直接用自然语言指挥大模型协助排查清理磁盘。

### 1. 注册 MCP 服务

在你的客户端配置（如 **Claude Desktop**、**Cursor**、**Windsurf** 或 **Antigravity** 全局配置 `~/.gemini/config/mcp_config.json`）中添加以下配置：

```json
{
  "mcpServers": {
    "mac-disk-cleaner": {
      "command": "python3",
      "args": [
        "/Users/你的用户名/mac-disk-cleaner/cleaner_mcp_server.py"
      ]
    }
  }
}
```

### 2. 提供的 MCP 工具清单

| 工具名称 | 功能描述 | 常用输入参数 |
| :--- | :--- | :--- |
| `get_disk_space_overview` | 查询当前 Mac 磁盘占用比例、剩余容量与推荐排查路径 | 无 |
| `scan_large_files` | 递归扫描目标目录中的大文件，按大小倒序返回 | `path`, `min_size_mb`, `include_hidden`, `max_results` |
| `scan_ai_models_and_cache` | 专用于检索 HuggingFace、ModelScope、Ollama 等模型权重 | `min_size_mb`, `max_results` |
| `move_files_to_trash` | 将指定文件安全移入 macOS 系统废纸篓 | `paths: list[str]` |
| `delete_files_permanently` | 彻底永久删除指定文件（需显式确认） | `paths: list[str]`, `confirm: bool` |
| `find_duplicate_files` | 基于采样 Hash 极速校验相同大文件，标记建议原件与冗余副本 | `path`, `min_size_mb`, `max_results` |
| `reveal_in_finder` | 在 macOS 访达中高亮定位选中文件 | `path: str` |

### 3. 大模型对话示例

- *“帮我查一下现在磁盘剩余空间，重点扫描一下 `~/.cache` 下大于 500MB 的 AI 模型文件。”*
- *“查看 `~/Downloads` 目录下超过 1GB 的 `.dmg` 安装包，把不需要的移入废纸篓。”*
- *“在访达里定位刚才扫描出来的那个 20GB 大视频。”*

---

## 🔒 安全性考量

1. **废纸篓优先原则**：所有日常删除操作默认对接 macOS 系统的废纸篓机制（AppleScript 与 `~/.Trash` 双保障），误删随时可以在访达里点“放回原处”。
2. **黑名单防护**：系统关键目录（如 `/`, `/System`, `/Applications`, `/Library`, `/usr`, `/bin` 等）内置底层拦截逻辑，即使大模型误发指令也绝不会删除系统文件。
3. **彻底删除二次确认**：彻底抹除操作在前端与 MCP 工具层均设置了强制二次确认机制。

---

## 📄 开源许可证

本项目采用 [MIT License](LICENSE) 开源许可证。
