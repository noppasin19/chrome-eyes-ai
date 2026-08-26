#!/usr/bin/env python3
"""
Chrome Inspector & Interactive Controller Tool
Connects to a running Google Chrome instance via Chrome DevTools Protocol (CDP)
to capture screenshots, extract DOM, and perform interactive actions (click, type, navigate).
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
import requests
from playwright.async_api import async_playwright

DEFAULT_CDP_PORT = 9222

def get_cdp_url(port: int = DEFAULT_CDP_PORT) -> str:
    """Find active CDP URL trying IPv4, localhost, and IPv6."""
    candidates = [
        f"http://[::1]:{port}",
        f"http://127.0.0.1:{port}",
        f"http://localhost:{port}"
    ]
    for url in candidates:
        try:
            res = requests.get(f"{url}/json/version", timeout=1.0)
            if res.status_code == 200:
                return url
        except Exception:
            continue
    return f"http://localhost:{port}"

def is_chrome_running_with_cdp(port: int = DEFAULT_CDP_PORT) -> bool:
    """Check if Chrome is reachable on the given remote debugging port."""
    cdp_url = get_cdp_url(port)
    try:
        res = requests.get(f"{cdp_url}/json/version", timeout=1.0)
        return res.status_code == 200
    except Exception:
        return False

def get_open_tabs_info(port: int = DEFAULT_CDP_PORT) -> list:
    """Get list of active page tabs from Chrome CDP HTTP endpoint."""
    cdp_url = get_cdp_url(port)
    try:
        res = requests.get(f"{cdp_url}/json/list", timeout=1.0)
        if res.status_code == 200:
            tabs = res.json()
            return [t for t in tabs if t.get("type") == "page"]
    except Exception:
        pass
    return []

async def get_target_page(browser):
    """Get the active page tab, or create/find the most relevant one."""
    for context in browser.contexts:
        for page in context.pages:
            # Skip internal chrome:// and empty background pages if other pages exist
            if not page.url.startswith("chrome-extension://") and not page.url.startswith("devtools://"):
                return page

    # Fallback to any first page if available
    for context in browser.contexts:
        if context.pages:
            return context.pages[-1]

    # If no pages exist in context, create one
    if browser.contexts:
        return await browser.contexts[0].new_page()
    return None

async def capture_screenshot(cdp_url: str, output_path: str) -> dict:
    """Capture a screenshot of the active Chrome tab."""
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp(cdp_url)
        except Exception as e:
            return {"status": "error", "message": f"Could not connect to Chrome on {cdp_url}: {e}"}

        page = await get_target_page(browser)
        if not page:
            return {"status": "error", "message": "No tab found in Chrome."}

        title = await page.title()
        url = page.url

        abs_output_path = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(abs_output_path), exist_ok=True)

        await page.screenshot(path=abs_output_path, full_page=False)
        return {
            "status": "success",
            "action": "screenshot",
            "title": title,
            "url": url,
            "screenshot_path": abs_output_path
        }

async def extract_dom_summary(cdp_url: str) -> dict:
    """Extract page title, url, interactive elements, and headings from the active tab."""
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp(cdp_url)
        except Exception as e:
            return {"status": "error", "message": f"Could not connect to Chrome on {cdp_url}: {e}"}

        page = await get_target_page(browser)
        if not page:
            return {"status": "error", "message": "No tab found in Chrome."}

        title = await page.title()
        url = page.url

        dom_data = await page.evaluate('''() => {
            const headings = Array.from(document.querySelectorAll('h1, h2, h3')).map(h => ({
                tag: h.tagName.toLowerCase(),
                text: h.innerText.trim()
            })).filter(h => h.text.length > 0);

            const interactive = Array.from(document.querySelectorAll('button, a, input, textarea, select, [role="button"], [role="link"]')).map(el => {
                const text = (el.innerText || el.value || el.placeholder || el.getAttribute('aria-label') || el.getAttribute('title') || '').trim();
                return {
                    tag: el.tagName.toLowerCase(),
                    text: text.substring(0, 50),
                    id: el.id || undefined,
                    href: el.getAttribute('href') || undefined
                };
            }).filter(el => el.text.length > 0 || el.id).slice(0, 40);

            return { headings, interactive };
        }''')

        return {
            "status": "success",
            "action": "dom",
            "title": title,
            "url": url,
            "data": dom_data
        }

async def perform_click(cdp_url: str, selector: str = None, text: str = None) -> dict:
    """Click an element by CSS selector or by text content."""
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp(cdp_url)
        except Exception as e:
            return {"status": "error", "message": f"Could not connect to Chrome on {cdp_url}: {e}"}

        page = await get_target_page(browser)
        if not page:
            return {"status": "error", "message": "No active tab found in Chrome."}

        try:
            if selector:
                await page.click(selector, timeout=5000)
                target_desc = f"selector '{selector}'"
            elif text:
                # Find by text or role
                locator = page.get_by_text(text, exact=False).first
                await locator.click(timeout=5000)
                target_desc = f"text '{text}'"
            else:
                return {"status": "error", "message": "Either --selector or --text must be provided."}

            await page.wait_for_timeout(1000) # Give UI time to update
            return {
                "status": "success",
                "action": "click",
                "target": target_desc,
                "current_url": page.url,
                "current_title": await page.title()
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to click {selector or text}: {e}"}

async def perform_type(cdp_url: str, selector: str, text_to_type: str, press_enter: bool = False) -> dict:
    """Type text into an input element and optionally press Enter."""
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp(cdp_url)
        except Exception as e:
            return {"status": "error", "message": f"Could not connect to Chrome on {cdp_url}: {e}"}

        page = await get_target_page(browser)
        if not page:
            return {"status": "error", "message": "No active tab found in Chrome."}

        try:
            await page.fill(selector, text_to_type, timeout=5000)
            if press_enter:
                await page.press(selector, "Enter")
                await page.wait_for_timeout(1500)
            return {
                "status": "success",
                "action": "type",
                "selector": selector,
                "text": text_to_type,
                "pressed_enter": press_enter,
                "current_url": page.url,
                "current_title": await page.title()
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to type into {selector}: {e}"}

async def navigate_to(cdp_url: str, url: str) -> dict:
    """Navigate active tab to a new URL."""
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp(cdp_url)
        except Exception as e:
            return {"status": "error", "message": f"Could not connect to Chrome on {cdp_url}: {e}"}

        page = await get_target_page(browser)
        if not page:
            return {"status": "error", "message": "No active tab found in Chrome."}

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            return {
                "status": "success",
                "action": "goto",
                "url": page.url,
                "title": await page.title()
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to navigate to {url}: {e}"}

def main():
    parser = argparse.ArgumentParser(description="Chrome Inspector & Interactive Controller")
    parser.add_argument("command", choices=["check", "screenshot", "dom", "click", "type", "goto"],
                        help="Action to perform")
    parser.add_argument("--port", type=int, default=DEFAULT_CDP_PORT,
                        help=f"CDP Remote Debugging Port (default: {DEFAULT_CDP_PORT})")
    parser.add_argument("--output", type=str, default="current_tab.png",
                        help="Path to save screenshot (default: current_tab.png)")
    parser.add_argument("--selector", type=str, help="CSS Selector for click/type action")
    parser.add_argument("--text", type=str, help="Text to click or type")
    parser.add_argument("--enter", action="store_true", help="Press Enter after typing")
    parser.add_argument("--url", type=str, help="URL to navigate to")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()
    cdp_url = get_cdp_url(args.port)

    if args.command == "check":
        running = is_chrome_running_with_cdp(args.port)
        tabs = get_open_tabs_info(args.port) if running else []
        result = {"status": "success", "cdp_running": running, "port": args.port, "open_tabs_count": len(tabs), "tabs": tabs}
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            if running:
                print(f"[OK] Chrome CDP is active on port {args.port} (Found {len(tabs)} tabs)")
                for t in tabs:
                    print(f"  - {t.get('title')} ({t.get('url')})")
            else:
                print(f"[WARN] Chrome CDP is NOT responding on port {args.port}")
        return

    if not is_chrome_running_with_cdp(args.port):
        err = {
            "status": "error",
            "message": f"Chrome is not running with remote debugging on port {args.port}."
        }
        if args.json:
            print(json.dumps(err, indent=2, ensure_ascii=False))
        else:
            print(f"[ERROR] {err['message']}", file=sys.stderr)
        sys.exit(1)

    if args.command == "screenshot":
        res = asyncio.run(capture_screenshot(cdp_url, args.output))
    elif args.command == "dom":
        res = asyncio.run(extract_dom_summary(cdp_url))
    elif args.command == "click":
        res = asyncio.run(perform_click(cdp_url, selector=args.selector, text=args.text))
    elif args.command == "type":
        res = asyncio.run(perform_type(cdp_url, selector=args.selector, text_to_type=args.text, press_enter=args.enter))
    elif args.command == "goto":
        res = asyncio.run(navigate_to(cdp_url, url=args.url))

    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        if res.get("status") == "success":
            print(f"[SUCCESS] {res.get('action').upper()} completed.")
            if "title" in res:
                print(f"Title: {res.get('title')} ({res.get('url')})")
            if "screenshot_path" in res:
                print(f"Screenshot: {res.get('screenshot_path')}")
            if "data" in res:
                print(f"Data: {json.dumps(res.get('data'), indent=2, ensure_ascii=False)}")
        else:
            print(f"[ERROR] {res.get('message')}", file=sys.stderr)

if __name__ == "__main__":
    main()
