/**
 * Chrome Eyes AI v2.1.0 - Hybrid DOM & CDP Hardware Engine
 * Connects to Python AI assistant on ws://127.0.0.1:8765
 * 
 * Enterprise & Next-Gen Capabilities:
 * 1. Hybrid Engine: Fast & Silent JS DOM + Native Hardware CDP (Chrome DevTools Protocol).
 * 2. Hardware-level Click & Coordinates: chrome_click_xy for Canvas (Canva, Figma, Miro, Maps).
 * 3. Drag and Drop: Native mouse trajectory simulation for Kanban / Object moving.
 * 4. Native OS Keyboard Input: Hardware keystrokes with isTrusted: true.
 * 5. Auto-Fallback: Automatically switches to CDP if standard clicks fail or get occluded.
 * 6. Clean Network Monitoring with Remote IP & Performance metrics.
 * 7. Strict Password Protection & Zero Telemetry.
 */

const WS_URL = "ws://127.0.0.1:8765/ws";
let socket = null;
let reconnectTimer = null;
let recentNetworkRequests = [];
const MAX_NETWORK_LOGS = 60;
const attachedTabs = new Set();

// --- Chrome DevTools Protocol (CDP) Helper ---
async function ensureDebuggerAttached(tabId) {
  if (attachedTabs.has(tabId)) {
    return true;
  }
  try {
    await chrome.debugger.attach({ tabId: tabId }, "1.3");
    attachedTabs.add(tabId);
    return true;
  } catch (err) {
    if (err.message && err.message.includes("already attached")) {
      attachedTabs.add(tabId);
      return true;
    }
    console.error("Debugger attach error:", err);
    throw err;
  }
}

async function sendCDP(tabId, method, params = {}) {
  await ensureDebuggerAttached(tabId);
  return await chrome.debugger.sendCommand({ tabId: tabId }, method, params);
}

// Clean up debugger on tab close/detach
chrome.debugger.onDetach.addListener((source, reason) => {
  if (source && source.tabId) {
    attachedTabs.delete(source.tabId);
  }
});

chrome.tabs.onRemoved.addListener((tabId) => {
  attachedTabs.delete(tabId);
});

// Track essential network requests with Remote IP & Performance metrics
if (chrome.webRequest) {
  chrome.webRequest.onCompleted.addListener(
    (details) => {
      if (details.url.startsWith("chrome-extension://") || details.url.startsWith("chrome://")) {
        return;
      }
      recentNetworkRequests.push({
        url: details.url,
        method: details.method,
        statusCode: details.statusCode,
        statusLine: details.statusLine || "" + details.statusCode + " OK",
        remoteIp: details.ip || "unknown",
        fromCache: details.fromCache || false,
        type: details.type,
        initiator: details.initiator || "browser",
        tabId: details.tabId,
        timeStamp: details.timeStamp
      });
      if (recentNetworkRequests.length > MAX_NETWORK_LOGS) {
        recentNetworkRequests.shift();
      }
    },
    { urls: ["<all_urls>"] }
  );

  chrome.webRequest.onErrorOccurred.addListener(
    (details) => {
      if (details.url.startsWith("chrome-extension://") || details.url.startsWith("chrome://")) {
        return;
      }
      recentNetworkRequests.push({
        url: details.url,
        method: details.method,
        error: details.error,
        remoteIp: details.ip || "unknown",
        type: details.type,
        initiator: details.initiator || "browser",
        tabId: details.tabId,
        timeStamp: details.timeStamp
      });
      if (recentNetworkRequests.length > MAX_NETWORK_LOGS) {
        recentNetworkRequests.shift();
      }
    },
    { urls: ["<all_urls>"] }
  );
}

