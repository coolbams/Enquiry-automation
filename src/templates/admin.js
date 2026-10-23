document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const statTotal = document.getElementById("stat-total");
  const statSent = document.getElementById("stat-sent");
  const statFailed = document.getElementById("stat-failed");
  const statBots = document.getElementById("stat-bots");

  const tabEnquiries = document.getElementById("tab-enquiries");
  const tabBots = document.getElementById("tab-bots");
  const panelEnquiries = document.getElementById("panel-enquiries");
  const panelBots = document.getElementById("panel-bots");

  const enquiriesTbody = document.getElementById("enquiries-tbody");
  const botsTbody = document.getElementById("bots-tbody");
  const enquiriesCount = document.getElementById("enquiries-count");
  const botsCount = document.getElementById("bots-count");
  const refreshBtn = document.getElementById("refresh-btn");
  const logoutBtn = document.getElementById("logout-btn");

  // Logout
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      try {
        await fetch("/api/admin/logout", { method: "POST" });
      } finally {
        window.location.href = "/login";
      }
    });
  }

  // Tab Switching
  tabEnquiries.addEventListener("click", () => {
    tabEnquiries.classList.add("active");
    tabBots.classList.remove("active");
    panelEnquiries.style.display = "block";
    panelBots.style.display = "none";
  });

  tabBots.addEventListener("click", () => {
    tabBots.classList.add("active");
    tabEnquiries.classList.remove("active");
    panelBots.style.display = "block";
    panelEnquiries.style.display = "none";
  });

  refreshBtn.addEventListener("click", () => {
    loadAllData();
  });

  // Helpers
  function formatDate(isoString) {
    if (!isoString) return "-";
    const d = new Date(isoString);
    return d.toISOString().replace("T", " ").substring(0, 19);
  }

  function getStatusBadge(status) {
    const s = status || "received";
    return `<span class="badge ${s}">${s}</span>`;
  }

  // Fetch Stats
  async function loadStats() {
    try {
      const res = await fetch("/api/admin/stats");
      if (!res.ok) throw new Error("Unauthorized or server error");
      const data = await res.json();
      statTotal.textContent = data.total_enquiries;
      statSent.textContent = data.emails_sent;
      statFailed.textContent = data.emails_failed;
      statBots.textContent = data.bots_blocked;
    } catch (err) {
      console.error("Failed to load stats:", err);
    }
  }

  // Fetch Enquiries
  async function loadEnquiries() {
    try {
      const res = await fetch("/api/admin/enquiries");
      if (!res.ok) throw new Error("Failed to load enquiries");
      const enquiries = await res.json();

      enquiriesCount.textContent = `${enquiries.length} records`;

      if (enquiries.length === 0) {
        enquiriesTbody.innerHTML = `<tr><td colspan="4" class="empty-state">// no enquiries recorded yet</td></tr>`;
        return;
      }

      enquiriesTbody.innerHTML = enquiries.map((item, idx) => {
        const latestLog = item.logs && item.logs.length > 0 ? item.logs[item.logs.length - 1] : null;
        const status = latestLog ? latestLog.status : "received";

        const timelineHtml = (item.logs || []).map(log => `
          <div class="timeline-item">
            <span class="time">${formatDate(log.created_at)}</span>
            <strong>[${log.status}]</strong>
            ${log.error_message ? `<span style="color: var(--error)">- ${log.error_message}</span>` : ""}
          </div>
        `).join("");

        return `
          <tr>
            <td style="color: var(--text-muted); font-size: 11px;">${formatDate(item.received_at)}</td>
            <td>
              <div style="font-weight: 600;">${item.name}</div>
              <div style="color: var(--text-muted); font-size: 11px;">${item.email}</div>
            </td>
            <td class="message-cell">
              <div>${item.message}</div>
              <button class="expand-btn" data-target="drawer-${idx}">[view audit logs (${item.logs.length})]</button>
              <div id="drawer-${idx}" class="timeline-drawer">
                ${timelineHtml}
              </div>
            </td>
            <td>${getStatusBadge(status)}</td>
          </tr>
        `;
      }).join("");

      // Add click listeners to expand buttons
      document.querySelectorAll(".expand-btn").forEach(btn => {
        btn.addEventListener("click", () => {
          const targetId = btn.getAttribute("data-target");
          const drawer = document.getElementById(targetId);
          if (drawer) {
            drawer.classList.toggle("open");
            btn.textContent = drawer.classList.contains("open") 
              ? "[collapse logs]" 
              : btn.textContent.replace("collapse", "view");
          }
        });
      });

    } catch (err) {
      enquiriesTbody.innerHTML = `<tr><td colspan="4" class="empty-state" style="color: var(--error)">Failed to load enquiries</td></tr>`;
    }
  }

  // Fetch Blocked Bots
  async function loadBots() {
    try {
      const res = await fetch("/api/admin/bots");
      if (!res.ok) throw new Error("Failed to load bots");
      const bots = await res.json();

      botsCount.textContent = `${bots.length} records`;

      if (bots.length === 0) {
        botsTbody.innerHTML = `<tr><td colspan="4" class="empty-state">// no bots trapped yet</td></tr>`;
        return;
      }

      botsTbody.innerHTML = bots.map(bot => `
        <tr>
          <td style="color: var(--text-muted); font-size: 11px;">${formatDate(bot.created_at)}</td>
          <td><span class="badge bot_blocked">bot_blocked</span></td>
          <td>honeypot_trap</td>
          <td style="color: var(--text-muted); font-size: 11px;">hidden website input was filled by scraper</td>
        </tr>
      `).join("");

    } catch (err) {
      botsTbody.innerHTML = `<tr><td colspan="4" class="empty-state" style="color: var(--error)">Failed to load bot logs</td></tr>`;
    }
  }

  function loadAllData() {
    loadStats();
    loadEnquiries();
    loadBots();
  }

  // Initial load
  loadAllData();
});
