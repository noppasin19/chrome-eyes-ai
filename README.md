# Chrome Eyes AI (chrome-eyes-ai) 🛰️👁️

> **The Intelligent Omniscient Eye for AI Agents in Google Chrome**  
> Real-time Google Chrome inspection, DOM extraction, network monitoring, and automation bridge for **Antigravity**, **Claude Code**, **Claude Desktop**, and **Cursor** via official **Model Context Protocol (MCP)**.

---

## 🌟 Key Features (v2.1.0 Enterprise Edition)
- **Hybrid DOM & Hardware CDP Engine**: Combines lightning-fast silent DOM automation with Chrome DevTools Protocol hardware inputs.
- **Canvas & Figma Support (`chrome_click_xy`)**: Click exact X, Y pixel coordinates on Canva, Figma, Miro, and Maps with `isTrusted=True`.
- **Drag & Drop Simulation (`chrome_drag`)**: Move Kanban cards, resize elements, and reorder objects with natural mouse trajectories.
- **100% Localhost & Private (`127.0.0.1`)**: Zero cloud telemetry, zero external network traffic.
- **Works on Everyday Chrome**: Inspects and controls your existing Chrome browser with all open tabs and logins (0 browser restarts needed).
- **20 Native MCP Tools**: First-class Model Context Protocol support with automatic tool auto-approval.
- **Silent Background Multi-Tab Inspection**: Reads and analyzes all tabs in parallel with 0 tab switching.
- **Privacy First (Password Protection)**: All `input[type="password"]` fields are masked as `[PROTECTED_PASSWORD]`.
- **SPA Intelligent Retry Polling**: Automatically waits for dynamic web elements to render before clicking or typing.
- **Clean Network Inspector**: Captures essential API metrics (Method, Status, Remote IP, Timing, Initiator).

---

## 🔌 Model Context Protocol (MCP) Setup

### For Antigravity & Claude Code (Workspace Config):
```json
{
  "mcpServers": {
    "chrome-monitor": {
      "command": "/Users/nop/AI/multi_agents/chrome-eyes-ai/.venv/bin/python",
      "args": [
        "/Users/nop/AI/multi_agents/chrome-eyes-ai/.agents/skills/chrome-monitor/scripts/mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/Users/nop/AI/multi_agents/chrome-eyes-ai"
      }
    }
  }
}
```

---

## 🛠️ List of Available MCP Tools (20 Tools)

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| `chrome_check()` | None | Check connection & active tab status |
| `chrome_tabs()` | None | List all open tabs (Title, URL, ID, Active status) |
| `chrome_inspect_all()` | None | Inspect all open tabs silently in background (0 tab switches) |
| `chrome_switch_tab(tab_id)` | `tab_id: int` | Switch/focus a specific tab |
| `chrome_new_tab(url)` | `url: str` | Open a URL in a new tab |
| `chrome_close_tab(tab_id)` | `tab_id: int` | Close a specific tab |
| `chrome_goto(url)` | `url: str` | Navigate active tab to a new URL |
| `chrome_screenshot(output_path, tab_id)` | `output_path: str` | Capture screenshot of tab |
| `chrome_dom(tab_id)` | None | Extract structured DOM (Headings, buttons, inputs with X,Y) |
| `chrome_text(tab_id)` | None | Extract clean readable text for AI summarization |
| `chrome_links(tab_id)` | None | Extract all hyperlinks |
| `chrome_click(text, selector)` | `text`, `selector` | Click element with SPA auto-wait & PointerEvents |
| `chrome_click_xy(x, y)` | `x`, `y` | **[Hardware CDP]** Click exact coordinates on Canvas / Figma |
| `chrome_drag(from_x, from_y, to_x, to_y)` | `from_x`... | **[Hardware CDP]** Drag & drop trajectory for Kanban / Objects |
| `chrome_type(text, selector, enter)` | `text`, `selector` | Type into input with React Controlled value setter |
| `chrome_native_type(text)` | `text` | **[Hardware CDP]** Type raw OS keystrokes for Canvas/Protected inputs |
| `chrome_scroll(direction, amount)` | `direction`, `amount` | Scroll page (down, up, top, bottom) |
| `chrome_select(selector, value, text)` | `selector`, `value` | Select dropdown option |
| `chrome_reload(hard)` | `hard: bool` | Reload active tab |
| `chrome_network()` | None | Essential HTTP requests and API calls with Remote IP |

---

## 🚀 Getting Started

1. **Install Extension in Chrome**:
   - Go to `chrome://extensions`
   - Enable **Developer mode**
   - Click **Load unpacked** and select the `/Users/nop/AI/multi_agents/chrome-eyes-ai/extension/` folder.

2. **Install Python Dependencies**:
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

3. **Start Coding**:
   Your AI assistant (Antigravity / Claude) can now directly inspect, read, and control your browser!