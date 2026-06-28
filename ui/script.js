// ════════════════════════════════════════════════════════════
//  AgentOS — Nimbus Grid frontend
// ════════════════════════════════════════════════════════════

const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function debounce(fn, ms) {
  let t;
  return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}

// ── WebGL aurora shader ──────────────────────────────────────

const canvas = document.querySelector(".shader-canvas");
const gl = canvas && canvas.getContext("webgl", { alpha: true, antialias: false });

const vertSrc = `attribute vec2 a_pos; void main() { gl_Position = vec4(a_pos, 0.0, 1.0); }`;

const fragSrc = `precision highp float;
uniform vec2 u_res;
uniform float u_time;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
  vec2 i = floor(p), f = fract(p);
  f = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x),
             mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x), f.y);
}
float fbm(vec2 p) {
  float v = 0.0, a = 0.5;
  for (int i = 0; i < 6; i++) { v += a * noise(p); p *= 2.0; a *= 0.5; }
  return v;
}
void main() {
  vec2 uv = gl_FragCoord.xy / u_res;
  vec2 p = uv * 3.0;
  p.x += u_time * 0.045;
  p.y -= u_time * 0.03;
  float n1 = fbm(p);
  float n2 = fbm(p * 0.7 + vec2(4.2, 1.3) + u_time * 0.02);
  float n3 = fbm(p * 1.6 + vec2(-u_time * 0.03, u_time * 0.025));

  // palette: teal -> cyan -> indigo -> violet
  vec3 teal   = vec3(0.169, 0.835, 0.753);
  vec3 cyan   = vec3(0.271, 0.902, 1.0);
  vec3 indigo = vec3(0.486, 0.549, 1.0);
  vec3 violet = vec3(0.690, 0.486, 1.0);

  vec3 col = mix(teal, cyan, smoothstep(0.2, 0.7, n1));
  col = mix(col, indigo, smoothstep(0.3, 0.9, n2));
  col = mix(col, violet, smoothstep(0.55, 1.0, n3) * 0.7);

  float glow = pow(n1, 2.0) * 0.6 + n3 * 0.25;
  float alpha = smoothstep(0.05, 0.75, n1) * 0.42 + glow * 0.22;
  gl_FragColor = vec4(col * (0.5 + glow), alpha);
}`;

function compileShader(gl, type, src) {
  const s = gl.createShader(type);
  gl.shaderSource(s, src); gl.compileShader(s);
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) { console.error(gl.getShaderInfoLog(s)); return null; }
  return s;
}
function createProgram(gl, vs, fs) {
  const v = compileShader(gl, gl.VERTEX_SHADER, vs), f = compileShader(gl, gl.FRAGMENT_SHADER, fs);
  if (!v || !f) return null;
  const p = gl.createProgram();
  gl.attachShader(p, v); gl.attachShader(p, f); gl.linkProgram(p);
  if (!gl.getProgramParameter(p, gl.LINK_STATUS)) { console.error(gl.getProgramInfoLog(p)); return null; }
  return p;
}

if (gl && !prefersReduced) {
  const program = createProgram(gl, vertSrc, fragSrc);
  if (program) {
    const aPos = gl.getAttribLocation(program, "a_pos");
    const uRes = gl.getUniformLocation(program, "u_res");
    const uTime = gl.getUniformLocation(program, "u_time");
    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, -1,1, 1,-1, 1,1]), gl.STATIC_DRAW);
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
    function render(time) {
      const w = canvas.width, h = canvas.height;
      if (w && h) {
        gl.viewport(0, 0, w, h);
        gl.useProgram(program);
        gl.uniform2f(uRes, w, h);
        gl.uniform1f(uTime, time * 0.001);
        gl.bindBuffer(gl.ARRAY_BUFFER, buf);
        gl.enableVertexAttribArray(aPos);
        gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);
        gl.drawArrays(gl.TRIANGLES, 0, 6);
      }
      requestAnimationFrame(render);
    }
    requestAnimationFrame(render);
  }
}

