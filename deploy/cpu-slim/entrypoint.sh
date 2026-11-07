#!/bin/sh
# 不创建、不覆盖 data/.config.yaml。缺文件就退出。
set -eu
cd /opt/xiaozhi-esp32-server
if [ ! -f data/.config.yaml ]; then
  echo "缺少 data/.config.yaml。请挂载已有配置，或自行放入 deploy/cpu-slim/config.cpu-slim.yaml.example。本入口不会写入密钥，也不会覆盖已有文件。" >&2
  exit 1
fi
exec python app.py
