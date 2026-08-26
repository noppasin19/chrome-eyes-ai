#!/Users/nop/AI/multi_agents/spy_satellite/.venv/bin/python3
"""
Chrome Native Messaging Host for Antigravity & Claude Code
Spawned automatically by Google Chrome when the extension connects.
Bridges commands between the local Unix Domain Socket (/tmp/antigravity_chrome.sock) and Chrome stdio.
"""

import asyncio
import json
import os
import struct
import sys

UNIX_SOCKET_PATH = "/tmp/antigravity_chrome.sock"
pending_requests = {}
chrome_writer_lock = asyncio.Lock()

def read_message_sync():
    """Read a single Native Messaging frame from sys.stdin."""
    raw_length = sys.stdin.buffer.read(4)
    if not raw_length or len(raw_length) < 4:
        return None
    message_length = struct.unpack("@I", raw_length)[0]
    raw_message = sys.stdin.buffer.read(message_length)
    if not raw_message or len(raw_message) < message_length:
        return None
    return json.loads(raw_message.decode("utf-8"))

def send_message_sync(message_dict):
    """Write a single Native Messaging frame to sys.stdout."""
    encoded_content = json.dumps(message_dict).encode("utf-8")
    length_prefix = struct.pack("@I", len(encoded_content))
    sys.stdout.buffer.write(length_prefix)
    sys.stdout.buffer.write(encoded_content)
    sys.stdout.buffer.flush()

async def chrome_stdin_reader():
    """Continuously read messages from Chrome via stdin in a separate thread."""
    loop = asyncio.get_running_loop()
    while True:
        try:
            msg = await loop.run_in_executor(None, read_message_sync)
            if msg is None:
                break
            req_id = msg.get("id")
            if req_id and req_id in pending_requests:
                future = pending_requests[req_id]
                if not future.done():
                    future.set_result(msg)
        except Exception:
            break

async def handle_unix_client(reader, writer):
    """Handle CLI command requests coming from extension_bridge.py via Unix socket."""
    try:
        data = await reader.read(1024 * 1024) # Up to 1MB request
        if not data:
            writer.close()
            await writer.wait_closed()
            return

        command = json.loads(data.decode("utf-8"))
        req_id = command.get("id") or str(asyncio.get_running_loop().time())
        command["id"] = req_id

        # Register future for response
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        pending_requests[req_id] = future

        # Send command to Chrome
        async with chrome_writer_lock:
            send_message_sync(command)

        # Wait for response from Chrome (up to 8 seconds)
        try:
            response = await asyncio.wait_for(future, timeout=8.0)
            writer.write(json.dumps(response).encode("utf-8"))
            await writer.drain()
        except asyncio.TimeoutError:
            err_resp = {"status": "error", "message": f"Timeout waiting for Chrome response to {command.get('action')}"}
            writer.write(json.dumps(err_resp).encode("utf-8"))
            await writer.drain()
        finally:
            pending_requests.pop(req_id, None)

    except Exception as e:
        err_resp = {"status": "error", "message": f"Native host error: {e}"}
        try:
            writer.write(json.dumps(err_resp).encode("utf-8"))
            await writer.drain()
        except Exception:
            pass
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass

async def main():
    # Clean up existing Unix socket if present
    if os.path.exists(UNIX_SOCKET_PATH):
        try:
            os.unlink(UNIX_SOCKET_PATH)
        except Exception:
            pass

    # Start Unix Domain Socket server for CLI tools
    server = await asyncio.start_unix_server(handle_unix_client, path=UNIX_SOCKET_PATH)
    os.chmod(UNIX_SOCKET_PATH, 0o777)

    # Start background Chrome stdin reader
    stdin_task = asyncio.create_task(chrome_stdin_reader())

    try:
        await stdin_task
    finally:
        server.close()
        await server.wait_closed()
        if os.path.exists(UNIX_SOCKET_PATH):
            try:
                os.unlink(UNIX_SOCKET_PATH)
            except Exception:
                pass

if __name__ == "__main__":
    asyncio.run(main())