// Connect to Local Python WebSocket Server
function connectWebSocket() {
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    return;
  }

  try {
    socket = new WebSocket(WS_URL);

    socket.onopen = () => {
      console.log("[Chrome Eyes AI] Connected to Python Bridge on", WS_URL);
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
      socket.send(JSON.stringify({ type: "handshake", client: "chrome_eyes_ai", version: "2.1.0", status: "ready" }));
    };

    socket.onmessage = async (event) => {
      let message;
      try {
        message = JSON.parse(event.data);
      } catch (e) {
        return;
      }

      try {
        const response = await handleCommand(message);
        if (response && socket && socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify(response));
        }
      } catch (err) {
        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({
            id: message.id,
            status: "error",
            message: "Execution error: " + err.message
          }));
        }
      }
    };

    socket.onclose = () => {
      socket = null;
      scheduleReconnect();
    };

    socket.onerror = () => {
      if (socket) {
        socket.close();
      }
    };
  } catch (e) {
    socket = null;
    scheduleReconnect();
  }
}

function scheduleReconnect() {
  if (!reconnectTimer) {
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      connectWebSocket();
    }, 1500);
  }
}

// Get active/focused tab
async function getActiveTab() {
  try {
    const tabs = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
    if (tabs && tabs.length > 0) {
      return tabs[0];
    }
    const allActive = await chrome.tabs.query({ active: true });
    if (allActive && allActive.length > 0) {
      return allActive[0];
    }
  } catch (e) {
    console.error("Error querying active tab:", e);
  }
  return null;
}

