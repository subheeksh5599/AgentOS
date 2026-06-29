// Dashboard — SSE agent event stream
const events = [];
const agents = {};
const lastSeen = {};

function addEvent(type, agent, summary, walrus) {
  const list = document.getElementById("event-list");
  const empty = list.querySelector(".event-empty");
  if (empty) empty.remove();
  const el = document.createElement("div");
  el.className = "event-row";
  const t = new Date().toLocaleTimeString("en-US", { hour12: false });
  const w = walrus ? `<span class="ev-walrus">walrus:${walrus.slice(-12)}</span>` : "";
  el.innerHTML = `<span class="ev-time">${t}</span><span class="ev-agent">${agent}</span><span class="ev-msg">${summary}</span>${w}`;
  list.prepend(el);
  while (list.children.length > 100) list.lastChild.remove();
  events.unshift({ type, agent, summary });
}

function updateCard(prefix, balance, pnl, actions, lastAction) {
  const bal = document.getElementById(`${prefix}-bal`);
  const p = document.getElementById(`${prefix}-pnl`);
  const a = document.getElementById(`${prefix}-acts`);
  const l = document.getElementById(`${prefix}-last`);
  if (bal) bal.textContent = `${balance} SUI`;
  if (p) { p.textContent = pnl >= 0 ? `+${pnl} SUI` : `${pnl} SUI`; p.style.color = pnl >= 0 ? "var(--green)" : "var(--hot)"; }
  if (a) a.textContent = actions;
  if (l) l.textContent = lastAction || "—";
}

function connect() {
  const proto = location.protocol === "https:" ? "https:" : "http:";
  const host = location.hostname === "localhost" ? "localhost:8420" : location.host;
  const es = new EventSource(`${proto}//${host}/api/runtime/events`);

  es.onopen = () => { document.querySelector(".event-live")?.classList.add("connected"); };

  es.onmessage = (e) => {
    try {
      const d = JSON.parse(e.data);
      if (d.event_type === "heartbeat") return;

      const name = d.agent_name;
      if (!agents[name]) { agents[name] = { type: d.agent_type, balance: 500, pnl: 0, actions: 0, last: "" }; }

      const a = agents[name];
      a.last = d.summary?.slice(0, 60) || "";
      if (d.event_type === "txn") a.actions++;

      const prefix = name === "Alpha Yield" ? "yield" : name === "Arb Hunter v2" ? "trad" : "pred";
      updateCard(prefix, a.balance, a.pnl, a.actions, a.last);

      let walrus = d.walrus_blob_id || "";
      addEvent(d.event_type, name, d.summary || "", walrus);
    } catch (_) {}
  };

  es.onerror = () => {
    document.querySelector(".event-live")?.classList.remove("connected");
    es.close();
    setTimeout(connect, 5000);
  };
}

connect();
