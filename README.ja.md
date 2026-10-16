# 🍎 Mac 大容量ファイルクリーナー (Mac Disk Cleaner)

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

**macOS** のために設計された最新の大容量ファイル検出、AIモデル重みクリーンアップ、アプリケーションキャッシュ管理ツールです。**洗練された直感的なWebダッシュボード** を備え、次世代の **MCP (Model Context Protocol)** にも標準対応。ブラウザ上で快適にディスクを整理できるだけでなく、Claude、Cursor、Antigravity などのAIアシスタントと自然言語で対話しながらディスクを管理できます！

---

## 🌟 主な機能と特長

- 🖥️ **直感的でモダンな Web UI**：単一ページ構成でフロントエンドのビルド環境は不要。起動後すぐに使用可能。
- 🌐 **多言語対応 (i18n)**：🇨🇳 **簡体字中国語**、🇺🇸 **英語 (English)**、🇯🇵 **日本語** のワンクリック即時切り替えに対応し、言語設定を自動保持。
- 📊 **システムディスクのリアルタイム監視**：ストレージ総容量、使用率、空き容量をヘルスカラー表示で一目瞭然に把握。
- ⚡ **プリセットショートカット＆ディープスキャン**：
  - ワンクリックで選べる定番ディレクトリ：**ホーム (`~`)**、**ダウンロード (`Downloads`)**、**AIキャッシュ (`~/.cache`)**、**Ollama モデル (`~/.ollama`)**、**デスクトップ**、**WeChat キャッシュ**など。
  - 任意のカスタムパスや隠しディレクトリ（`.cache`、`.venv`、`.git` など）のスキャンにも対応。
- 🎯 **多次元フィルタリング＆スマート動的集計**：
  - **カテゴリ分類タブ**：AIモデル重み (`.safetensors`、`.bin`、`.gguf`、`.pth`)、動画、アーカイブ・ディスクイメージ (`.dmg`、`.zip`、`.iso`)、音声、文書などを自動識別。
  - **デュアル検索入力**：「ファイル名検索」と「パス・ディレクトリ検索」を独立して搭載。
  - **所在フォルダの動的集計絞り込み**：スキャン結果に含まれる親ディレクトリを自動抽出し、ファイル件数順にリスト化して絞り込み可能。
  - **拡張子の動的集計絞り込み**：検出されたファイル拡張子を件数付きで一覧表示。
  - **ワンクリックフィルター解除**：適用中の絞り込み件数バッジ付きで、全条件を一発リセット可能。
- 💾 **スキャン結果の永続化とキャッシュ保持**：スキャンデータはサーバーとブラウザの双方に保存され、ページをリロードしても消えません（キャッシュ消去ボタンあり）。
- 📂 **Finder 連携ハイライト**：スキャン結果のファイルをワンクリックで macOS Finder 上で選択・ハイライト表示。
- 🛡️ **ゴミ箱優先の安全な削除設計**：
  - **ゴミ箱に移動 (推奨・安全)**：macOS システムゴミ箱へ移動。誤って削除した場合も Finder の「元に戻す」から復元可能。
  - **完全消去 (完全削除)**：ディスクから物理的に抹消し、即座に空き領域を回復。
  - **重要システム領域の保護**：`/System`、`/Library`、`/usr` などのmacOS基盤パスへの削除操作はシステムレベルでブロック。
  - **フローティング一括操作バー**：複数選択時、解放見込み容量をリアルタイム表示し、確認ダイアログで誤操作を防止。
- 👯 **重複ファイルの高速照合とスマート分類**：
  - サンプルHash（先頭・中間・末尾ブロック）と厳密なバイトサイズ照合により、GB級ファイルを丸ごとメモリに載せることなくミリ秒単位で同一ファイルを特定。
  - 保持推奨の「原本」（正規パス・より古い作成日）と余分な「コピー」を自動判別。
  - 警告バナー、重複ファイル専用フィルター、および原本を保護しながら不要なコピーだけを一括選択する**「余分なコピーを一括選択」**を提供。
- 🤖 **ネイティブ MCP サーバー付属**：7つの標準MCPツールを搭載し、AIエージェントとスムーズに連携。

