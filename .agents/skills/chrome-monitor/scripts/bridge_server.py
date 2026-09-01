#!/usr/bin/env python3
"""
Antigravity Chrome Monitor - Unified Secure HTTP & WebSocket Bridge Server
Listens on http://127.0.0.1:8765
Endpoints:
- /ws : WebSocket endpoint for Google Chrome Extension
- /api/check : Check connection & active tab
- /api/tabs : List all tabs
- /api/inspect_all : Inspect all tabs in background (0 tab switching)
- /api/new_tab : Open new tab
- /api/close_tab : Close specific tab
- /api/switch_tab : Switch/focus tab
- /api/reload : Reload tab
- /api/screenshot : Capture screenshot
- /api/dom : Extract structured DOM (Password masked)
- /api/text : Extract clean readable text
- /api/links : Extract hyperlinks
- /api/scroll : Scroll page (up/down/top/bottom)
- /api/select : Select dropdown option
- /api/click : Click element
- /api/type : Type text into input
- /api/goto : Navigate URL
- /api/network : Network requests summary
"""

import asyncio
import base64
import json
import os
import sys
from aiohttp import web

HOST = "127.0.0.1"
PORT = 8765

extension_ws = None
pending_responses = {}

async def ws_handler(request):
    global extension_ws
    ws = web.WebSocketResponse(heartbeat=15.0)
    await ws.prepare(request)

    extension_ws = ws
    print("[SERVER] Chrome Extension connected via WebSocket!")

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    req_id = data.get("id")
                    if req_id and req_id in pending_responses:
                        future = pending_responses[req_id]
                        if not future.done():
                            future.set_result(data)
                except Exception as e:
                    print(f"[SERVER] Error parsing extension message: {e}")
            elif msg.type == web.WSMsgType.ERROR:
                print(f"[SERVER] WebSocket connection closed with exception {ws.exception()}")
    finally:
        if extension_ws is ws:
            extension_ws = None
        print("[SERVER] Chrome Extension disconnected.")

    return ws

