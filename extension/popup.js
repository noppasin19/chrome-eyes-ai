document.addEventListener("DOMContentLoaded", async () => {
  const statusEl = document.getElementById("status");
  const badgeEl = document.getElementById("badge");
  const tabTitleEl = document.getElementById("tabTitle");
  const tabUrlEl = document.getElementById("tabUrl");

  // Get active tab
  try {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tabs && tabs.length > 0) {
      const tab = tabs[0];
      tabTitleEl.innerText = tab.title || "ไม่มีชื่อหน้า";
      tabUrlEl.innerText = tab.url || "";
    }
  } catch (e) {
    tabTitleEl.innerText = "Active Tab";
  }

  // Check status
  statusEl.innerText = "พร้อมรับคำสั่งจาก AI (Standby)";
  statusEl.style.color = "#38bdf8";
});
