#!/usr/bin/env python3
"""
Antigravity Chrome Monitor - Secure Developer CLI Client
Communicates with bridge_server.py on http://127.0.0.1:8765

Supported Commands:
- check         : Check connection status and active tab
- tabs          : List all open tabs
- inspect_all   : Inspect all tabs silently in the background (0 tab switching)
- screenshot    : Capture screenshot of active/specified tab
- dom           : Extract DOM structure (headings & elements with password masking)
- text          : Extract clean readable text from the page
- links         : Extract all hyperlinks on the page
- scroll        : Scroll page (down, up, top, bottom)
- select        : Select option in dropdown (<select>)
- click         : Click button/link by text or selector
- type          : Type text into input field
- goto          : Navigate to URL
- new_tab       : Open URL in a new tab
- close_tab     : Close specific tab by ID
- reload        : Reload active tab
- network       : Inspect recent network requests
"""

import argparse
import json
import os
import subprocess
import sys
import time
import requests

SERVER_URL = "http://127.0.0.1:8765"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_SCRIPT = os.path.join(SCRIPT_DIR, "bridge_server.py")

def ensure_server_running():
    """Check if bridge_server is running; if not, launch it in background."""
    try:
        r = requests.get(f"{SERVER_URL}/api/check", timeout=1.0)
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
            r = requests.get(f"{SERVER_URL}/api/check", timeout=1.0)
            return True
        except Exception:
            pass
    return False

def inspect_all_tabs(json_output=False):
    """Inspect all open tabs silently in the background (Zero tab switching!)."""
    try:
        res = requests.get(f"{SERVER_URL}/api/inspect_all", timeout=15.0).json()
    except Exception as e:
        res = {"status": "error", "message": str(e)}

    if json_output:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        if res.get("status") == "success":
            results = res.get("tabs_inspection", [])
            print(f"\n[BACKGROUND INSPECTION] Found {res.get('total_tabs', len(results))} open tabs (0 tab switches):\n" + "=" * 65)
            for idx, item in enumerate(results, 1):
                act = "🟢 [ACTIVE]" if item.get("active") else "💤"
                print(f"\n📑 [{idx}] {act} {item['title']}")
                print(f"    URL: {item['url']}")
                if item.get("top_headings"):
                    print(f"    📌 Headings: {', '.join(item['top_headings'][:3])}")
                if item.get("key_elements"):
                    print(f"    🔘 Elements: {', '.join(item['key_elements'][:4])}")
                if item.get("summary"):
                    print(f"    ℹ️ Info: {item['summary']}")
            print("\n" + "=" * 65)
        else:
            print(f"[ERROR] {res.get('message')}")
            if "hint" in res:
                print(f"  Hint: {res['hint']}")

    return res

