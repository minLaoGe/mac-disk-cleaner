#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

PORT=8899
URL="http://127.0.0.1:$PORT"

# 检查当前端口是否已经被占用
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "========================================================"
    echo "  大文件清理助手已经在运行中！"
    echo "  访问地址: $URL"
    echo "========================================================"
    open "$URL"
    exit 0
fi

# 激活虚拟环境（如果存在）
if [ -d "$DIR/.venv" ]; then
    source "$DIR/.venv/bin/activate"
fi

echo "========================================================"
echo "  启动 Mac 大文件清理助手 Web 版..."
echo "  服务端口: $PORT"
echo "  访问地址: $URL"
echo "========================================================"

# 后台等待 1 秒自动打开浏览器
(sleep 1.2 && open "$URL") &

# 启动 FastAPI 服务
exec python3 -m uvicorn cleaner.app:app --host 127.0.0.1 --port $PORT
