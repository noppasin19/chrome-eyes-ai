---
name: chrome-monitor
description: Monitor active Google Chrome tabs, capture screenshots, extract clean text & DOM, inspect all tabs silently, click (DOM & Canvas XY coordinates), drag & drop, type, and manage tabs via Secure Local WebSocket Bridge (ws://127.0.0.1:8765) with Hybrid DOM & Hardware CDP Engine. Built-in password protection and zero cloud telemetry.
---

# Chrome Eyes AI v2.1.0 — Enterprise Browser Automation & MCP Suite

Enables Antigravity, Claude Code, Claude Desktop, and Cursor to monitor, inspect, and interact with the user's active Google Chrome browser in real time.

## 🛡️ Security & Privacy Guardrails
- **100% Localhost (`127.0.0.1`)**: Zero cloud telemetry, zero external network traffic.
- **Password Protection**: All password inputs are strictly masked as `[PROTECTED_PASSWORD]`.
- **Zero Cookie/Auth Token Harvesting**: No session tokens are ever dumped.

---

## 🎯 Visual & Interaction Playbook for AI Agents

Follow this decision tree when interacting with web pages:

```
[Target to Click/Interact]
       │
       ├──► Standard HTML Web Page (GitHub, YouTube, Google, Dashboard)
       │       └──► Use chrome_click(text="...") or chrome_click(selector="...")
       │            (Fast & silent, auto-waits for SPA elements)
       │
       ├──► Canvas / Visual UI (Canva, Figma, Miro, Google Maps, Flutter Web, TradingView)
       │       └──► Step 1: chrome_screenshot()
       │            Step 2: Locate target X, Y coordinates
       │            Step 3: chrome_click_xy(x, y) (Hardware CDP click, isTrusted=True)
       │
       ├──► Drag & Drop / Reordering (Kanban, Trello, Jira, Canvas Objects)
       │       └──► Use chrome_drag(from_x, from_y, to_x, to_y)
       │
       └──► Overlay / Modal Blocking or Strict Anti-Bot Verification
               └──► Fallback to chrome_click_xy(x, y) or chrome_native_type(text="...")
```

---

## 🛠️ Complete MCP Tools (20 Tools)

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| `chrome_check()` | None | Connection & active tab status |
| `chrome_tabs()` | None | List all open tabs |
| `chrome_inspect_all()` | None | Background multi-tab inspection (0 tab switching) |
| `chrome_switch_tab(tab_id)` | `tab_id: int` | Focus specific tab |
| `chrome_new_tab(url)` | `url: str` | Open URL in new tab |
| `chrome_close_tab(tab_id)` | `tab_id: int` | Close specific tab |
| `chrome_goto(url)` | `url: str` | Navigate active tab |
| `chrome_screenshot(output_path)`| `output_path: str` | Capture screenshot |
| `chrome_dom(tab_id)` | `tab_id` | Extract structured DOM (Headings, buttons, inputs with X,Y) |
| `chrome_text(tab_id)` | `tab_id` | Extract clean readable text for AI reading |
| `chrome_links(tab_id)` | `tab_id` | Extract hyperlinks |
| `chrome_click(text, selector)`| `text`, `selector` | Click element with SPA auto-wait & PointerEvents |
| `chrome_click_xy(x, y)` | `x`, `y`, `click_count` | **[Hardware CDP]** Click exact coordinates on Canvas / Figma |
| `chrome_drag(from_x, from_y, to_x, to_y)` | `from_x`, `to_x`... | **[Hardware CDP]** Drag & drop trajectory for Kanban / Objects |
| `chrome_type(text, selector)` | `text`, `selector` | Type into input with React Controlled value setter |
| `chrome_native_type(text)` | `text` | **[Hardware CDP]** Type raw OS keystrokes for Canvas/Protected inputs |
| `chrome_scroll(direction)` | `direction`, `amount`| Scroll page |
| `chrome_select(selector, value)`| `selector`, `value`| Select dropdown option |
| `chrome_reload(hard)` | `hard: bool` | Reload tab |
| `chrome_network()` | None | Essential API & HTTP network logs with Remote IP |