# CPU 精简小智

**停。** 生产机 `free -h`：总内存 961MiB，可用 559MiB，swap 255MiB 里只剩 201MiB。本路线测到的容器 `memory.peak` 是 3156066304 字节（约 2.94GiB），venv 进程 VmHWM 是 3267612 kB（约 3.12GiB）。961MiB 装不下这次加载。这是硬性不适配，不是再调参能解决的。不要把镜像 load 到这台机器，也不要在这里继续做本地识别。已生成的包保留，不删除。StackChan 的离线角色、触摸、喂食和动作不在这个服务端仓库里做；语音后端另案。

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

## 不要部署到这台 1GB 机器

上面的磁盘数字只说明测试机上的镜像有多大。生产机内存是 961MiB，低于实测加载峰值，load 或启动都会内存不足。分块包已经写在测试机的 artifacts 里，不再继续交付，也不再做这条本地识别路线。
