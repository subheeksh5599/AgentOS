// Dashboard — live agent monitoring via SSE (real data only)

const AGENTS = {};     // { name: { type, status, balance, pnl, actions } }
const EVENTS = [];     // incoming events, newest first
const MAX_EVENTS = 200;

// ── SSE Connection ──

function connectSSE() {
  const proto = location.protocol === "https:" ? "https:" : "http:";
  const host = location.hostname === "localhost" ? "localhost:8420" : location.host;
  const url = `${proto}//${host}/api/runtime/events`;

  const es = new EventSource(url);

  es.onopen = () => {
    document.getElementById("dash-agents").textContent = "0";
    document.getElementById("dash-volume").textContent = "0 SUI";
    document.getElementById("dash-txns").textContent = "0";
    document.getElementById("dash-pnl").textContent = "0 SUI";
    document.getElementById("dash-pnl").style.color = "var(--ink)";
    setConnectionStatus(true);
  };

  es.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      if (data.event_type === "heartbeat") return;
      handleEvent(data);
    } catch (_) {}
  };

  es.onerror = () => {
    setConnectionStatus(false);
    es.close();
    setTimeout(connectSSE, 5000);
  };
}

// ── Handle incoming events ──

function handleEvent(data) {
  EVENTS.unshift(data);
  if (EVENTS.length > MAX_EVENTS) EVENTS.length = MAX_EVENTS;

  const name = data.agent_name;

  if (!AGENTS[name]) {
    AGENTS[name] = { type: data.agent_type, status: "running", balance: 500, pnl: 0, actions: 0 };
  }

  const agent = AGENTS[name];

  if (data.event_type === "txn") {
    agent.actions++;
    const amount = data.details?.amount || 0;
    if (data.agent_type === "trader" && data.details?.expected_profit_pct) {
      agent.pnl += amount * data.details.expected_profit_pct / 100;
    }
    const pnlSign = agent.pnl >= 0 ? "+" : "";
    agent.pnlDisplay = `${pnlSign}${agent.pnl.toFixed(1)} SUI`;
  } else if (data.event_type === "error") {
    agent.lastError = data.summary;
  }

  renderAll();
}

// ── Render ──

function setConnectionStatus(connected) {
  const dot = document.getElementById("status-dot");
  if (dot) dot.className = connected ? "status-dot live" : "status-dot dead";
  const label = document.getElementById("status-label");
  if (label) label.textContent = connected ? "Live" : "Reconnecting…";
}

function renderAll() {
  const agentList = Object.entries(AGENTS);
  const totalAgents = agentList.length;
  const totalActions = agentList.reduce((s, [, a]) => s + a.actions, 0);
  const totalPnl = agentList.reduce((s, [, a]) => s + a.pnl, 0);

  document.getElementById("dash-agents").textContent = totalAgents;
  document.getElementById("dash-txns").textContent = totalActions;

  const pnlEl = document.getElementById("dash-pnl");
  const pnlSign = totalPnl >= 0 ? "+" : "";
  pnlEl.textContent = `${pnlSign}${totalPnl.toFixed(1)} SUI`;
  pnlEl.style.color = totalPnl >= 0 ? "var(--green)" : totalPnl < 0 ? "var(--red)" : "var(--ink)";

  // Agent table
  const table = document.getElementById("agent-table");
  const empty = document.getElementById("agent-table-empty");
  if (empty && totalAgents > 0) empty.remove();

  const rows = table.querySelectorAll(".agent-row:not(#agent-row-template)");
  rows.forEach(r => r.remove());

  agentList.forEach(([name, agent]) => {
    const row = document.getElementById("agent-row-template").cloneNode(true);
    row.style.display = "grid";
    row.removeAttribute("id");

    row.querySelector(".a-name").textContent = name;
    row.querySelector(".a-type").textContent = agent.type === "yield" ? "Yield Agent"
      : agent.type === "trader" ? "Trader Agent" : "Prediction Agent";
    row.querySelector(".a-balance").textContent = `${agent.balance} SUI`;
    const pnl = row.querySelector(".a-pnl");
    pnl.textContent = agent.pnlDisplay || "0 SUI";
    pnl.classList.toggle("positive", agent.pnl > 0);
    pnl.classList.toggle("negative", agent.pnl < 0);
    row.querySelector(".a-actions").textContent = agent.actions;
    const status = row.querySelector(".a-status");
    status.textContent = agent.status === "running" ? "Active" : "Error";
    status.classList.add(agent.status === "running" ? "active" : "");
    if (agent.lastError) {
      status.textContent = "Error";
      status.classList.remove("active");
    }
    table.appendChild(row);
  });

  // Action log
  const log = document.getElementById("action-log");
  log.innerHTML = EVENTS.slice(0, 50).map(e => {
    const time = new Date(e.timestamp).toLocaleTimeString("en-US", { hour12: false });
    const hash = e.txn_digest
      ? (e.txn_digest.length > 12 ? e.txn_digest.slice(0, 10) + "…" : e.txn_digest)
      : "—";
    const walrus = e.walrus_blob_id
      ? (e.walrus_blob_id.length > 16 ? e.walrus_blob_id.slice(0, 14) + "…" : e.walrus_blob_id)
      : "—";
    const tag = e.event_type === "txn" ? "TX" : e.event_type === "error" ? "ERR" : e.event_type.toUpperCase();

    return `<div class="action-log-entry">
      <span class="log-time">${time}</span>
      <span class="log-agent">${e.agent_name}</span>
      <span class="log-action">${e.summary}</span>
      <span class="log-hash" title="${e.walrus_blob_id}">${walrus}</span>
    </div>`;
  }).join("");

  // If no events yet
  if (EVENTS.length === 0) {
    log.innerHTML = '<div class="action-log-entry"><span class="log-time">—</span><span class="log-agent">—</span><span class="log-action">Waiting for agent activity… (first cycle in ~30s)</span><span class="log-hash">—</span></div>';
  }
}

// ── Init ──

connectSSE();
setConnectionStatus(false);