const SHADER_W = 1280, SHADER_H = 760;
function updateShaderSize() {
  if (!canvas) return;
  const hero = document.querySelector(".hero");
  const scale = Math.max(window.innerWidth / SHADER_W, (window.innerHeight + 120) / SHADER_H);
  hero.style.setProperty("--shader-scale", String(scale));
  canvas.width = SHADER_W; canvas.height = SHADER_H;
}
window.addEventListener("resize", debounce(updateShaderSize, 160));
updateShaderSize();

// ── Header scroll state + progress bar ───────────────────────

const header = document.getElementById("site-header");
const progress = document.getElementById("scroll-progress");
function onScroll() {
  const y = window.scrollY;
  if (header) header.classList.toggle("is-scrolled", y > 24);
  if (progress) {
    const max = document.documentElement.scrollHeight - window.innerHeight;
    progress.style.width = (max > 0 ? (y / max) * 100 : 0) + "%";
  }
}
window.addEventListener("scroll", onScroll, { passive: true });
onScroll();

// ── Parallax ─────────────────────────────────────────────────

const layerDeep = document.querySelector(".layer-deep");
const layerMid = document.querySelector(".layer-mid");
if (!prefersReduced) {
  window.addEventListener("scroll", () => {
    const y = window.scrollY;
    if (layerDeep) layerDeep.style.transform = `translate3d(0, ${y * -0.08}px, 0)`;
    if (layerMid) layerMid.style.transform = `translate3d(0, ${y * -0.04}px, 0)`;
  }, { passive: true });
}

// ── Reveal on scroll ─────────────────────────────────────────

const revealEls = document.querySelectorAll(".reveal-up, .reveal-scale");
if ("IntersectionObserver" in window) {
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) { e.target.classList.add("is-visible"); io.unobserve(e.target); }
    });
  }, { threshold: 0.12, rootMargin: "0px 0px -8% 0px" });
  revealEls.forEach((el) => io.observe(el));
} else {
  revealEls.forEach((el) => el.classList.add("is-visible"));
}

// ── Spotlight feature cards ──────────────────────────────────

document.querySelectorAll("[data-spotlight]").forEach((card) => {
  card.addEventListener("pointermove", (e) => {
    const r = card.getBoundingClientRect();
    card.style.setProperty("--mx", `${e.clientX - r.left}px`);
    card.style.setProperty("--my", `${e.clientY - r.top}px`);
  });
});

// ── Magnetic buttons ─────────────────────────────────────────

if (!prefersReduced) {
  document.querySelectorAll("[data-magnetic]").forEach((el) => {
    el.addEventListener("pointermove", (e) => {
      const r = el.getBoundingClientRect();
      const mx = e.clientX - r.left - r.width / 2;
      const my = e.clientY - r.top - r.height / 2;
      el.style.transform = `translate(${mx * 0.16}px, ${my * 0.22}px)`;
    });
    el.addEventListener("pointerleave", () => { el.style.transform = ""; });
  });
}

// ── Console tabs + typewriter ────────────────────────────────

let typeTimer;
function cancelTyping() { if (typeTimer) { clearTimeout(typeTimer); typeTimer = null; } }
function resetTyped(pane) {
  pane.querySelectorAll("[data-typed]").forEach((el) => {
    if (el.dataset.original === undefined) el.dataset.original = el.getAttribute("data-typed");
    el.textContent = "";
  });
}
async function typeSeq(pane) {
  const els = pane.querySelectorAll("[data-typed]");
  for (const el of els) {
    const full = el.dataset.original || "";
    el.textContent = ""; el.classList.add("is-typing");
    await new Promise((resolve) => {
      let i = 0;
      (function tick() {
        if (i < full.length) { el.textContent += full[i++]; typeTimer = setTimeout(tick, 34); }
        else { el.classList.remove("is-typing"); resolve(); }
      })();
    });
  }
}
function switchTab(index) {
  cancelTyping();
  const tabs = document.querySelectorAll(".console-tab");
  const panes = document.querySelectorAll(".console-pane");
  tabs.forEach((t, i) => { const a = i === index; t.classList.toggle("is-active", a); t.setAttribute("aria-selected", String(a)); });
  panes.forEach((p, i) => p.classList.toggle("is-active", i === index));
  const active = panes[index];
  resetTyped(active); typeSeq(active);
}
document.querySelectorAll(".console-tab").forEach((t, i) => t.addEventListener("click", () => switchTab(i)));
const firstPane = document.querySelector(".console-pane.is-active");
if (firstPane) { resetTyped(firstPane); typeSeq(firstPane); }

