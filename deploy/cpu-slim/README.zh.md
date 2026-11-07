# CPU 精简小智

基线 `4f6e9ec6`。MIT 许可证在仓库根目录。SenseVoice 权重许可证在 `licenses/FunASR-MODEL_LICENSE.txt`。依赖锁是 `requirements-cpu.lock`。安装使用 `--no-deps`，避免 FunASR 再拉进未锁定的 `transformers` / `modelscope`。

镜像只在这台测试机构建和 load。没有 push。没有在 15GB 生产机上构建或加载。`bootstrap.sh` 不覆盖已有 `.config.yaml` 和 `model.pt`。

## 实测数字

| 项 | 字节 |
| --- | --- |
| 镜像展开（`docker image inspect` Size） | 2890369574 |
| `docker save` 未压缩 | 694630912 |
| `xiaozhi-cpu-slim.tar.gz` | 688617801 |
| tar.gz SHA-256 | `ccb54890b09de2219dc11187b68538ba5ceb4603a2d5802f6711299527b41582` |
| 清空镜像后 `/var/lib/docker` | 2718142 |
| `docker load` 该 tar.gz 之后 | 2768340556 |
| load 磁盘增量 | 2765622414 |
| tar.gz 还留在盘上时的合计 | 3454240215 |
| 构建缓存（prune 前，`docker system df`） | 2.92GB |
| 容器 cgroup `memory.peak` | 3156066304 |
| 先前 venv 进程 VmHWM | 3267612 kB |

基础镜像 `python:3.10.22-slim-bookworm@sha256:5be5aaecb962a41567bc8041f1e9e3432cb085b037fe057f9a562630b2e4b370`。镜像内 `torch 2.2.2+cpu`，`torch.version.cuda is None`，没有 `libtorch_cuda*`。

测试机 `free`：16003 MiB，Swap 0。容器峰值约 2.94GiB，venv 进程 VmHWM 约 3.12GiB。可用内存低于这个峰值时可能被 OOM 杀掉。没有测过更小内存，也不保证加了交换区就稳。生产机的 `free -h` 还没拿到，所以这里不写它的内存。

tar.gz 复制到交付目录时 `close` 返回 `Invalid argument`，文件变成 0 字节，已删掉。包没有附在 PR 上，也没有公开上传。SHA-256 对的是测试机上的 `/tmp/xz-runtime/out/xiaozhi-cpu-slim.tar.gz`。

## 已测行为

- 镜像容器挂上已有 `model.pt`（只读，SHA-256 `833ca2dcfdf8ec91bd4f31cfac36d6124e0c459074d5e909aec9cabe6204a3ea`）后完成 FunASR 加载。
- 本地假 OpenAI 接口只返回「你好」，没有请求 DeepSeek。EdgeTTS 真实合成。下行 32 个 Opus 包，按 24000Hz 解码为 1440 采样/帧（60ms），合计 1.92 秒。日志有「发送第一段语音: 你好」。
- 客户端 hello 报上行 16000。服务端回复 24000/60ms。StackChan v0.14.3 用这个回复里的采样率开下行解码器。libopus 在 16000 下也能解出 960 采样，那是重采样，不能当成这包就是 16kHz。
- 回环 nginx TLS：无 Bearer 和错误 Bearer 的 HTTP/WebSocket 都是 401。`Bearer local-test-bearer` 可以通过，并完成 hello。这是测试口令，不是 `server.auth.token`。证书是临时自签，没有部署到生产机。

DeepSeek 云端整段对话未测。

## 生产机可以怎么做

等三样东西到了再动生产机：`free -h`、公网域名和正式证书、DeepSeek 密钥。密钥只写进已有 `data/.config.yaml` 的副本，不要覆盖原文件。

不要在那台机器上 `docker build`。构建缓存实测还有 2.92GB。可以做的是把上面的 tar.gz 传上去之后 `docker load`，再删掉 tar。load 增量 2765622414 字节，tar 还在时合计 3454240215 字节。用户给出的空闲是 8.9GB，这个 load 峰值落在里面。这不包含再构建，也不包含再拉官方 CUDA 镜像。`model.pt` 继续用已经在盘上的那份。

服务只绑 `127.0.0.1:8000`。公网用 `tls-proxy/nginx.conf` 这种反代：TLS 终止，校验 `Authorization: Bearer <你自己定的口令>`，再转到 `127.0.0.1:8000`。设备里的 XiaoZhi URL 用 `wss://域名/xiaozhi/v1/`，Bearer 填同一口令。原生签发续签没核实，不要填 `server.auth.token`。

`model_name` 仍按 2026-11-07 文档用 `deepseek-flash`，可改。没有密钥就不要启动对外服务。
