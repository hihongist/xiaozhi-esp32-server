"""StackChan v0.14.3 风格的 WebSocket hello 冒烟。

设备侧见 ciniml/stackchan-idf v0.14.3 components/conversation/xiaozhi_client.cpp：
Device-Id 为 STA MAC，Client-Id 为 00000000-0000-0000-0000-<machex>，
可选 Authorization: Bearer，Protocol-Version: 1，
hello 为 opus/16000/1/60ms，features.mcp=false，随后 listen state=start mode=auto。
"""
import asyncio
import json
import sys

import opuslib_next
import websockets


async def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else "ws://127.0.0.1:8000/xiaozhi/v1/"
    headers = {
        "Device-Id": "02:00:00:00:00:01",
        "Client-Id": "00000000-0000-0000-0000-020000000001",
        "Protocol-Version": "1",
        "Authorization": "Bearer stage-smoke-token",
    }
    hello = {
        "type": "hello",
        "version": 1,
        "transport": "websocket",
        "features": {"mcp": False},
        "audio_params": {
            "format": "opus",
            "sample_rate": 16000,
            "channels": 1,
            "frame_duration": 60,
        },
    }
    async with websockets.connect(url, additional_headers=headers, open_timeout=10) as ws:
        await ws.send(json.dumps(hello))
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
        print("HELLO_REPLY", json.dumps(msg, ensure_ascii=False))
        if msg.get("type") != "hello" or msg.get("transport") != "websocket" or not msg.get("session_id"):
            raise SystemExit("hello reply missing required fields")
        await ws.send(json.dumps({
            "type": "listen",
            "state": "start",
            "mode": "auto",
            "session_id": msg["session_id"],
        }))
        enc = opuslib_next.Encoder(16000, 1, opuslib_next.APPLICATION_AUDIO)
        frame = enc.encode(b"\x00\x00" * 960, 960)
        await ws.send(frame)
        print("OPUS_FRAME_BYTES", len(frame))
        await ws.send(json.dumps({"type": "ping"}))
        print("HELLO_SMOKE_OK")


if __name__ == "__main__":
    asyncio.run(main())
