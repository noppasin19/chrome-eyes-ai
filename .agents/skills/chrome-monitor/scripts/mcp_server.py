#!/usr/bin/env python3
"""
Antigravity Chrome Monitor - Model Context Protocol (MCP) Server
Exposes Chrome monitoring and automation tools directly as first-class MCP tools
for Antigravity, Claude Code, Claude Desktop, and Cursor.
"""

import json
import os
import subprocess
import sys
import time
from typing import Optional
import httpx2
from mcp.server.mcpserver import MCPServer

SERVER_URL = "http://127.0.0.1:8765"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_SCRIPT = os.path.join(SCRIPT_DIR, "bridge_server.py")

# Initialize MCP Server
mcp = MCPServer(
    name="chrome_monitor",
    version="2.1.0",
    instructions="Tools to inspect, monitor, click, type, navigate, and manage active Google Chrome tabs."
)

def ensure_server_running():
    """Ensure the background bridge server (ws://127.0.0.1:8765) is running."""
    try:
        with httpx2.Client(timeout=1.0) as client:
            r = client.get(f"{SERVER_URL}/api/check")
            if r.status_code == 200:
                return True
    except Exception:
        pass

    # Start bridge_server in background
    python_bin = sys.executable
    subprocess.Popen(
        [python_bin, SERVER_SCRIPT],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    for _ in range(15):
        time.sleep(0.2)
        try:
            with httpx2.Client(timeout=1.0) as client:
                r = client.get(f"{SERVER_URL}/api/check")
                if r.status_code == 200:
                    return True
        except Exception:
            pass
    return False

@mcp.tool()
def chrome_check() -> str:
    """Check connection status and get details about the currently active Google Chrome tab."""
    ensure_server_running()
    with httpx2.Client(timeout=10.0) as client:
        res = client.get(f"{SERVER_URL}/api/check").json()
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
def chrome_tabs() -> str:
    """List all open tabs in Google Chrome with their IDs, Titles, URLs, and Active status."""
    ensure_server_running()
    with httpx2.Client(timeout=10.0) as client:
        res = client.get(f"{SERVER_URL}/api/tabs").json()
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
def chrome_inspect_all() -> str:
    """Inspect all open tabs silently in the background (0 tab switching) and extract their headings and key elements."""
    ensure_server_running()
    with httpx2.Client(timeout=15.0) as client:
        res = client.get(f"{SERVER_URL}/api/inspect_all").json()
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
def chrome_switch_tab(tab_id: int) -> str:
    """Switch focus to a specific Chrome tab by its tab ID."""
    ensure_server_running()
    with httpx2.Client(timeout=10.0) as client:
        res = client.post(f"{SERVER_URL}/api/switch_tab", json={"tab_id": tab_id}).json()
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
def chrome_new_tab(url: str = "https://google.com") -> str:
    """Open a URL in a new Google Chrome tab."""
    ensure_server_running()
    with httpx2.Client(timeout=10.0) as client:
        res = client.post(f"{SERVER_URL}/api/new_tab", json={"url": url}).json()
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
def chrome_close_tab(tab_id: int) -> str:
    """Close a specific Google Chrome tab by its tab ID."""
    ensure_server_running()
    with httpx2.Client(timeout=10.0) as client:
        res = client.post(f"{SERVER_URL}/api/close_tab", json={"tab_id": tab_id}).json()
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
def chrome_goto(url: str) -> str:
    """Navigate the active Chrome tab to a new URL."""
    ensure_server_running()
    with httpx2.Client(timeout=12.0) as client:
        res = client.post(f"{SERVER_URL}/api/goto", json={"url": url}).json()
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
def chrome_screenshot(output_path: str = "current_tab.png", tab_id: Optional[int] = None) -> str:
    """Capture a screenshot of the active (or specified) Chrome tab and save it to output_path."""
    ensure_server_running()
    q = f"?output={output_path}" + (f"&tab_id={tab_id}" if tab_id else "")
    with httpx2.Client(timeout=15.0) as client:
        res = client.get(f"{SERVER_URL}/api/screenshot{q}").json()
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
def chrome_dom(tab_id: Optional[int] = None) -> str:
    """Extract structured DOM elements (Headings, buttons, inputs, links with IDs) from the tab. Password inputs are masked."""
    ensure_server_running()
    q = f"?tab_id={tab_id}" if tab_id else ""
    with httpx2.Client(timeout=10.0) as client:
        res = client.get(f"{SERVER_URL}/api/dom{q}").json()
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
def chrome_text(tab_id: Optional[int] = None) -> str:
    """Extract clean readable text content from the page (ideal for AI article summarization and documentation reading)."""
    ensure_server_running()
    q = f"?tab_id={tab_id}" if tab_id else ""
    with httpx2.Client(timeout=10.0) as client:
        res = client.get(f"{SERVER_URL}/api/text{q}").json()
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
def chrome_links(tab_id: Optional[int] = None) -> str:
    """Extract all hyperlinks (anchor text and destination URLs) from the page."""
    ensure_server_running()
    q = f"?tab_id={tab_id}" if tab_id else ""
    with httpx2.Client(timeout=10.0) as client:
        res = client.get(f"{SERVER_URL}/api/links{q}").json()
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
def chrome_click(text: Optional[str] = None, selector: Optional[str] = None) -> str:
    """Click an element on the active page by visible text or CSS selector. Automatically waits for SPA element rendering."""
    ensure_server_running()
    payload = {"text": text, "selector": selector}
    with httpx2.Client(timeout=12.0) as client:
        res = client.post(f"{SERVER_URL}/api/click", json=payload).json()
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
def chrome_type(text: str, selector: Optional[str] = None, enter: bool = True) -> str:
    """Type text into an input field on the active page. Automatically focuses, triggers input events, and optionally presses Enter."""
    ensure_server_running()
    payload = {"text": text, "selector": selector, "enter": enter}
    with httpx2.Client(timeout=12.0) as client:
        res = client.post(f"{SERVER_URL}/api/type", json=payload).json()
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
def chrome_scroll(direction: str = "down", amount: int = 500) -> str:
    """Scroll the active page up, down, top, or bottom."""
    ensure_server_running()
    payload = {"direction": direction, "amount": amount}
    with httpx2.Client(timeout=10.0) as client:
        res = client.post(f"{SERVER_URL}/api/scroll", json=payload).json()
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
def chrome_select(selector: str, value: Optional[str] = None, text: Optional[str] = None) -> str:
    """Select an option in a dropdown (<select>) element by option value or visible text."""
    ensure_server_running()
    payload = {"selector": selector, "value": value, "text": text}
    with httpx2.Client(timeout=10.0) as client:
        res = client.post(f"{SERVER_URL}/api/select", json=payload).json()
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
def chrome_reload(hard: bool = False) -> str:
    """Reload the active tab (optionally hard reload bypassing cache)."""
    ensure_server_running()
    with httpx2.Client(timeout=10.0) as client:
        res = client.post(f"{SERVER_URL}/api/reload", json={"bypass_cache": hard}).json()
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
def chrome_network() -> str:
    """Inspect recent network HTTP requests and API calls made by open tabs."""
    ensure_server_running()
    with httpx2.Client(timeout=10.0) as client:
        res = client.get(f"{SERVER_URL}/api/network").json()
    return json.dumps(res, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    # Run standard stdio MCP Server
    mcp.run(transport="stdio")
