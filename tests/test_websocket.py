"""
Automated unit test for WebSocket streaming from background worker threads
"""
import asyncio
import json
import threading
import time
import unittest
import requests
import websockets
import uvicorn
from src.api.server import create_app


class TestWebSocketStreaming(unittest.TestCase):
    def test_live_websocket_delivery_from_worker_threads(self):
        test_port = 8798
        base_url = f"http://127.0.0.1:{test_port}"
        ws_url = f"ws://127.0.0.1:{test_port}/ws"

        app = create_app(use_virtual=True)
        config = uvicorn.Config(app, host="127.0.0.1", port=test_port, log_level="error")
        server = uvicorn.Server(config)

        t = threading.Thread(target=server.run, daemon=True)
        t.start()

        for _ in range(25):
            try:
                r = requests.get(f"{base_url}/api/status", timeout=0.2)
                if r.status_code == 200:
                    break
            except Exception:
                time.sleep(0.08)

        # Select output
        ports = requests.get(f"{base_url}/api/ports").json()
        out_name = ports["outputs"][0]["name"]
        requests.post(f"{base_url}/api/ports/output/select", json={"port_name": out_name})

        received = []

        async def _client_coro():
            async with websockets.connect(ws_url) as ws:
                # Trigger HTTP send in background thread worker
                requests.post(f"{base_url}/api/send/program-change", json={
                    "channel": 1,
                    "program": 18,
                    "preset_convention": "0-127",
                })
                raw = await asyncio.wait_for(ws.recv(), timeout=2.0)
                received.append(json.loads(raw))

        asyncio.run(_client_coro())
        server.should_exit = True
        t.join(timeout=1.0)

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["type"], "midi_message")
        self.assertEqual(received[0]["message"]["data1"], 18)


if __name__ == "__main__":
    unittest.main()