// ── Smooth scroll for in-page links ──────────────────────────

document.querySelectorAll('a[href^="#"]').forEach((link) => {
  link.addEventListener("click", (e) => {
    const id = link.getAttribute("href");
    if (id.length < 2) return;
    const target = document.querySelector(id);
    if (target) { e.preventDefault(); target.scrollIntoView({ behavior: prefersReduced ? "auto" : "smooth", block: "start" }); }
  });
});

// ── Popups ───────────────────────────────────────────────────

const popupOverlay = document.getElementById("popup-overlay");
const popupBody = popupOverlay.querySelector(".popup-body");
const popupClose = popupOverlay.querySelector(".popup-close");
const popupContent = {
  encryption: {
    title: "AES-256-GCM Encryption",
    body: `<p>Every object written to the grid is encrypted with AES-256-GCM using a unique per-object data key. Those keys are wrapped by a master key stored in a FIPS 140-2 Level 3 HSM.</p><p>Keys rotate every 72 hours — a fresh data key is generated for each write after rotation. Old keys are never deleted; they stay available for reads until the object itself is removed.</p><dl class="popup-stat"><dt>Algorithm</dt><dd>AES-256-GCM</dd><dt>Rotation</dt><dd>Every 72 hours</dd><dt>HSM</dt><dd>FIPS 140-2 L3</dd></dl>`,
  },
  residency: {
    title: "Data Residency Controls",
    body: `<p>AgentOS enforces geographic residency at the control plane. Pin a pool to a region and the metadata service guarantees no data-bearing request leaves it — not for replication, backup, or maintenance.</p><p>Each region is a fully isolated deployment with its own control plane, metadata store, and object layer. Cross-region replication is opt-in only.</p><dl class="popup-stat"><dt>Regions</dt><dd>14 globally</dd><dt>Isolation</dt><dd>Per-region plane</dd><dt>Compliance</dt><dd>SOC 2 · ISO 27001</dd></dl>`,
  },
  throughput: {
    title: "Provisioned Throughput",
    body: `<p>Every pool gets dedicated provisioned IOPS and bandwidth. No noisy neighbours — capacity is reserved at the node level with strict quality-of-service enforcement.</p><p>Each pool includes 50% burst headroom above provisioned capacity for up to 30 minutes per day, giving room for spikes without over-provisioning.</p><dl class="popup-stat"><dt>Min IOPS</dt><dd>1,000 / pool</dd><dt>Max IOPS</dt><dd>100,000 / pool</dd><dt>Burst</dt><dd>50% · 30min/day</dd></dl>`,
  },
  audit: {
    title: "Tamper-Proof Ledger",
    body: `<p>Every read, write, list, and permission change is recorded in an append-only ledger with cryptographic chaining. Each entry is hashed and linked to the previous — tamper with any record and the chain rejects it.</p><p>The grid continuously re-verifies the chain; the live "verified" badge in the hero reflects the real <code>verify_chain()</code> result from the backend.</p><dl class="popup-stat"><dt>Chaining</dt><dd>SHA-256</dd><dt>Format</dt><dd>JSON over gRPC</dd><dt>Export</dt><dd>Splunk · Datadog · S3</dd></dl>`,
  },
  contact: {
    title: "Contact Enterprise Sales",
    body: `<p>Our enterprise team designs a topology that matches your compliance requirements, performance targets, and budget. We typically respond within one business day.</p><p>Enterprise plans include dedicated support engineers, custom SLAs, on-premise gateways, and bring-your-own-key encryption.</p><form class="popup-form" onsubmit="event.preventDefault(); this.innerHTML='<p style=color:var(--green)>Thanks — we&rsquo;ll reach out within 24 hours.</p>'"><label class="popup-label" for="ce">Work email</label><input id="ce" type="email" class="popup-input" placeholder="you@company.com" required /><button type="submit" class="popup-submit">Send</button></form>`,
  },
};
function openPopup(key) {
  const d = popupContent[key]; if (!d) return;
  popupBody.innerHTML = `<h3>${d.title}</h3>${d.body}`;
  popupOverlay.classList.add("is-open");
  popupOverlay.setAttribute("aria-hidden", "false");
  document.body.style.overflow = "hidden";
}
function closePopup() {
  popupOverlay.classList.remove("is-open");
  popupOverlay.setAttribute("aria-hidden", "true");
  document.body.style.overflow = "";
}
popupClose.addEventListener("click", closePopup);
popupOverlay.addEventListener("click", (e) => { if (e.target === popupOverlay) closePopup(); });
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && popupOverlay.classList.contains("is-open")) closePopup(); });
document.querySelectorAll("[data-popup]").forEach((el) => el.addEventListener("click", (e) => { e.preventDefault(); openPopup(el.dataset.popup); }));