def main():
    parser = argparse.ArgumentParser(description="Antigravity Chrome Monitor - Secure Dev CLI")
    parser.add_argument("command", choices=[
        "check", "tabs", "inspect_all", "switch_tab", "new_tab", "close_tab", "reload",
        "screenshot", "dom", "text", "links", "scroll", "select", "click", "type", "goto", "network"
    ], help="Action to perform on Chrome")
    parser.add_argument("--output", type=str, default="current_tab.png",
                        help="Output path for screenshot (default: current_tab.png)")
    parser.add_argument("--tab-id", type=int, help="Target Tab ID")
    parser.add_argument("--selector", type=str, help="CSS selector")
    parser.add_argument("--text", type=str, help="Text to click, type, or match")
    parser.add_argument("--value", type=str, help="Value for dropdown select")
    parser.add_argument("--url", type=str, help="URL for navigation or new tab")
    parser.add_argument("--direction", choices=["down", "up", "top", "bottom"], default="down",
                        help="Scroll direction (default: down)")
    parser.add_argument("--amount", type=int, default=500, help="Scroll pixel amount")
    parser.add_argument("--enter", action="store_true", help="Press Enter after typing")
    parser.add_argument("--hard", action="store_true", help="Hard reload bypassing cache")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    ensure_server_running()

    if args.command == "inspect_all":
        inspect_all_tabs(json_output=args.json)
        return

    try:
        if args.command == "check":
            res = requests.get(f"{SERVER_URL}/api/check", timeout=10.0).json()
        elif args.command == "tabs":
            res = requests.get(f"{SERVER_URL}/api/tabs", timeout=10.0).json()
        elif args.command == "switch_tab":
            res = requests.post(f"{SERVER_URL}/api/switch_tab", json={"tab_id": args.tab_id}, timeout=10.0).json()
        elif args.command == "new_tab":
            res = requests.post(f"{SERVER_URL}/api/new_tab", json={"url": args.url or "https://google.com"}, timeout=10.0).json()
        elif args.command == "close_tab":
            res = requests.post(f"{SERVER_URL}/api/close_tab", json={"tab_id": args.tab_id}, timeout=10.0).json()
        elif args.command == "reload":
            res = requests.post(f"{SERVER_URL}/api/reload", json={"bypass_cache": args.hard}, timeout=10.0).json()
        elif args.command == "screenshot":
            q = f"?output={args.output}" + (f"&tab_id={args.tab_id}" if args.tab_id else "")
            res = requests.get(f"{SERVER_URL}/api/screenshot{q}", timeout=12.0).json()
        elif args.command == "dom":
            q = f"?tab_id={args.tab_id}" if args.tab_id else ""
            res = requests.get(f"{SERVER_URL}/api/dom{q}", timeout=10.0).json()
        elif args.command == "text":
            q = f"?tab_id={args.tab_id}" if args.tab_id else ""
            res = requests.get(f"{SERVER_URL}/api/text{q}", timeout=10.0).json()
        elif args.command == "links":
            q = f"?tab_id={args.tab_id}" if args.tab_id else ""
            res = requests.get(f"{SERVER_URL}/api/links{q}", timeout=10.0).json()
        elif args.command == "scroll":
            res = requests.post(f"{SERVER_URL}/api/scroll", json={"direction": args.direction, "amount": args.amount}, timeout=10.0).json()
        elif args.command == "select":
            res = requests.post(f"{SERVER_URL}/api/select", json={"selector": args.selector, "value": args.value, "text": args.text}, timeout=10.0).json()
        elif args.command == "click":
            payload = {"selector": args.selector, "text": args.text}
            res = requests.post(f"{SERVER_URL}/api/click", json=payload, timeout=10.0).json()
        elif args.command == "type":
            payload = {"selector": args.selector, "text": args.text or "", "enter": args.enter}
            res = requests.post(f"{SERVER_URL}/api/type", json=payload, timeout=10.0).json()
        elif args.command == "goto":
            payload = {"url": args.url}
            res = requests.post(f"{SERVER_URL}/api/goto", json=payload, timeout=10.0).json()
        elif args.command == "network":
            res = requests.get(f"{SERVER_URL}/api/network", timeout=10.0).json()
        else:
            res = {"status": "error", "message": f"Unknown command: {args.command}"}
    except Exception as e:
        res = {
            "status": "error",
            "message": f"Connection error: {e}",
            "hint": "Make sure bridge_server.py is running on http://127.0.0.1:8765"
        }

    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        if res.get("status") == "success":
            print(f"[SUCCESS] Action '{args.command}' completed on tab: {res.get('title', 'Unknown')}")
            if "url" in res:
                print(f"  URL: {res['url']}")
            if "screenshot_path" in res:
                print(f"  Screenshot saved to: {res['screenshot_path']} ({res.get('file_size_kb')} KB)")
            if "tabs" in res:
                print(f"  Total Tabs: {res.get('total_tabs', len(res['tabs']))}")
                for idx, t in enumerate(res["tabs"], 1):
                    act = "🟢 [ACTIVE]" if t.get("active") else "💤"
                    print(f"    {idx}. {act} {t['title']} ({t['url']})")
            if "text" in res:
                print(f"\n--- Clean Text Preview ({res.get('length')} chars) ---")
                print(res["text"][:600] + ("..." if len(res["text"]) > 600 else ""))
            if "links" in res:
                print(f"\n--- Links Extracted ({res.get('total_links')} links) ---")
                for l in res["links"][:8]:
                    print(f"    - {l['text']} -> {l['href']}")
            if "data" in res:
                headings = res["data"].get("headings", [])
                interactive = res["data"].get("interactive", [])
                print(f"  Headings ({len(headings)}):")
                for h in headings[:5]:
                    print(f"    - [{h['tag'].upper()}] {h['text']}")
                print(f"  Interactive Elements ({len(interactive)}):")
                for el in interactive[:8]:
                    info = f"[{el['tag'].upper()}] {el.get('text', '')}"
                    if el.get("id"):
                        info += f" (#{el['id']})"
                    print(f"    - {info}")
            if "requests_count" in res:
                print(f"  Recent Network Requests: {res['requests_count']}")
                for req in res.get("recent_requests", [])[:6]:
                    print(f"    - [{req.get('method', 'GET')}] {req.get('statusCode', '-')} {req.get('url', '')[:70]}")
        else:
            print(f"[ERROR] {res.get('message')}")
            if "hint" in res:
                print(f"  Hint: {res['hint']}")

if __name__ == "__main__":
    main()
