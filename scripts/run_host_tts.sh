#!/usr/bin/env bash
# run_host_tts.sh - 启动宿主机原生 TTS 微服务 (端口 8028)
set -e

PORT=${TTS_PORT:-8028}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TTS_DIR="$PROJECT_ROOT/services/tts"

echo "=== 启动宿主机原生 TTS 微服务 ==="
echo "工作目录: $TTS_DIR"
echo "监听端口: 0.0.0.0:$PORT"

# 检查当前端口占用
PID=$(lsof -ti :"$PORT" || true)
if [ -n "$PID" ]; then
  echo "警告: 端口 $PORT 已被进程 $PID 占用，尝试终止旧进程..."
  kill -9 "$PID" || true
  sleep 1
fi

cd "$TTS_DIR"
export TTS_PORT="$PORT"
export PYTHONUNBUFFERED=1

echo "正在启动 uvicorn main:app ..."
exec python3 main.py
