---
name: chrome-monitor
description: Monitor active Google Chrome tabs, capture screenshots, extract clean text & DOM, inspect all tabs silently, click, type, scroll, and manage tabs via Secure Local WebSocket Bridge (ws://127.0.0.1:8765). Built-in password protection and zero cloud telemetry.
---

# Chrome Monitor — Developer & Automation Suite & MCP Server

Enables Antigravity and Claude Code to monitor, inspect, and interact with the user's active Google Chrome browser in real time.

## 🛡️ Security & Privacy Guardrails
- **100% Localhost (`127.0.0.1`)**: Zero cloud telemetry, zero external network traffic.
- **Password Protection**: All `input[type="password"]` are strictly masked as `[PROTECTED_PASSWORD]`.
- **Zero Cookie/Auth Token Dumping**: No session tokens are ever harvested.

---

## 📡 Essential Network Metrics Captured (`chrome_network`)
The network inspector captures clean, non-noisy requests with the following essential keys:
- **`url`**: Full API / Request URL
- **`method`**: HTTP Method (`GET`, `POST`, `PUT`, `DELETE`)
- **`statusCode`**: HTTP Status Code (`200`, `304`, `404`, `500`)
- **`statusLine`**: Status line (`200 OK`)
- **`remoteIp`**: Remote server IP address (e.g. `20.15.156.71`)
- **`fromCache`**: Boolean (`true` if loaded from memory/disk cache)
- **`type`**: Request category (`xmlhttprequest`, `script`, `stylesheet`, `image`)
- **`initiator`**: Originating domain/document
- **`timeStamp`**: Epoch timestamp

---

## 🛠️ Complete MCP Tools (17 Tools)

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
| `chrome_dom()` | None | Extract structured DOM (Headings, buttons, inputs) |
| `chrome_text()` | None | Extract clean readable text for AI reading |
| `chrome_links()` | None | Extract hyperlinks |
| `chrome_click(text, selector)`| `text`, `selector` | Click element with SPA auto-wait & PointerEvents |
| `chrome_type(text, selector)` | `text`, `selector` | Type into input with React Controlled value setter |
| `chrome_scroll(direction)` | `direction`, `amount`| Scroll page |
| `chrome_select(selector, value)`| `selector`, `value`| Select dropdown option |
| `chrome_reload(hard)` | `hard: bool` | Reload tab |
| `chrome_network()` | None | Essential API & HTTP network logs with Remote IP |
