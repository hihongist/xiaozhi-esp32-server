# 私下交付：分块 tar.gz

整包没有放进 git，也没有附在 PR 上，没有公开 push 或 release。

单文件 `xiaozhi-cpu-slim.tar.gz`（688617801 字节）写入 `/opt/cursor/artifacts/` 时失败：

```
cp: failed to close '/opt/cursor/artifacts/xiaozhi-cpu-slim.tar.gz': Invalid argument
```

关闭后该路径上的文件是 0 字节，已删除。没有再重试整包。没有探测 20MiB 和 688617801 之间的精确上限。20MiB 分块可以写入并重新读出。

分块在 `/opt/cursor/artifacts/`，每块最多 20971520 字节，共 33 块。清单：

`/opt/cursor/artifacts/xiaozhi-cpu-slim.tar.gz.SHA256SUMS`

重组后的 SHA-256 与原包一致：

`ccb54890b09de2219dc11187b68538ba5ceb4603a2d5802f6711299527b41582`

原包仍在测试机 `/tmp/xz-runtime/out/xiaozhi-cpu-slim.tar.gz`，没有删除。重组文件是另一个路径，校验通过后可以丢掉重组副本。

## 重组

把 33 个 `xiaozhi-cpu-slim.tar.gz.part-000` 到 `part-032` 放在同一目录，按文件名顺序拼接：

```sh
cat xiaozhi-cpu-slim.tar.gz.part-* > xiaozhi-cpu-slim.tar.gz
sha256sum xiaozhi-cpu-slim.tar.gz
```

必须得到上面的 SHA-256，并且大小是 688617801。然后：

```sh
docker load -i xiaozhi-cpu-slim.tar.gz
```

这只恢复镜像 `xiaozhi-cpu-slim:local`。不要在 15GB 生产机上 build。load 磁盘增量等数字见 `../measurements/image-sizes.txt`。

各块 SHA-256 见同目录 `SHA256SUMS.txt`。
