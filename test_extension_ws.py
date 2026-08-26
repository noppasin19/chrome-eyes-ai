#!/usr/bin/env python3
"""
Unit test for WebSocket extension bridge protocol.
Simulates a Chrome Extension WebSocket client and tests check, screenshot, and dom commands.
"""

import asyncio
import base64
import json
import unittest
import websockets
from scripts.extension_bridge import execute_command, WS_HOST, WS_PORT

class TestWebSocketBridge(unittest.IsolatedAsyncioTestCase):

    async def mock_extension_client(self, delay=0.1):
        """Simulate Chrome Extension connecting to Python server."""
        await asyncio.sleep(delay)
        uri = f"ws://{WS_HOST}:{WS_PORT}"
        async with websockets.connect(uri) as ws:
            # Send handshake
            await ws.send(json.dumps({"type": "handshake", "client": "chrome_extension"}))
            # Wait for command
            msg_raw = await ws.recv()
            cmd = json.loads(msg_raw)
            action = cmd.get("action")

            # Mock responses
            if action == "check":
                resp = {
                    "id": cmd["id"],
                    "status": "success",
                    "action": "check",
                    "title": "YouTube",
                    "url": "https://www.youtube.com"
                }
            elif action == "screenshot":
                resp = {
                    "id": cmd["id"],
                    "status": "success",
                    "action": "screenshot",
                    "title": "YouTube",
                    "url": "https://www.youtube.com",
                    "data_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
                }
            elif action == "goto":
                resp = {
                    "id": cmd["id"],
                    "status": "success",
                    "action": "goto",
                    "url": cmd.get("url")
                }
            else:
                resp = {"id": cmd["id"], "status": "success", "action": action}

            await ws.send(json.dumps(resp))

    async def test_check_command(self):
        # Start mock extension in background
        client_task = asyncio.create_task(self.mock_extension_client())
        # Run bridge command
        res = await execute_command({"action": "check"}, timeout=3.0)
        await client_task

        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("title"), "YouTube")

    async def test_goto_command(self):
        client_task = asyncio.create_task(self.mock_extension_client())
        res = await execute_command({"action": "goto", "url": "https://www.youtube.com/results?search_query=piggaploy"}, timeout=3.0)
        await client_task

        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("url"), "https://www.youtube.com/results?search_query=piggaploy")

if __name__ == "__main__":
    unittest.main()