// ── Stat counters ────────────────────────────────────────────

const statValues = document.querySelectorAll(".stat-value[data-count]");
if ("IntersectionObserver" in window) {
  const so = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (!e.isIntersecting) return;
      so.unobserve(e.target);
      const el = e.target;
      const target = parseFloat(el.dataset.count);
      const decimals = parseInt(el.dataset.decimals || "0", 10);
      const dur = 1500, start = performance.now();
      function tick(now) {
        const t = Math.min((now - start) / dur, 1);
        const eased = 1 - Math.pow(1 - t, 3);
        el.textContent = (target * eased).toFixed(decimals);
        if (t < 1) requestAnimationFrame(tick); else el.textContent = target.toFixed(decimals);
      }
      requestAnimationFrame(tick);
    });
  }, { threshold: 0.4 });
  statValues.forEach((el) => so.observe(el));
}

// ════════════════════════════════════════════════════════════
//  AgentOS backend integration
// ════════════════════════════════════════════════════════════

const feedLog = document.getElementById("feed-log");
const feedStatusText = document.getElementById("feed-status-text");
const feedDot = document.querySelector(".feed-dot");
const feedMeta = document.getElementById("feed-meta");
const consoleOutput = document.getElementById("console-output");
const consoleInput = document.getElementById("console-input");
const consoleForm = document.getElementById("console-form");
const navStatus = document.getElementById("nav-status");
const navStatusText = document.getElementById("nav-status-text");

const TAG_MAP = {
  agent_online: ["ONLINE", "agent-online"], pool_created: ["POOL", "storage"],
  storage_allocated: ["STORAGE", "storage"], health_report: ["HEALTH", "monitor"],
  node_alert: ["ALERT", "alert"], security_scan: ["SECURITY", "security"],
  txn_committed: ["TXN", "txn"], console_command: ["CMD", "console"],
  status_report: ["STATUS", "monitor"], error: ["ERROR", "alert"],
};
const AGENT_FOR_TAG = {
  storage: "StorageAgent", security: "SecurityAgent", monitor: "MonitorAgent",
  txn: "OpsAgent", console: "OpsAgent",
};

let lastEventCount = 0;
let lastFeedEntry = null; // for collapsing repeated health events

