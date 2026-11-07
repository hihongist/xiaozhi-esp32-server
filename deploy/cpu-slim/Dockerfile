# 不要在 15GB 生产机上构建本镜像。
# 基础镜像 digest 于 2026-11-07 由 docker pull python:3.10.22-slim-bookworm 得到。
FROM python:3.10.22-slim-bookworm@sha256:5be5aaecb962a41567bc8041f1e9e3432cb085b037fe057f9a562630b2e4b370

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
    python -m pip install --no-cache-dir --no-deps \
      --index-url https://pypi.org/simple \
      -r /tmp/requirements-cpu.rest.txt && \
    python -c "import importlib.util,torch,funasr,onnxruntime,edge_tts,openai; assert torch.version.cuda is None; assert importlib.util.find_spec('transformers') is None; assert importlib.util.find_spec('modelscope') is None; assert importlib.util.find_spec('nvidia') is None"

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
