// Dashboard — live agent monitoring

const DEMO_AGENTS = [
  { name: "Alpha Yield", type: "Yield Agent", balance: "342.5 SUI", pnl: "+12.4 SUI", positive: true, actions: 47, status: "active" },
  { name: "Arb Hunter v2", type: "Trader Agent", balance: "891.2 SUI", pnl: "+89.7 SUI", positive: true, actions: 312, status: "active" },
  { name: "Prediction Scout", type: "Prediction Agent", balance: "156.8 SUI", pnl: "-3.2 SUI", positive: false, actions: 28, status: "active" },
];

const DEMO_ACTIONS = [
  { time: "14:32:01", agent: "Arb Hunter v2", action: "Swap 50 SUI → 142 USDC on DeepBook Spot (SUI/USDC pool)", hash: "0x7a3b…9f2e" },
  { time: "14:28:15", agent: "Alpha Yield", action: "Rebalanced: moved 80 SUI from SUI/USDT to SUI/USDC pool (APR 8.2% > 6.5%)", hash: "0xb4c2…1d8a" },
  { time: "14:15:42", agent: "Prediction Scout", action: "Placed 10 SUI bet on SUI>5 by July (confidence 72%, edge 8%)", hash: "0x3f1a…c7b0" },
  { time: "13:58:03", agent: "Arb Hunter v2", action: "Arbitrage: bought 100 SUI at 3.42, sold at 3.47 (1.5% profit, 5 SUI net)", hash: "0x9e5d…2a4c" },
  { time: "13:42:11", agent: "Alpha Yield", action: "Compounded 4.2 SUI in rewards from SUI/USDC LP position", hash: "0xd8f7…4e1b" },
  { time: "13:30:00", agent: "Arb Hunter v2", action: "Stop-loss triggered: sold 20 SUI at 3.38 (5% loss threshold)", hash: "0x1c6a…8f3d" },
  { time: "13:15:22", agent: "Alpha Yield", action: "Daily rebalance check — current allocation optimal (no action)", hash: "0xa4b8…2e7c" },
  { time: "12:58:47", agent: "Prediction Scout", action: "Claimed 18.5 SUI winnings from resolved market: ETH>5000 by June", hash: "0x6f2d…a1b9" },
];

function renderDashboard() {
  // Stats
  document.getElementById("dash-agents").textContent = DEMO_AGENTS.length;
  const totalVol = DEMO_AGENTS.reduce((s, a) => s + parseInt(a.balance), 0);
  document.getElementById("dash-volume").textContent = totalVol.toLocaleString() + " SUI";
  document.getElementById("dash-txns").textContent = DEMO_AGENTS.reduce((s, a) => s + a.actions, 0);
  const totalPnl = DEMO_AGENTS.reduce((s, a) => {
    const v = parseFloat(a.pnl);
    return s + (a.positive ? v : -v);
  }, 0);
  const pnlEl = document.getElementById("dash-pnl");
  pnlEl.textContent = (totalPnl >= 0 ? "+" : "") + totalPnl.toFixed(1) + " SUI";
  pnlEl.style.color = totalPnl >= 0 ? "var(--green)" : "var(--red)";

  // Agent table
  const table = document.getElementById("agent-table");
  const empty = document.getElementById("agent-table-empty");
  if (empty) empty.remove();

  // Remove existing rows (keep header)
  const rows = table.querySelectorAll(".agent-row:not(#agent-row-template)");
  rows.forEach(r => r.remove());

  DEMO_AGENTS.forEach(a => {
    const row = document.getElementById("agent-row-template").cloneNode(true);
    row.style.display = "grid";
    row.removeAttribute("id");
    row.querySelector(".a-name").textContent = a.name;
    row.querySelector(".a-type").textContent = a.type;
    row.querySelector(".a-balance").textContent = a.balance;
    const pnl = row.querySelector(".a-pnl");
    pnl.textContent = a.pnl;
    pnl.classList.add(a.positive ? "positive" : "negative");
    row.querySelector(".a-actions").textContent = a.actions;
    const status = row.querySelector(".a-status");
    status.textContent = a.status === "active" ? "Active" : "Paused";
    status.classList.add(a.status);
    if (a.status !== "active") row.querySelector(".agent-dot").classList.remove("active");
    table.appendChild(row);
  });

  // Action log
  const log = document.getElementById("action-log");
  log.innerHTML = "";
  DEMO_ACTIONS.forEach(a => {
    const entry = document.createElement("div");
    entry.className = "action-log-entry";
    entry.innerHTML = `<span class="log-time">${a.time}</span><span class="log-agent">${a.agent}</span><span class="log-action">${a.action}</span><span class="log-hash">${a.hash}</span>`;
    log.appendChild(entry);
  });
}

renderDashboard();
