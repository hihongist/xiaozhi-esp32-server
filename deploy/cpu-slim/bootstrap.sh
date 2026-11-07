#!/bin/sh
# 只在目标路径不存在时复制模板。已有文件一律保留。
# 不访问生产机，不删除任何数据，不写入密钥。
set -eu
ROOT=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
DEST=${1:?用法: bootstrap.sh <目标目录>}

install_if_absent() {
  src=$1
  dst=$2
  if [ -e "$dst" ]; then
    echo "保留已有文件: $dst"
    return 0
  fi
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
  echo "写入新文件: $dst"
}

install_if_absent "$ROOT/config.cpu-slim.yaml.example" "$DEST/data/.config.yaml.cpu-slim.example"
if [ -e "$DEST/data/.config.yaml" ]; then
  echo "保留已有文件: $DEST/data/.config.yaml"
else
  echo "未写入 $DEST/data/.config.yaml 。请自行复制 example 后再填写密钥。"
fi
if [ -e "$DEST/models/SenseVoiceSmall/model.pt" ]; then
  echo "保留已有权重: $DEST/models/SenseVoiceSmall/model.pt"
else
  echo "目标没有 model.pt。本脚本不会下载 893MiB 权重。"
fi