async def send_command_to_extension(command_dict, timeout=12.0):
    global extension_ws
    if extension_ws is None or extension_ws.closed:
        return {
            "status": "error",
            "message": "Chrome Extension is not connected.",
            "hint": "Please open Google Chrome and ensure the 'Antigravity Chrome Monitor Bridge' extension is active."
        }

    req_id = command_dict.get("id") or str(asyncio.get_running_loop().time())
    command_dict["id"] = req_id

    loop = asyncio.get_running_loop()
    future = loop.create_future()
    pending_responses[req_id] = future

    try:
        await extension_ws.send_str(json.dumps(command_dict))
        result = await asyncio.wait_for(future, timeout=timeout)
        return result
    except asyncio.TimeoutError:
        return {
            "status": "error",
            "message": f"Timeout waiting for Chrome response to '{command_dict.get('action')}'"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        pending_responses.pop(req_id, None)

# --- HTTP API Handlers ---
async def api_check(request):
    res = await send_command_to_extension({"action": "check"})
    return web.json_response(res)

async def api_tabs(request):
    res = await send_command_to_extension({"action": "tabs"})
    return web.json_response(res)

async def api_inspect_all(request):
    res = await send_command_to_extension({"action": "inspect_all"})
    return web.json_response(res)

async def api_new_tab(request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    url = body.get("url") or request.query.get("url", "https://google.com")
    res = await send_command_to_extension({"action": "new_tab", "url": url})
    return web.json_response(res)

async def api_close_tab(request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    tab_id = body.get("tab_id") or request.query.get("tab_id")
    res = await send_command_to_extension({"action": "close_tab", "tab_id": tab_id})
    return web.json_response(res)

async def api_switch_tab(request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    tab_id = body.get("tab_id") or request.query.get("tab_id")
    res = await send_command_to_extension({"action": "switch_tab", "tab_id": tab_id})
    return web.json_response(res)

async def api_reload(request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    bypass_cache = body.get("bypass_cache", False)
    res = await send_command_to_extension({"action": "reload", "bypass_cache": bypass_cache})
    return web.json_response(res)

async def api_screenshot(request):
    tab_id = request.query.get("tab_id")
    cmd = {"action": "screenshot"}
    if tab_id:
        cmd["tab_id"] = tab_id
    res = await send_command_to_extension(cmd)
    output_path = request.query.get("output", "current_tab.png")
    if res.get("status") == "success" and "data_url" in res:
        data_url = res.pop("data_url")
        if "," in data_url:
            raw_base64 = data_url.split(",", 1)[1]
            image_data = base64.b64decode(raw_base64)
            abs_output = os.path.abspath(output_path)
            with open(abs_output, "wb") as f:
                f.write(image_data)
            res["screenshot_path"] = abs_output
            res["file_size_kb"] = round(len(image_data) / 1024, 2)
    return web.json_response(res)

async def api_dom(request):
    tab_id = request.query.get("tab_id")
    cmd = {"action": "dom"}
    if tab_id:
        cmd["tab_id"] = tab_id
    res = await send_command_to_extension(cmd)
    return web.json_response(res)

async def api_text(request):
    tab_id = request.query.get("tab_id")
    cmd = {"action": "text"}
    if tab_id:
        cmd["tab_id"] = tab_id
    res = await send_command_to_extension(cmd)
    return web.json_response(res)

async def api_links(request):
    tab_id = request.query.get("tab_id")
    cmd = {"action": "links"}
    if tab_id:
        cmd["tab_id"] = tab_id
    res = await send_command_to_extension(cmd)
    return web.json_response(res)

async def api_scroll(request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    direction = body.get("direction") or request.query.get("direction", "down")
    amount = body.get("amount") or request.query.get("amount", 500)
    res = await send_command_to_extension({"action": "scroll", "direction": direction, "amount": amount})
    return web.json_response(res)

async def api_select(request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    selector = body.get("selector") or request.query.get("selector")
    value = body.get("value") or request.query.get("value")
    text = body.get("text") or request.query.get("text")
    res = await send_command_to_extension({"action": "select", "selector": selector, "value": value, "text": text})
    return web.json_response(res)

async def api_click(request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    selector = body.get("selector") or request.query.get("selector")
    text = body.get("text") or request.query.get("text")
    res = await send_command_to_extension({"action": "click", "selector": selector, "text": text})
    return web.json_response(res)

async def api_type(request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    selector = body.get("selector") or request.query.get("selector")
    text = body.get("text") or request.query.get("text", "")
    enter = body.get("enter", True)
    res = await send_command_to_extension({"action": "type", "selector": selector, "text": text, "enter": enter})
    return web.json_response(res)

async def api_goto(request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    url = body.get("url") or request.query.get("url")
    if not url:
        return web.json_response({"status": "error", "message": "Missing 'url' parameter"}, status=400)
    res = await send_command_to_extension({"action": "goto", "url": url})
    return web.json_response(res)

async def api_network(request):
    res = await send_command_to_extension({"action": "network"})
    return web.json_response(res)


async def api_click_xy(request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    x = body.get("x") or request.query.get("x", 0)
    y = body.get("y") or request.query.get("y", 0)
    click_count = body.get("click_count", 1)
    tab_id = body.get("tab_id")
    cmd = {"action": "click_xy", "x": x, "y": y, "click_count": click_count}
    if tab_id:
        cmd["tab_id"] = tab_id
    res = await send_command_to_extension(cmd)
    return web.json_response(res)

async def api_drag(request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    from_x = body.get("from_x", 0)
    from_y = body.get("from_y", 0)
    to_x = body.get("to_x", 0)
    to_y = body.get("to_y", 0)
    tab_id = body.get("tab_id")
    cmd = {"action": "drag", "from_x": from_x, "from_y": from_y, "to_x": to_x, "to_y": to_y}
    if tab_id:
        cmd["tab_id"] = tab_id
    res = await send_command_to_extension(cmd)
    return web.json_response(res)

async def api_native_type(request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    txt = body.get("text", "")
    tab_id = body.get("tab_id")
    cmd = {"action": "native_type", "text": txt}
    if tab_id:
        cmd["tab_id"] = tab_id
    res = await send_command_to_extension(cmd)
    return web.json_response(res)

def create_app():
    app = web.Application()
    app.router.add_get("/ws", ws_handler)
    app.router.add_get("/api/check", api_check)
    app.router.add_get("/api/tabs", api_tabs)
    app.router.add_get("/api/inspect_all", api_inspect_all)
    app.router.add_post("/api/new_tab", api_new_tab)
    app.router.add_post("/api/close_tab", api_close_tab)
    app.router.add_post("/api/switch_tab", api_switch_tab)
    app.router.add_post("/api/reload", api_reload)
    app.router.add_get("/api/screenshot", api_screenshot)
    app.router.add_get("/api/dom", api_dom)
    app.router.add_get("/api/text", api_text)
    app.router.add_get("/api/links", api_links)
    app.router.add_post("/api/scroll", api_scroll)
    app.router.add_post("/api/select", api_select)
    app.router.add_post("/api/click", api_click)
    app.router.add_post("/api/click_xy", api_click_xy)
    app.router.add_post("/api/drag", api_drag)
    app.router.add_post("/api/native_type", api_native_type)
    app.router.add_post("/api/type", api_type)
    app.router.add_post("/api/goto", api_goto)
    app.router.add_get("/api/network", api_network)
    return app

if __name__ == "__main__":
    app = create_app()
    print(f"[START] Antigravity Chrome Bridge Server running at http://{HOST}:{PORT}")
    web.run_app(app, host=HOST, port=PORT)
