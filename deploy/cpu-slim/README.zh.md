# CPU 精简小智（本阶段：venv 已测，镜像未测）

基线源码 `4f6e9ec6b1169ac6f3dbd78b5d8b1f717e493b9b`。服务端许可证是仓库根目录 MIT `LICENSE`。SenseVoiceSmall 权重适用 `licenses/FunASR-MODEL_LICENSE.txt`（FunASR Model License 1.1）。依赖锁定见 `requirements-cpu.lock`。

本阶段没有构建镜像，没有 `docker save` / `docker load`，没有改生产机，没有删除数据，没有 DeepSeek 请求，没有发布镜像。

## 已测（隔离 venv，Python 3.10.22）

| 项 | 结果 |
| --- | --- |
| 官方 CPU torch `2.2.2+cpu` + torchaudio `2.2.2+cpu` | `torch.version.cuda is None`。`torch/lib` 只有 `libtorch_cpu.so`（450MiB），没有 `libtorch_cuda*.so` |
| 选定模块启动 | VAD Silero（onnxruntime 1.20.1 CPU）、ASR FunASR 1.4.16、LLM DeepSeek 客户端、TTS 配置为 EdgeTTS、Memory nomem、Intent nointent。监听 `127.0.0.1:8000` |
| 中文 ASR | 真实。`model.pt` SHA-256 `833ca2dcfdf8ec91bd4f31cfac36d6124e0c459074d5e909aec9cabe6204a3ea`（与 Hugging Face LFS 一致，未入库）。`example/zh.mp3` 识别为「开放时间早上9点至下午5点。」 |
| WebSocket hello | 真实。对齐 ciniml/stackchan-idf v0.14.3：Device-Id、Client-Id、Protocol-Version、可选 Bearer、opus 16k/60ms、`features.mcp=false`、`listen mode=auto`。服务端回了 `type=hello`、`transport=websocket`、`session_id`。静音 Opus 帧已发送，连接未因此断开 |
| EdgeTTS | 真实合成，未走完整对话链路。`zh-CN-XiaoxiaoNeural` 文本「你好」得到 11232 字节音频 |
| 目录占用 | venv 展开 1.4G，其中 torch 目录 686M。`model.pt` 另计 893M，已在用户盘上的那份不要再复制进镜像 |

服务进程（PID 9884，加载权重并完成 hello 之后）：RSS 1593580 kB（约 1.52GiB），VmHWM 3267612 kB（约 3.12GiB）。这是这一次加载的峰值，不是生产机内存。

## 未测

- Docker 镜像。本环境 Docker Engine 29.9.3 的守护进程可以连通，存储驱动是 overlayfs，`containerd snapshotter=true`。没有执行 build，所以没有压缩层、展开层和 `docker load` 峰值。
- 听中文 → DeepSeek → 下行语音的端到端。没有 API 密钥，不能声称这条链路通过。
- 设备实机播放。hello 回复里的 `audio_params` 被服务端换成了客户端上报的 16000Hz，而连接建立日志仍写「配置输出音频采样率为: 24000」。下行 Opus 没在本阶段生成，播放采样率未验证。
- 公网 TLS 反代，以及与设备可选 Bearer 兼容的部署层认证。这是后续要求，本阶段不实现、不部署。
- 原生 `AuthManager` 签发与续签。它生成的是绑定 `client_id|device_id` 的 `HMAC.timestamp`，默认约 30 天过期。没有核实固件会续签，这里不提供、不编造 `server.auth.token`。冒烟时 `auth.enabled=false`，带上的 Bearer 没有被服务端校验。

## 磁盘

用户描述的生产盘是 15GB 总量、已用 5.3GB、空闲 8.9GB，另有两个不能动的容器。本阶段没有在那台机器上复测。只根据这里的 venv：Python 依赖展开已经 1.4G，权重 893M 已在盘上。Docker 29 还会同时保留压缩内容和展开快照，构建或 load 时峰值高于最终镜像。在镜像数字测出来之前，不能判断 8.9GB 够不够，也不要在生产机上构建或加载。

官方 `server_latest` 解压 `libtorch_cuda_linalg.so` 时磁盘满，是 CUDA 轮子的问题。CPU 轮子去掉了该文件，但这只说明 venv 里没有它，不能外推成「生产机一定装得下镜像」。

## 依赖取舍（按真实 import）

SenseVoice 注册实际还需要：`rapidfuzz`、`tiktoken`、`jamo`、`jaconv`、`torch-complex`、`regex`、`hydra-core`、`sentencepiece`，以及 `librosa` 带进来的 `numba` / `llvmlite` / `scipy`。`modelscope`、`transformers`、`umap-learn`、`oss2`、`sherpa-onnx`、`vosk`、`mcp`、`httpx2` 没有装。`httpx2` 2.16.0 要求 Python ≥3.11，服务端 MCP 改为第一次初始化时再导入，语音进程启动时不导入它。`pytorch_wpe` 未装；本次加载走的是 `WavFrontend`。

`am.mvn`（11203 字节，SHA-256 `29b3c740a2c0cfc6b308126d31d7f265fa2be74f3bb095cd2f143ea970896ae5`）原来不在仓库里，本地模型加载需要它，已放入 `models/SenseVoiceSmall/`。`model.pt` 继续只挂载，不入库。

## 配置

`config.cpu-slim.yaml.example` 选择 FunASR + SileroVAD + DeepSeek + EdgeTTS。`model_name` 写成官方文档当前的 `deepseek-flash`，可以改。`bootstrap.sh <目录>` 只在目标不存在时复制 example，已有 `.config.yaml` 和 `model.pt` 都不改。它不会把 example 自动变成生效的 `.config.yaml`。已有官方模板若没有这些 `selected_module`，需要人工合并，不要覆盖原文件。