function escapeHtml(s) {
  return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

function addFeedEntry(tag, tagClass, sender, msg, time) {
  if (!feedLog) return;
  const placeholder = feedLog.querySelector(".feed-placeholder");
  if (placeholder) placeholder.remove();

  // collapse consecutive same-type entries (kills the HEALTH spam)
  if (lastFeedEntry && lastFeedEntry.dataset.tag === tagClass && lastFeedEntry.dataset.sender === sender) {
    const n = (parseInt(lastFeedEntry.dataset.count || "1", 10)) + 1;
    lastFeedEntry.dataset.count = String(n);
    const t = time ? new Date(time) : new Date();
    lastFeedEntry.querySelector(".feed-time").textContent = t.toLocaleTimeString("en-US", { hour12: false });
    lastFeedEntry.querySelector(".feed-msg").innerHTML =
      `<span class="agent-name">${escapeHtml(sender)}</span> ${escapeHtml(msg)} <span class="feed-count">×${n}</span>`;
    return;
  }

  const entry = document.createElement("div");
  entry.className = "feed-entry";
  entry.dataset.tag = tagClass; entry.dataset.sender = sender; entry.dataset.count = "1";
  const t = time ? new Date(time) : new Date();
  entry.innerHTML =
    `<span class="feed-tag ${tagClass}">${escapeHtml(tag)}</span>` +
    `<span class="feed-time">${t.toLocaleTimeString("en-US", { hour12: false })}</span>` +
    `<span class="feed-msg"><span class="agent-name">${escapeHtml(sender)}</span> ${escapeHtml(msg)}</span>`;
  feedLog.prepend(entry);
  lastFeedEntry = entry;
  while (feedLog.children.length > 80) feedLog.lastChild.remove();
}

function appendConsole(text, cls = "") {
  if (!consoleOutput) return;
  const pre = document.createElement("pre");
  pre.className = "console-text" + (cls ? " " + cls : "");
  pre.innerHTML = text;
  consoleOutput.appendChild(pre);
  consoleOutput.scrollTop = consoleOutput.scrollHeight;
}

function setConnected(online) {
  if (feedStatusText) feedStatusText.textContent = online ? "Connected" : "Offline";
  if (feedDot) feedDot.classList.toggle("disconnected", !online);
  if (navStatus) { navStatus.classList.toggle("is-online", online); navStatus.classList.toggle("is-offline", !online); }
  if (navStatusText) navStatusText.textContent = online ? "grid online" : "offline";
}

async function pollEvents() {
  try {
    const resp = await fetch(`/api/events/history?room=grid-ops&limit=60`);
    const events = await resp.json();
    if (events.length > lastEventCount) {
      for (let i = lastEventCount; i < events.length; i++) {
        const m = events[i];
        const [tag, tagClass] = TAG_MAP[m.event_type] || [(m.event_type || "EVENT").toUpperCase(), "console"];
        addFeedEntry(tag, tagClass, m.sender, m.content, m.timestamp);
        flashAgent(AGENT_FOR_TAG[tagClass]);
        if (m.event_type === "health_report") updateHealthReadout(m.content);
        if (tagClass === "txn" || tagClass === "storage") gridFirePacket();
      }
      lastEventCount = events.length;
    }
    setConnected(true);
  } catch { setConnected(false); }
}

async function initConsole() {
  appendConsole('<span class="output success">Connected to AgentOS v0.1</span>');
  try {
    const resp = await fetch(`/api/console`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ command: "status" }) });
    const data = await resp.json();
    appendConsole(escapeHtml(data.output));
    appendConsole('<span class="output muted">Type a command below — try store, scan, nodes…</span>');
    setConnected(true);
  } catch {
    setConnected(false);
    appendConsole('<span class="error">Backend unreachable. Is the server running?</span>');
  }
}

async function sendCommand(cmd) {
  if (!cmd.trim()) return;
  appendConsole(`<span class="prompt">$</span> ${escapeHtml(cmd)}`);
  try {
    const resp = await fetch(`/api/console`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ command: cmd }) });
    const data = await resp.json();
    const isErr = /error|fail|unknown/i.test(data.output);
    appendConsole(escapeHtml(data.output), isErr ? "error" : "output success");
    refreshState();
  } catch { appendConsole("Error: AgentOS backend not reachable.", "error"); }
}

if (consoleForm) {
  consoleForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const cmd = consoleInput.value.trim();
    if (cmd) { sendCommand(cmd); consoleInput.value = ""; }
  });
}

