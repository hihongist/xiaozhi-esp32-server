"""Mock DeepSeek with a local OpenAI-compatible stream, then require real EdgeTTS Opus.

The LLM reply is fixed to 你好. This does not call api.deepseek.com and is not an
end-to-end cloud pass. Uplink stays 16 kHz. Downlink must match the server hello
sample_rate, which StackChan v0.14.3 uses as the Opus decoder rate.
"""
import asyncio
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import opuslib_next
import websockets

MOCK_TEXT = "你好"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("MOCK " + (fmt % args) + "\n")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        _ = self.rfile.read(length)
        body = (
            'data: {"id":"mock","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"role":"assistant","content":"你好"},"finish_reason":null}]}\n\n'
            'data: {"id":"mock","object":"chat.completion.chunk","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}\n\n'
            "data: [DONE]\n\n"
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve(port: int) -> ThreadingHTTPServer:
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def decode_at(packet: bytes, rate: int):
    frame_samples = rate * 60 // 1000
    decoder = opuslib_next.Decoder(rate, 1)
    try:
        pcm = decoder.decode(packet, frame_samples)
    except Exception as exc:
        return f"fail:{type(exc).__name__}"
    return f"ok samples={len(pcm)//2}"


async def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else "ws://127.0.0.1:8000/xiaozhi/v1/"
    headers = {
        "Device-Id": "02:00:00:00:00:01",
        "Client-Id": "00000000-0000-0000-0000-020000000001",
        "Protocol-Version": "1",
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
    texts = []
    packets = []
    async with websockets.connect(url, additional_headers=headers, open_timeout=10, max_size=None) as ws:
        await ws.send(json.dumps(hello))
        reply = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
        print("HELLO_REPLY", json.dumps(reply, ensure_ascii=False))
        rate = int(reply["audio_params"]["sample_rate"])
        frame_ms = int(reply["audio_params"]["frame_duration"])
        if rate != 24000 or frame_ms != 60:
            raise SystemExit(f"server hello rate/frame {rate}/{frame_ms} is not the configured 24000/60 downlink")
        await asyncio.sleep(2)
        await ws.send(json.dumps({
            "session_id": reply["session_id"],
            "type": "listen",
            "state": "detect",
            "text": "请回复",
        }))
        deadline = asyncio.get_event_loop().time() + 40
        stop = False
        while asyncio.get_event_loop().time() < deadline and not stop:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
            except asyncio.TimeoutError:
                break
            if isinstance(msg, bytes):
                packets.append(msg)
                continue
            data = json.loads(msg)
            print("JSON", json.dumps(data, ensure_ascii=False)[:300])
            if data.get("type") == "tts" and data.get("state") == "sentence_start":
                texts.append(data.get("text") or "")
            if data.get("type") == "tts" and data.get("state") == "stop":
                stop = True
    print("TTS_TEXTS", texts)
    print("OPUS_PACKETS", len(packets), "BYTES", sum(len(p) for p in packets))
    if not packets:
        raise SystemExit("no downlink opus")
    if MOCK_TEXT not in "".join(texts):
        raise SystemExit("tts text did not contain the mock reply")
    sample = packets[len(packets) // 2]
    print("MID_PACKET_BYTES", len(sample))
    print("DECODE_24000", decode_at(sample, 24000))
    print("DECODE_16000", decode_at(sample, 16000))
    decoder = opuslib_next.Decoder(24000, 1)
    total = 0
    for packet in packets:
        pcm = decoder.decode(packet, 1440)
        total += len(pcm) // 2
    print("PCM_SAMPLES_24K", total, "MS", round(total / 24000 * 1000))
    print("DOWNLINK_OPUS_OK")


if __name__ == "__main__":
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    if port:
        serve(port)
    asyncio.run(main())