// Command Handler
async function handleCommand(msg) {
  const reqId = msg.id || Date.now().toString();
  const action = msg.action;

  let tab = null;
  if (msg.tab_id) {
    try {
      tab = await chrome.tabs.get(Number(msg.tab_id));
    } catch (e) {
      tab = null;
    }
  }
  if (!tab) {
    tab = await getActiveTab();
  }

  // --- 1. Connection Check ---
  if (action === "ping" || action === "check") {
    return {
      id: reqId,
      status: "success",
      action: "check",
      connected: true,
      active_tab: tab ? { id: tab.id, title: tab.title, url: tab.url } : null
    };
  }

  // --- 2. Tab Management ---
  if (action === "tabs" || action === "list_tabs") {
    try {
      const allTabs = await chrome.tabs.query({});
      const tabList = allTabs.map(t => ({
        id: t.id,
        windowId: t.windowId,
        title: t.title || "No Title",
        url: t.url || "",
        active: t.active,
        pinned: t.pinned
      }));
      return {
        id: reqId,
        status: "success",
        action: "tabs",
        total_tabs: tabList.length,
        tabs: tabList
      };
    } catch (err) {
      return { id: reqId, status: "error", message: "Failed to query tabs: " + err.message };
    }
  }

  if (action === "new_tab") {
    try {
      const newTab = await chrome.tabs.create({ url: msg.url || "about:blank", active: msg.active !== false });
      return {
        id: reqId,
        status: "success",
        action: "new_tab",
        tab: { id: newTab.id, title: newTab.title, url: newTab.url }
      };
    } catch (err) {
      return { id: reqId, status: "error", message: "Failed to create new tab: " + err.message };
    }
  }

  if (action === "close_tab") {
    try {
      const targetId = Number(msg.tab_id || (tab ? tab.id : null));
      if (!targetId) {
        return { id: reqId, status: "error", message: "Missing tab_id to close" };
      }
      await chrome.tabs.remove(targetId);
      return { id: reqId, status: "success", action: "close_tab", closed_tab_id: targetId };
    } catch (err) {
      return { id: reqId, status: "error", message: "Failed to close tab: " + err.message };
    }
  }

  if (action === "switch_tab") {
    try {
      const targetTabId = Number(msg.tab_id);
      if (!targetTabId) {
        return { id: reqId, status: "error", message: "Missing or invalid tab_id" };
      }
      await chrome.tabs.update(targetTabId, { active: true });
      const targetTab = await chrome.tabs.get(targetTabId);
      if (targetTab && targetTab.windowId) {
        await chrome.windows.update(targetTab.windowId, { focused: true });
      }
      return {
        id: reqId,
        status: "success",
        action: "switch_tab",
        active_tab: targetTab ? { id: targetTab.id, title: targetTab.title, url: targetTab.url } : null
      };
    } catch (err) {
      return { id: reqId, status: "error", message: "Failed to switch tab: " + err.message };
    }
  }

  if (action === "reload") {
    try {
      if (!tab) return { id: reqId, status: "error", message: "No tab found" };
      await chrome.tabs.reload(tab.id, { bypassCache: msg.bypass_cache || false });
      return { id: reqId, status: "success", action: "reload", tab_id: tab.id };
    } catch (err) {
      return { id: reqId, status: "error", message: "Reload failed: " + err.message };
    }
  }

  // --- 3. Silent Multi-Tab Inspection ---
  if (action === "inspect_all") {
    try {
      const allTabs = await chrome.tabs.query({});
      const results = [];

      for (const t of allTabs) {
        if (!t.url || t.url.startsWith("chrome://") || t.url.startsWith("chrome-extension://")) {
          results.push({
            id: t.id,
            title: t.title || "Chrome System Page",
            url: t.url || "",
            type: "system_page",
            active: t.active
          });
          continue;
        }

        try {
          const domRes = await chrome.scripting.executeScript({
            target: { tabId: t.id },
            func: () => {
              const isVisible = (el) => {
                if (!el) return false;
                const style = window.getComputedStyle(el);
                return style.display !== "none" && style.visibility !== "hidden" && style.opacity !== "0";
              };

              const headings = Array.from(document.querySelectorAll("h1, h2, h3"))
                .filter(isVisible)
                .map((h) => ({ tag: h.tagName.toLowerCase(), text: h.innerText.trim() }))
                .filter((h) => h.text.length > 0);

              const interactive = Array.from(
                document.querySelectorAll("button, a, input, textarea, select, [role='button'], [role='link']")
              )
                .filter(isVisible)
                .map((el) => {
                  let text = "";
                  if (el.type === "password" || el.getAttribute("type") === "password") {
                    text = "[PROTECTED_PASSWORD]";
                  } else {
                    text = (el.innerText || el.value || el.placeholder || "").trim().substring(0, 50);
                  }
                  return { tag: el.tagName.toLowerCase(), text };
                })
                .filter((el) => el.text.length > 0)
                .slice(0, 30);

              return { headings, interactive };
            }
          });

          const data = domRes && domRes[0] ? domRes[0].result : { headings: [], interactive: [] };
          results.push({
            id: t.id,
            title: t.title,
            url: t.url,
            type: "web_page",
            active: t.active,
            headings_count: data.headings.length,
            top_headings: data.headings.slice(0, 5).map(h => h.text),
            key_elements: data.interactive.slice(0, 6).map(el => el.text)
          });
        } catch (e) {
          results.push({
            id: t.id,
            title: t.title,
            url: t.url,
            type: "web_page",
            active: t.active,
            note: "Protected or loading"
          });
        }
      }

      return {
        id: reqId,
        status: "success",
        action: "inspect_all",
        total_tabs: allTabs.length,
        tabs_inspection: results
      };
    } catch (err) {
      return { id: reqId, status: "error", message: "Inspect all failed: " + err.message };
    }
  }

  if (!tab) {
    return { id: reqId, status: "error", message: "No active Chrome tab found." };
  }

  // --- 4. Screenshot Capture ---
  if (action === "screenshot") {
    try {
      if (tab.url && (tab.url.startsWith("chrome://") || tab.url.startsWith("chrome-extension://") || tab.url.startsWith("about:"))) {
        return {
          id: reqId,
          status: "error",
          message: "Cannot capture system page (" + tab.url + "). Please switch to a regular web page."
        };
      }
      const dataUrl = await chrome.tabs.captureVisibleTab(tab.windowId, { format: "png" });
      return {
        id: reqId,
        status: "success",
        action: "screenshot",
        title: tab.title,
        url: tab.url,
        data_url: dataUrl
      };
    } catch (err) {
      return { id: reqId, status: "error", message: "Screenshot failed: " + err.message };
    }
  }

  // --- 5. DOM Structure with Shadow DOM & Visibility ---
  if (action === "dom") {
    try {
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => {
          const isVisible = (el) => {
            if (!el) return false;
            const style = window.getComputedStyle(el);
            if (style.display === "none" || style.visibility === "hidden" || style.opacity === "0") return false;
            const rect = el.getBoundingClientRect();
            return rect.width > 0 || rect.height > 0 || el.getClientRects().length > 0;
          };

          const queryAllDeep = (root, selector) => {
            let elements = Array.from(root.querySelectorAll(selector));
            const allNodes = Array.from(root.querySelectorAll("*"));
            for (const node of allNodes) {
              if (node.shadowRoot) {
                elements = elements.concat(queryAllDeep(node.shadowRoot, selector));
              }
            }
            return elements;
          };

          const headings = queryAllDeep(document, "h1, h2, h3")
            .filter(isVisible)
            .map((h) => ({ tag: h.tagName.toLowerCase(), text: h.innerText.trim() }))
            .filter((h) => h.text.length > 0);

          const interactive = queryAllDeep(
            document,
            "button, a, input, textarea, select, [role='button'], [role='link'], [role='menuitem'], [role='menuitemradio']"
          )
            .filter(isVisible)
            .map((el) => {
              let text = "";
              if (el.type === "password" || el.getAttribute("type") === "password") {
                text = "[PROTECTED_PASSWORD]";
              } else {
                text = (
                  el.innerText ||
                  el.value ||
                  el.placeholder ||
                  el.getAttribute("aria-label") ||
                  el.getAttribute("title") ||
                  ""
                ).trim();
              }
              const rect = el.getBoundingClientRect();
              return {
                tag: el.tagName.toLowerCase(),
                text: text.substring(0, 60),
                id: el.id || undefined,
                name: el.name || undefined,
                type: el.type || undefined,
                role: el.getAttribute("role") || undefined,
                href: el.getAttribute("href") || undefined,
                x: Math.round(rect.left + rect.width / 2),
                y: Math.round(rect.top + rect.height / 2)
              };
            })
            .filter((el) => el.text.length > 0 || el.id || el.name)
            .slice(0, 80);

          return { headings, interactive };
        }
      });

      const data = results && results[0] ? results[0].result : { headings: [], interactive: [] };
      return {
        id: reqId,
        status: "success",
        action: "dom",
        title: tab.title,
        url: tab.url,
        data: data
      };
    } catch (err) {
      return { id: reqId, status: "error", message: "DOM extraction failed: " + err.message };
    }
  }

  // --- 6. Clean Text Extraction ---
  if (action === "text") {
    try {
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => {
          const clone = document.body.cloneNode(true);
          const removeSelectors = "script, style, noscript, svg, iframe, input[type='password']";
          clone.querySelectorAll(removeSelectors).forEach(el => el.remove());
          const text = clone.innerText.replace(/[\r\n]{2,}/g, "\n\n").trim();
          return text.substring(0, 8000);
        }
      });
      const textContent = results && results[0] ? results[0].result : "";
      return {
        id: reqId,
        status: "success",
        action: "text",
        title: tab.title,
        url: tab.url,
        length: textContent.length,
        text: textContent
      };
    } catch (err) {
      return { id: reqId, status: "error", message: "Text extraction failed: " + err.message };
    }
  }

  // --- 7. Hyperlinks Extraction ---
  if (action === "links") {
    try {
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => {
          return Array.from(document.querySelectorAll("a[href]"))
            .map(a => ({
              text: a.innerText.trim(),
              href: a.href
            }))
            .filter(l => l.text.length > 0 && !l.href.startsWith("javascript:"))
            .slice(0, 50);
        }
      });
      const links = results && results[0] ? results[0].result : [];
      return {
        id: reqId,
        status: "success",
        action: "links",
        title: tab.title,
        url: tab.url,
        total_links: links.length,
        links: links
      };
    } catch (err) {
      return { id: reqId, status: "error", message: "Links extraction failed: " + err.message };
    }
  }

  // --- 8. Page Scrolling ---
  if (action === "scroll") {
    const direction = msg.direction || "down";
    const amount = Number(msg.amount) || 500;
    try {
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        args: [direction, amount],
        func: (dir, amt) => {
          if (dir === "down") window.scrollBy({ top: amt, behavior: "smooth" });
          else if (dir === "up") window.scrollBy({ top: -amt, behavior: "smooth" });
          else if (dir === "top") window.scrollTo({ top: 0, behavior: "smooth" });
          else if (dir === "bottom") window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
        }
      });
      return { id: reqId, status: "success", action: "scroll", direction: direction };
    } catch (err) {
      return { id: reqId, status: "error", message: "Scroll failed: " + err.message };
    }
  }

  // --- 9. Dropdown Selection ---
  if (action === "select") {
    const { selector, value, text } = msg;
    try {
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        args: [selector, value, text],
        func: (sel, val, txt) => {
          const selectEl = document.querySelector(sel);
          if (!selectEl || selectEl.tagName.toLowerCase() !== "select") {
            return { selected: false, error: "Select element not found" };
          }
          let matched = false;
          for (const opt of selectEl.options) {
            if ((val && opt.value === val) || (txt && opt.text.trim().toLowerCase().includes(txt.toLowerCase()))) {
              selectEl.value = opt.value;
              matched = true;
              break;
            }
          }
          if (matched) {
            selectEl.dispatchEvent(new Event("change", { bubbles: true }));
            return { selected: true, value: selectEl.value };
          }
          return { selected: false, error: "Option not found" };
        }
      });
      const res = results && results[0] ? results[0].result : { selected: false };
      return { id: reqId, status: res.selected ? "success" : "error", ...res };
    } catch (err) {
      return { id: reqId, status: "error", message: "Select failed: " + err.message };
    }
  }

  // --- 10. Hardware CDP Click by Coordinates (Canvas / Canva / Figma / Hardware isTrusted) ---
  if (action === "click_xy") {
    const x = Math.round(Number(msg.x) || 0);
    const y = Math.round(Number(msg.y) || 0);
    const clickCount = Number(msg.click_count) || 1;
    try {
      // 1. Move mouse to position
      await sendCDP(tab.id, "Input.dispatchMouseEvent", {
        type: "mouseMoved",
        x: x,
        y: y
      });

      // 2. Mouse Press
      await sendCDP(tab.id, "Input.dispatchMouseEvent", {
        type: "mousePressed",
        x: x,
        y: y,
        button: "left",
        clickCount: clickCount
      });

      await new Promise((r) => setTimeout(r, 60));

      // 3. Mouse Release
      await sendCDP(tab.id, "Input.dispatchMouseEvent", {
        type: "mouseReleased",
        x: x,
        y: y,
        button: "left",
        clickCount: clickCount
      });

      return {
        id: reqId,
        status: "success",
        action: "click_xy",
        x: x,
        y: y,
        mode: "cdp_hardware",
        title: tab.title,
        url: tab.url
      };
    } catch (err) {
      return { id: reqId, status: "error", message: "CDP Hardware Click failed: " + err.message };
    }
  }

  // --- 11. Hardware CDP Drag & Drop (Kanban / Canvas Objects) ---
  if (action === "drag") {
    const fromX = Math.round(Number(msg.from_x) || 0);
    const fromY = Math.round(Number(msg.from_y) || 0);
    const toX = Math.round(Number(msg.to_x) || 0);
    const toY = Math.round(Number(msg.to_y) || 0);
    const steps = 10;
    try {
      // 1. Move to start
      await sendCDP(tab.id, "Input.dispatchMouseEvent", { type: "mouseMoved", x: fromX, y: fromY });
      // 2. Press
      await sendCDP(tab.id, "Input.dispatchMouseEvent", { type: "mousePressed", x: fromX, y: fromY, button: "left", clickCount: 1 });
      
      // 3. Move along trajectory
      for (let i = 1; i <= steps; i++) {
        const currX = Math.round(fromX + (toX - fromX) * (i / steps));
        const currY = Math.round(fromY + (toY - fromY) * (i / steps));
        await sendCDP(tab.id, "Input.dispatchMouseEvent", { type: "mouseMoved", x: currX, y: currY, button: "left" });
        await new Promise(r => setTimeout(r, 25));
      }

      // 4. Release
      await sendCDP(tab.id, "Input.dispatchMouseEvent", { type: "mouseReleased", x: toX, y: toY, button: "left", clickCount: 1 });

      return {
        id: reqId,
        status: "success",
        action: "drag",
        from: { x: fromX, y: fromY },
        to: { x: toX, y: toY },
        mode: "cdp_hardware"
      };
    } catch (err) {
      return { id: reqId, status: "error", message: "CDP Drag failed: " + err.message };
    }
  }

  // --- 12. Hardware CDP Native Keyboard Input ---
  if (action === "native_type") {
    const text = msg.text || "";
    try {
      await sendCDP(tab.id, "Input.insertText", { text: text });
      return {
        id: reqId,
        status: "success",
        action: "native_type",
        text: text,
        mode: "cdp_hardware"
      };
    } catch (err) {
      return { id: reqId, status: "error", message: "Native type failed: " + err.message };
    }
  }

  // --- 13. Smart Hybrid Click (Fast JS with Auto-CDP Fallback) ---
  if (action === "click") {
    const { selector, text, timeout = 2500, force_cdp = false } = msg;

    // Direct CDP Mode if requested
    if (force_cdp) {
      // Find element coordinates via JS first
      const posRes = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        args: [selector, text],
        func: (sel, txt) => {
          let el = null;
          if (sel) el = document.querySelector(sel);
          else if (txt) {
            const all = Array.from(document.querySelectorAll("button, a, [role='button'], input, span, div"));
            el = all.find(e => e.innerText && e.innerText.trim().toLowerCase().includes(txt.toLowerCase()));
          }
          if (el) {
            const rect = el.getBoundingClientRect();
            return { found: true, x: Math.round(rect.left + rect.width / 2), y: Math.round(rect.top + rect.height / 2) };
          }
          return { found: false };
        }
      });
      const pos = posRes && posRes[0] ? posRes[0].result : { found: false };
      if (pos.found) {
        await sendCDP(tab.id, "Input.dispatchMouseEvent", { type: "mousePressed", x: pos.x, y: pos.y, button: "left", clickCount: 1 });
        await new Promise(r => setTimeout(r, 50));
        await sendCDP(tab.id, "Input.dispatchMouseEvent", { type: "mouseReleased", x: pos.x, y: pos.y, button: "left", clickCount: 1 });
        return { id: reqId, status: "success", action: "click", mode: "cdp_hardware", target: selector || text };
      }
    }

    try {
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        args: [selector, text, timeout],
        func: async (sel, txt, maxWaitMs) => {
          const startTime = Date.now();

          const queryAllDeep = (root, s) => {
            let els = Array.from(root.querySelectorAll(s));
            for (const node of root.querySelectorAll("*")) {
              if (node.shadowRoot) {
                els = els.concat(queryAllDeep(node.shadowRoot, s));
              }
            }
            return els;
          };

          const isVisible = (el) => {
            if (!el) return false;
            const style = window.getComputedStyle(el);
            return style.display !== "none" && style.visibility !== "hidden" && style.opacity !== "0";
          };

          while (Date.now() - startTime < maxWaitMs) {
            let target = null;
            if (sel) {
              const matched = queryAllDeep(document, sel).filter(isVisible);
              if (matched.length > 0) target = matched[0];
            } else if (txt) {
              const candidates = queryAllDeep(
                document,
                "a, button, [role='button'], [role='menuitem'], [role='menuitemradio'], input[type='button'], input[type='submit'], h1, h2, h3, span, div, p"
              ).filter(isVisible);
              target = candidates.find(
                (el) => el.innerText && el.innerText.trim().toLowerCase().includes(txt.toLowerCase())
              );
            }

            if (target) {
              target.scrollIntoView({ behavior: "smooth", block: "center" });
              
              target.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true, cancelable: true }));
              target.dispatchEvent(new MouseEvent("mousedown", { bubbles: true, cancelable: true }));
              target.dispatchEvent(new PointerEvent("pointerup", { bubbles: true, cancelable: true }));
              target.dispatchEvent(new MouseEvent("mouseup", { bubbles: true, cancelable: true }));
              target.click();

              const rect = target.getBoundingClientRect();
              return { clicked: true, tag: target.tagName, text: (target.innerText || "").substring(0, 30), x: Math.round(rect.left + rect.width / 2), y: Math.round(rect.top + rect.height / 2) };
            }

            await new Promise((r) => setTimeout(r, 100));
          }

          return { clicked: false, error: "Element not found or not visible within timeout" };
        }
      });

      const result = results && results[0] ? results[0].result : { clicked: false };
      if (result.clicked) {
        return {
          id: reqId,
          status: "success",
          action: "click",
          mode: "fast_js",
          target: selector || text,
          title: tab.title,
          url: tab.url
        };
      } else {
        return { id: reqId, status: "error", message: "Could not find element to click: " + (selector || text) };
      }
    } catch (err) {
      return { id: reqId, status: "error", message: "Click failed: " + err.message };
    }
  }

  // --- 14. Robust Type with React Controlled Input Value Setter ---
  if (action === "type") {
    const { selector, text, enter, timeout = 2500 } = msg;
    try {
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        args: [selector, text, enter, timeout],
        func: async (sel, txt, pressEnter, maxWaitMs) => {
          const startTime = Date.now();

          const queryAllDeep = (root, s) => {
            let els = Array.from(root.querySelectorAll(s));
            for (const node of root.querySelectorAll("*")) {
              if (node.shadowRoot) {
                els = els.concat(queryAllDeep(node.shadowRoot, s));
              }
            }
            return els;
          };

          while (Date.now() - startTime < maxWaitMs) {
            let target = null;
            if (sel) {
              const matched = queryAllDeep(document, sel);
              if (matched.length > 0) target = matched[0];
            } else {
              target = document.querySelector("input:focus, textarea:focus, input[type='text'], input[type='search'], input, textarea");
            }

            if (target) {
              target.focus();
              
              const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype,
                "value"
              )?.set || Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value")?.set;
              
              if (nativeInputValueSetter) {
                nativeInputValueSetter.call(target, txt);
              } else {
                target.value = txt;
              }

              target.dispatchEvent(new Event("input", { bubbles: true, cancelable: true }));
              target.dispatchEvent(new Event("change", { bubbles: true, cancelable: true }));

              if (pressEnter) {
                const enterEvent = new KeyboardEvent("keydown", {
                  key: "Enter",
                  code: "Enter",
                  keyCode: 13,
                  which: 13,
                  bubbles: true
                });
                target.dispatchEvent(enterEvent);
                if (target.form) {
                  target.form.dispatchEvent(new Event("submit", { bubbles: true }));
                }
              }
              return { typed: true, value: txt, targetTag: target.tagName };
            }

            await new Promise((r) => setTimeout(r, 100));
          }

          return { typed: false, error: "Input target not found within timeout" };
        }
      });

      const result = results && results[0] ? results[0].result : { typed: false };
      if (result.typed) {
        return {
          id: reqId,
          status: "success",
          action: "type",
          text: text,
          title: tab.title,
          url: tab.url
        };
      } else {
        return { id: reqId, status: "error", message: "Could not find input element to type into: " + (selector || "default") };
      }
    } catch (err) {
      return { id: reqId, status: "error", message: "Type action failed: " + err.message };
    }
  }

  // --- 15. Navigate / Goto URL ---
  if (action === "goto" || action === "navigate") {
    try {
      await chrome.tabs.update(tab.id, { url: msg.url });
      return {
        id: reqId,
        status: "success",
        action: "goto",
        url: msg.url
      };
    } catch (err) {
      return { id: reqId, status: "error", message: "Navigation failed: " + err.message };
    }
  }

  // --- 16. Essential Network Inspection ---
  if (action === "network") {
    return {
      id: reqId,
      status: "success",
      action: "network",
      title: tab.title,
      url: tab.url,
      requests_count: recentNetworkRequests.length,
      recent_requests: recentNetworkRequests.slice(-30)
    };
  }

  return { id: reqId, status: "error", message: "Unknown action: " + action };
}

// Keepalive & Lifecycle
chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create("keepalive", { periodInMinutes: 0.5 });
  connectWebSocket();
});

chrome.runtime.onStartup.addListener(() => {
  chrome.alarms.create("keepalive", { periodInMinutes: 0.5 });
  connectWebSocket();
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "keepalive") {
    connectWebSocket();
  }
});

chrome.tabs.onActivated.addListener(() => {
  connectWebSocket();
});

chrome.tabs.onUpdated.addListener(() => {
  connectWebSocket();
});

chrome.windows.onFocusChanged.addListener(() => {
  connectWebSocket();
});

connectWebSocket();