// Provision button (Provision tab)
const provisionBtn = document.querySelector(".console-provision");
if (provisionBtn) {
  provisionBtn.addEventListener("click", async () => {
    provisionBtn.disabled = true;
    try {
      const resp = await fetch(`/api/pools`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: "web-db-prod", region: "eu-west-1", tier: "encrypted-fast", capacity_tb: 128 }),
      });
      const pool = await resp.json();
      provisionBtn.textContent = `✓ Pool ${pool.name} provisioned`;
      provisionBtn.classList.add("is-done");
      gridFirePacket(); refreshState();
      setTimeout(() => { provisionBtn.textContent = "Provision pool"; provisionBtn.classList.remove("is-done"); provisionBtn.disabled = false; }, 2600);
    } catch { provisionBtn.textContent = "Backend offline"; provisionBtn.disabled = false; }
  });
}

// ── Live state → hero metrics + grid readout + API pane ──────

const heroNodes = document.getElementById("hero-nodes");
const heroRegions = document.getElementById("hero-regions");
const heroChain = document.getElementById("hero-chain");
const roLoad = document.getElementById("ro-load");
const roLoadBar = document.getElementById("ro-load-bar");
const roCap = document.getElementById("ro-cap");
const roTput = document.getElementById("ro-tput");

async function refreshState() {
  try {
    const resp = await fetch(`/api/state`);
    const s = await resp.json();
    if (heroNodes) heroNodes.innerHTML = `${s.online_nodes}<span>/${s.total_nodes}</span>`;
    if (heroRegions) heroRegions.textContent = s.regions.length;
    if (heroChain) heroChain.textContent = s.chain_verified ? "verified" : "broken";
    const usedPct = s.total_capacity_tb ? (s.total_used_tb / s.total_capacity_tb) * 100 : 0;
    if (roLoad) roLoad.textContent = usedPct.toFixed(1) + "%";
    if (roLoadBar) roLoadBar.style.width = Math.max(2, usedPct) + "%";
    if (roCap) roCap.textContent = `${s.total_used_tb.toFixed(0)} / ${s.total_capacity_tb.toFixed(0)} TB`;
    // agents online chips
    if (s.agents) {
      document.querySelectorAll(".ag-chip").forEach((chip) => {
        const online = s.agents[chip.dataset.agent];
        chip.classList.toggle("is-active", !!online);
      });
    }
    const apiPane = document.querySelector('[data-pane="1"]');
    if (apiPane && s.total_nodes > 0) {
      apiPane.innerHTML = `<pre class="console-text"><span class="prompt">GET</span> /api/state
{
  "<span class="key">online_nodes</span>": <span class="num">${s.online_nodes}</span>,
  "<span class="key">total_nodes</span>": <span class="num">${s.total_nodes}</span>,
  "<span class="key">total_pools</span>": <span class="num">${s.total_pools}</span>,
  "<span class="key">capacity_tb</span>": <span class="num">${s.total_capacity_tb.toFixed(0)}</span>,
  "<span class="key">used_tb</span>": <span class="num">${s.total_used_tb.toFixed(1)}</span>,
  "<span class="key">committed_txns</span>": <span class="num">${s.committed_transactions}</span>,
  "<span class="key">chain_verified</span>": <span class="val">${s.chain_verified}</span>,
  "<span class="key">regions</span>": [${s.regions.map((r) => `<span class="val">"${r}"</span>`).join(", ")}]
}</pre>`;
    }
    setConnected(true);
  } catch { setConnected(false); }
}

const roLat = document.getElementById("ro-lat");
function updateHealthReadout(content) {
  const lat = content.match(/latency:\s*([\d.]+)\s*ms/i);
  const tput = content.match(/Throughput:\s*([\d.]+)\s*Mbps/i);
  if (lat && roLat) roLat.textContent = `${parseFloat(lat[1]).toFixed(0)} ms`;
  if (tput && roTput) roTput.textContent = `${parseFloat(tput[1]).toFixed(0)} Mbps`;
}

