# 本文件是与隔离 venv 相同的安装配方。
# 2026-11-07 本阶段没有执行 docker build / save / load，镜像体积未测。
# 不要在 15GB 生产机上构建本镜像。
FROM python:3.10.22-slim-bookworm

RUN apt-get update && \
    apt-get install -y --no-install-recommends libopus0 ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/xiaozhi-esp32-server

COPY deploy/cpu-slim/requirements-cpu.lock /tmp/requirements-cpu.lock

# 先装官方 CPU wheel，再装其余锁定依赖，避免 PyPI 的 CUDA torch 被拉进来。
RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir \
      --index-url https://download.pytorch.org/whl/cpu \
      "torch==2.2.2+cpu" "torchaudio==2.2.2+cpu" && \
    grep -E -v '^(torch|torchaudio)==' /tmp/requirements-cpu.lock > /tmp/requirements-cpu.rest.txt && \
    python -m pip install --no-cache-dir \
      --index-url https://pypi.org/simple \
      -r /tmp/requirements-cpu.rest.txt && \
    python -c "import torch; assert torch.version.cuda is None, torch.version.cuda"

COPY main/xiaozhi-server /opt/xiaozhi-esp32-server
COPY deploy/cpu-slim/licenses/FunASR-MODEL_LICENSE.txt /opt/xiaozhi-esp32-server/models/SenseVoiceSmall/MODEL_LICENSE.txt
COPY LICENSE /opt/xiaozhi-esp32-server/LICENSE

RUN groupadd --system --gid 10001 xiaozhi && \
    useradd --system --uid 10001 --gid 10001 --home-dir /opt/xiaozhi-esp32-server xiaozhi && \
    mkdir -p /opt/xiaozhi-esp32-server/tmp /opt/xiaozhi-esp32-server/data && \
    chown -R 10001:10001 /opt/xiaozhi-esp32-server

COPY deploy/cpu-slim/entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh

USER 10001:10001
EXPOSE 8000 8003
ENTRYPOINT ["/entrypoint.sh"]