---

## 📸 スクリーンショット

### 1. コントロールパネルとディスク概要
ディスク使用率のモニタリング、スキャンサイズ閾値の設定、定番プリセットの選択：
![ダッシュボード概要](docs/screenshots/overview.png)

### 2. 大容量ファイル一覧と絞り込み
カテゴリバッジ、フルパス、サイズ表示、更新日時を見やすく表示：
![スキャン結果一覧](docs/screenshots/scanned_list.png)

### 3. フローティング一括削除バー
複数ファイル選択時に下部からスライドインし、安全にゴミ箱へ移動：
![一括操作バー](docs/screenshots/batch_action.png)

---

## 🚀 クイックスタート

### 動作要件
- macOS 10.15+
- Python 3.10+

### インストール手順

1. **リポジトリをクローン**：
   ```bash
   git clone git@github.com:minLaoGe/mac-disk-cleaner.git
   cd mac-disk-cleaner
   ```

2. **依存ライブラリのインストール**：
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Web パネルの起動**：
   ```bash
   chmod +x start_cleaner.sh
   ./start_cleaner.sh
   ```
   > スクリプトを実行すると FastAPI サーバー（ポート `8899`）が起動し、ブラウザで `http://127.0.0.1:8899` が自動的に開きます。

---

## 🤖 AI アシスタント＆ MCP (Model Context Protocol) 連携

本プロジェクトには、AIエージェントが自然言語でディスク操作を行えるようにする標準 MCP サーバー [`cleaner_mcp_server.py`](cleaner_mcp_server.py) が付属しています。

### 1. MCP サーバーの登録

**Claude Desktop**、**Cursor**、**Windsurf**、または **Antigravity** の設定ファイル（例：`~/.gemini/config/mcp_config.json`）に以下を追加します：

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

### 2. 利用可能な MCP ツール一覧

| ツール名 | 説明 | 主なパラメータ |
| :--- | :--- | :--- |
| `get_disk_space_overview` | ディスク使用率、空き容量、推奨点検パスを取得 | なし |
| `scan_large_files` | 対象ディレクトリを再帰的にスキャンし、サイズ降順で取得 | `path`, `min_size_mb`, `include_hidden`, `max_results` |
| `scan_ai_models_and_cache` | HuggingFace、ModelScope、Ollama 等のモデル重みをスキャン | `min_size_mb`, `max_results` |
| `move_files_to_trash` | 指定ファイルを安全に macOS のゴミ箱へ移動 | `paths: list[str]` |
| `delete_files_permanently` | 指定ファイルをディスクから完全に消去（要確認フラグ） | `paths: list[str]`, `confirm: bool` |
| `find_duplicate_files` | サンプルHashにより同一大容量ファイルを特定し、原本と余分なコピーを分類 | `path`, `min_size_mb`, `max_results` |
| `reveal_in_finder` | 指定ファイルを macOS Finder で選択・ハイライト表示 | `path: str` |

### 3. AI 対話プロンプトの例

- *「現在のディスクの空き容量を確認して、`~/.cache` 内の 500MB 以上の AI モデルファイルをスキャンして。」*
- *「`~/Downloads` にある 1GB を超える `.dmg` ファイルを探して、不要なものをゴミ箱に移動して。」*
- *「さっき検出された 20GB の大容量動画ファイルを Finder で表示して。」*

---

## 🔒 セキュリティと安全性への配慮

1. **ゴミ箱優先の安全哲学**：日常のファイル削除は AppleScript と `~/.Trash` を利用して macOS のゴミ箱へ送るため、万一の誤操作時も Finder からすぐに復元できます。
2. **システム重要ディレクトリの保護**：`/`, `/System`, `/Applications`, `/Library`, `/usr`, `/bin` などの重要パスに対する削除は基盤ロジックでブロックされます。
3. **完全消去の二重確認**：ディスクからの完全抹消処理は、Web UI と MCP ツールの両方で厳格な二重確認が必要です。

---

## 📄 ライセンス

本プロジェクトは [MIT License](LICENSE) のもとで公開されています。