function flashAgent(name) {
  if (!name) return;
  const chip = document.querySelector(`.ag-chip[data-agent="${name}"]`);
  if (!chip) return;
  chip.classList.add("is-fire");
  setTimeout(() => chip.classList.remove("is-fire"), 700);
}

// ════════════════════════════════════════════════════════════
//  Live grid topology canvas
// ════════════════════════════════════════════════════════════

const gridCanvas = document.getElementById("grid-canvas");
let gridFirePacket = () => {};

if (gridCanvas) {
  const ctx = gridCanvas.getContext("2d");
  let DPR = Math.min(window.devicePixelRatio || 1, 2);
  let W = 0, H = 0;
  let nodes = [];      // {x,y,r,region,type,baseR,pulse,used}
  let regions = [];    // {name,cx,cy,nodes:[]}
  let links = [];      // [aIdx,bIdx]
  let packets = [];    // {a,b,t,speed,color}
  let t0 = performance.now();

  const COLORS = { storage: "#45e6ff", gateway: "#b07cff", line: "rgba(140,170,220,0.16)", packet: "#4be08a" };

  function resize() {
    const rect = gridCanvas.getBoundingClientRect();
    W = rect.width; H = rect.height;
    DPR = Math.min(window.devicePixelRatio || 1, 2);
    gridCanvas.width = W * DPR; gridCanvas.height = H * DPR;
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    layout();
  }

  function layout() {
    if (!regions.length) return;
    const n = regions.length;
    const leftPad = 70;
    const rightPad = W > 760 ? 280 : 70;   // keep clear of the readout panel
    const usableW = Math.max(120, W - leftPad - rightPad);
    const rad = Math.min(usableW / n, H) * 0.34;
    regions.forEach((reg, i) => {
      reg.cx = leftPad + usableW * ((i + 0.5) / n);
      reg.cy = H * 0.44;
      reg.rad = rad;
      const count = reg.nodes.length;
      reg.nodes.forEach((idx, j) => {
        const ang = (j / count) * Math.PI * 2 - Math.PI / 2;
        const node = nodes[idx];
        node.x = reg.cx + Math.cos(ang) * rad * (node.type === "gateway" ? 0 : 1);
        node.y = reg.cy + Math.sin(ang) * rad * (node.type === "gateway" ? 0 : 1);
        node.baseR = node.type === "gateway" ? 9 : 5 + node.used * 4;
      });
    });
  }

  function buildFromNodes(apiNodes) {
    nodes = []; regions = []; links = [];
    const byRegion = {};
    apiNodes.forEach((n) => { (byRegion[n.region] ||= []).push(n); });
    Object.keys(byRegion).sort().forEach((regName) => {
      const reg = { name: regName, cx: 0, cy: 0, nodes: [] };
      // gateway hub for the region
      const gwIdx = nodes.length;
      nodes.push({ region: regName, type: "gateway", used: 0, baseR: 9, pulse: Math.random() * 6 });
      reg.nodes.push(gwIdx);
      byRegion[regName].forEach((apiN) => {
        const idx = nodes.length;
        const used = apiN.capacity_tb ? Math.min(apiN.used_tb / apiN.capacity_tb, 1) : 0;
        nodes.push({ region: regName, type: "storage", used, baseR: 6, pulse: Math.random() * 6, status: apiN.status });
        reg.nodes.push(idx);
        links.push([gwIdx, idx]);
      });
      regions.push(reg);
    });
    // gateway mesh between regions
    const gws = nodes.map((n, i) => (n.type === "gateway" ? i : -1)).filter((i) => i >= 0);
    for (let i = 0; i < gws.length; i++)
      for (let j = i + 1; j < gws.length; j++) links.push([gws[i], gws[j], true]);
    layout();
  }

  function spawnPacket(crossRegion) {
    const gws = nodes.map((n, i) => (n.type === "gateway" ? i : -1)).filter((i) => i >= 0);
    if (crossRegion && gws.length > 1) {
      const a = gws[Math.floor(Math.random() * gws.length)];
      let b = gws[Math.floor(Math.random() * gws.length)];
      if (a === b) b = gws[(gws.indexOf(b) + 1) % gws.length];
      packets.push({ a, b, t: 0, speed: 0.012 + Math.random() * 0.01, color: COLORS.packet, big: true });
    } else if (links.length) {
      const [a, b] = links[Math.floor(Math.random() * links.length)];
      packets.push({ a, b, t: 0, speed: 0.02 + Math.random() * 0.02, color: COLORS.packet });
    }
  }
  gridFirePacket = () => { spawnPacket(true); spawnPacket(false); };

  function draw(now) {
    if (!W || !H) { requestAnimationFrame(draw); return; }
    const time = (now - t0) / 1000;
    ctx.clearRect(0, 0, W, H);

    // links
    links.forEach(([a, b, cross]) => {
      const na = nodes[a], nb = nodes[b];
      if (!na || !nb) return;
      ctx.beginPath();
      ctx.moveTo(na.x, na.y); ctx.lineTo(nb.x, nb.y);
      ctx.strokeStyle = cross ? "rgba(176,124,255,0.18)" : COLORS.line;
      ctx.lineWidth = cross ? 1.2 : 1;
      ctx.stroke();
    });

    // packets
    packets = packets.filter((p) => p.t < 1);
    packets.forEach((p) => {
      p.t += p.speed;
      const na = nodes[p.a], nb = nodes[p.b];
      if (!na || !nb) return;
      const x = na.x + (nb.x - na.x) * p.t;
      const y = na.y + (nb.y - na.y) * p.t;
      const r = p.big ? 4 : 2.6;
      ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fillStyle = p.color; ctx.shadowColor = p.color; ctx.shadowBlur = 12;
      ctx.fill(); ctx.shadowBlur = 0;
    });

    // nodes
    nodes.forEach((n) => {
      if (n.x == null) return;
      const pulse = prefersReduced ? 0 : Math.sin(time * 1.4 + n.pulse) * 1.2;
      const r = n.baseR + pulse;
      const col = n.type === "gateway" ? COLORS.gateway : COLORS.storage;
      // glow ring
      ctx.beginPath(); ctx.arc(n.x, n.y, r + 5, 0, Math.PI * 2);
      ctx.fillStyle = n.type === "gateway" ? "rgba(176,124,255,0.10)" : "rgba(69,230,255,0.08)";
      ctx.fill();
      // core
      ctx.beginPath(); ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
      ctx.fillStyle = col; ctx.shadowColor = col; ctx.shadowBlur = 14;
      ctx.fill(); ctx.shadowBlur = 0;
      if (n.status && n.status !== "online") {
        ctx.beginPath(); ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
        ctx.strokeStyle = "#ff6b7d"; ctx.lineWidth = 1.5; ctx.stroke();
      }
    });

    // region labels
    ctx.font = "11px 'IBM Plex Mono', monospace";
    ctx.textAlign = "center";
    regions.forEach((reg) => {
      ctx.fillStyle = "rgba(142,162,192,0.7)";
      ctx.fillText(reg.name, reg.cx, reg.cy + (reg.rad || 60) + 28);
    });

    requestAnimationFrame(draw);
  }

  async function initGrid() {
    try {
      const resp = await fetch(`/api/nodes`);
      const apiNodes = await resp.json();
      if (Array.isArray(apiNodes) && apiNodes.length) buildFromNodes(apiNodes);
    } catch { /* offline — canvas stays empty */ }
  }

  window.addEventListener("resize", debounce(resize, 160));
  initGrid().then(resize);
  requestAnimationFrame(draw);
  // ambient cross-region traffic
  if (!prefersReduced) setInterval(() => { if (Math.random() > 0.4) spawnPacket(Math.random() > 0.5); }, 1400);
}

// ── Boot ─────────────────────────────────────────────────────

initConsole();
refreshState();
pollEvents();
setInterval(pollEvents, 3000);
setInterval(refreshState, 8000);
