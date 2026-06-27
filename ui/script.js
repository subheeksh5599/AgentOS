function debounce(fn, ms) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

// ── WebGL shader canvas ──

const canvas = document.querySelector(".shader-canvas");
const gl = canvas.getContext("webgl", { alpha: true, antialias: false });

const vertSrc = `attribute vec2 a_pos; void main() { gl_Position = vec4(a_pos, 0.0, 1.0); }`;

const fragSrc = `precision highp float;
uniform vec2 u_res;
uniform float u_time;

float hash(vec2 p) {
  return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  f = f * f * (3.0 - 2.0 * f);
  return mix(
    mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x),
    mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x),
    f.y
  );
}

float fbm(vec2 p) {
  float v = 0.0, a = 0.5;
  for (int i = 0; i < 5; i++) {
    v += a * noise(p);
    p *= 2.0;
    a *= 0.5;
  }
  return v;
}

void main() {
  vec2 uv = gl_FragCoord.xy / u_res;
  vec2 p = uv * 3.5;
  p.x += u_time * 0.06;
  p.y += u_time * 0.04;

  float n1 = fbm(p);
  float n2 = fbm(p + vec2(3.7, 1.2) + u_time * 0.03);
  float n3 = fbm(p * 0.6 + vec2(u_time * 0.05, -u_time * 0.02));

  float r = n1 * 0.15 + n3 * 0.08;
  float g = n1 * 0.22 + n2 * 0.12;
  float b = n1 * 0.35 + n2 * 0.18 + n3 * 0.10;

  float alpha = smoothstep(0.0, 0.7, n1) * 0.45 + r * 0.35;

  gl_FragColor = vec4(r, g, b, alpha);
}`;

function compileShader(gl, type, src) {
  const s = gl.createShader(type);
  gl.shaderSource(s, src);
  gl.compileShader(s);
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
    console.error(gl.getShaderInfoLog(s));
    gl.deleteShader(s);
    return null;
  }
  return s;
}

function createProgram(gl, vs, fs) {
  const vert = compileShader(gl, gl.VERTEX_SHADER, vs);
  const frag = compileShader(gl, gl.FRAGMENT_SHADER, fs);
  if (!vert || !frag) return null;
  const prog = gl.createProgram();
  gl.attachShader(prog, vert);
  gl.attachShader(prog, frag);
  gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
    console.error(gl.getProgramInfoLog(prog));
    return null;
  }
  return prog;
}

const program = createProgram(gl, vertSrc, fragSrc);
if (program) {
  const aPos = gl.getAttribLocation(program, "a_pos");
  const uRes = gl.getUniformLocation(program, "u_res");
  const uTime = gl.getUniformLocation(program, "u_time");

  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]), gl.STATIC_DRAW);

  function renderShader(time) {
    const w = canvas.width;
    const h = canvas.height;
    if (w === 0 || h === 0) {
      requestAnimationFrame(renderShader);
      return;
    }
    gl.viewport(0, 0, w, h);
    gl.useProgram(program);
    gl.uniform2f(uRes, w, h);
    gl.uniform1f(uTime, time * 0.001);
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.enableVertexAttribArray(aPos);
    gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);
    gl.drawArrays(gl.TRIANGLES, 0, 6);
    requestAnimationFrame(renderShader);
  }

  requestAnimationFrame(renderShader);
}

// ── Shader sizing ──

const shaderWidth = 1422;
const shaderHeight = 800;

function updateShaderSize() {
  const hero = document.querySelector(".hero");
  const w = window.innerWidth;
  const h = window.innerHeight;
  const scale = Math.max(w / shaderWidth, (h + 110) / shaderHeight);
  hero.style.setProperty("--shader-scale", String(scale));
  canvas.width = shaderWidth;
  canvas.height = shaderHeight;
}

const resizeShader = debounce(updateShaderSize, 180);
window.addEventListener("resize", resizeShader);
updateShaderSize();

// ── Console tabs + typewriter ──

let typeTimer;
let typeCancel;

function cancelTyping() {
  if (typeTimer) {
    clearTimeout(typeTimer);
    typeTimer = null;
  }
  if (typeCancel) {
    clearTimeout(typeCancel);
    typeCancel = null;
  }
}

function resetTypedElements(pane) {
  const els = pane.querySelectorAll("[data-typed]");
  els.forEach((el) => {
    el.textContent = "";
    if (el.dataset.original === undefined) {
      el.dataset.original = el.getAttribute("data-typed");
    }
  });
}

async function typeInSequence(pane) {
  const els = pane.querySelectorAll("[data-typed]");
  for (const el of els) {
    const full = el.dataset.original || el.getAttribute("data-typed") || "";
    el.textContent = "";
    el.classList.add("is-typing");
    await new Promise((resolve) => {
      let i = 0;
      function tick() {
        if (i < full.length) {
          el.textContent += full[i];
          i++;
          typeTimer = setTimeout(tick, 42);
        } else {
          el.classList.remove("is-typing");
          resolve();
        }
      }
      typeCancel = () => { i = full.length; el.classList.remove("is-typing"); resolve(); };
      tick();
    });
  }
}

function switchTab(index) {
  cancelTyping();

  const tabs = document.querySelectorAll(".console-tab");
  const panes = document.querySelectorAll(".console-pane");

  tabs.forEach((tab, i) => {
    const active = i === index;
    tab.classList.toggle("is-active", active);
    tab.setAttribute("aria-selected", String(active));
  });

  panes.forEach((pane, i) => {
    pane.classList.toggle("is-active", i === index);
  });

  const activePane = panes[index];
  resetTypedElements(activePane);
  typeInSequence(activePane);
}

document.querySelectorAll(".console-tab").forEach((tab, i) => {
  tab.addEventListener("click", () => switchTab(i));
});

// Start typewriter on load for the first pane
const activePane = document.querySelector(".console-pane.is-active");
if (activePane) {
  resetTypedElements(activePane);
  typeInSequence(activePane);
}

// ── Parallax scrolling ──

const layerDeep = document.querySelector(".layer-deep");
const layerMid = document.querySelector(".layer-mid");
const layerShallow = document.querySelector(".layer-shallow");

function updateParallax() {
  const scrollY = window.scrollY;
  if (layerDeep) layerDeep.style.transform = `translate3d(0, ${scrollY * -0.15}px, 0)`;
  if (layerMid) layerMid.style.transform = `translate3d(0, ${scrollY * -0.08}px, 0)`;
  if (layerShallow) layerShallow.style.transform = `translate3d(0, ${scrollY * -0.03}px, 0)`;
}

window.addEventListener("scroll", updateParallax, { passive: true });
updateParallax();

// ── Hide scroll hint on scroll ──

const scrollHint = document.querySelector(".scroll-hint");
if (scrollHint) {
  window.addEventListener("scroll", () => {
    const opacity = Math.max(0, 1 - window.scrollY / 300);
    scrollHint.style.opacity = String(opacity);
  }, { passive: true });
}

// ── Scroll reveal ──

const revealEls = document.querySelectorAll(".reveal-up");

function updateReveal() {
  const windowBottom = window.innerHeight + window.scrollY;
  revealEls.forEach((el) => {
    const top = el.getBoundingClientRect().top + window.scrollY;
    if (windowBottom > top + 40) {
      el.classList.add("is-visible");
    }
  });
}

window.addEventListener("scroll", updateReveal, { passive: true });
updateReveal();

// ── Stat counter animation ──

const statValues = document.querySelectorAll(".stat-value[data-count]");
let statsAnimated = false;

function animateStats() {
  if (statsAnimated) return;
  const statsSection = document.querySelector(".stats");
  if (!statsSection) return;
  const rect = statsSection.getBoundingClientRect();
  if (rect.top < window.innerHeight - 100) {
    statsAnimated = true;
    statValues.forEach((el) => {
      const target = parseFloat(el.dataset.count);
      const suffix = target % 1 !== 0 ? "" : "";
      const decimals = target % 1 !== 0 ? 1 : 0;
      const duration = 1400;
      const start = performance.now();

      function tick(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = target * eased;
        el.textContent = current.toFixed(decimals);
        if (progress < 1) requestAnimationFrame(tick);
        else el.textContent = target.toFixed(decimals);
      }

      requestAnimationFrame(tick);
    });
  }
}

window.addEventListener("scroll", animateStats, { passive: true });
animateStats();

// ── Popup system ──

const popupOverlay = document.getElementById("popup-overlay");
const popupBody = popupOverlay.querySelector(".popup-body");
const popupClose = popupOverlay.querySelector(".popup-close");

const popupContent = {
  encryption: {
    title: "AES-256-GCM Encryption",
    body: `<p>Every object written to Nimbus Grid is encrypted with AES-256-GCM using a unique per-object data key. Those data keys are wrapped by a master key stored in a FIPS 140-2 Level 3 HSM.</p><p>Key rotation happens every 72 hours — a new data key is generated for each write after rotation. Old keys are never deleted; they remain available for reads until the object itself is deleted.</p><dl class="popup-stat"><dt>Algorithm</dt><dd>AES-256-GCM</dd><dt>Key rotation</dt><dd>Every 72 hours</dd><dt>HSM</dt><dd>FIPS 140-2 Level 3</dd></dl>`,
  },
  residency: {
    title: "Data Residency Controls",
    body: `<p>Nimbus Grid enforces geographic data residency at the control plane. When you pin a storage pool to a region, the metadata service guarantees that no data-bearing requests are routed outside that region — not for replication, not for backup, not for maintenance.</p><p>Each region is a fully isolated deployment with its own control plane, metadata store, and object storage layer. Cross-region replication is opt-in only.</p><dl class="popup-stat"><dt>Available regions</dt><dd>14 globally</dd><dt>Isolation model</dt><dd>Per-region control plane</dd><dt>Compliance</dt><dd>SOC 2, ISO 27001, GDPR-ready</dd></dl>`,
  },
  throughput: {
    title: "Provisioned Throughput",
    body: `<p>Every storage pool gets dedicated provisioned IOPS and bandwidth. No noisy neighbours — your pool's capacity is reserved at the storage node level with strict quality-of-service enforcement.</p><p>Each pool includes 50% burst headroom above provisioned capacity for up to 30 minutes per day, giving you room for traffic spikes without over-provisioning.</p><dl class="popup-stat"><dt>Min provisioned IOPS</dt><dd>1,000 / pool</dd><dt>Max provisioned IOPS</dt><dd>100,000 / pool</dd><dt>Burst headroom</dt><dd>50% for 30 min/day</dd></dl>`,
  },
  audit: {
    title: "Immutable Audit Trail",
    body: `<p>Every read, write, list, and permission change is recorded in an append-only ledger with cryptographic chaining. Each entry is hashed and linked to the previous entry — tampering with any record invalidates the chain.</p><p>Audit trails stream to your SIEM in real time over gRPC with structured JSON payloads. Retention is configurable from 7 days to unlimited.</p><dl class="popup-stat"><dt>Format</dt><dd>JSON over gRPC stream</dd><dt>Chaining</dt><dd>SHA-256 hash chain</dd><dt>Export targets</dt><dd>Splunk, Datadog, Elastic, S3</dd></dl>`,
  },
  contact: {
    title: "Contact Enterprise Sales",
    body: `<p>Our enterprise team works with you to design a storage topology that matches your compliance requirements, performance targets, and budget. We typically respond within one business day.</p><p>Enterprise plans include dedicated support engineers, custom SLAs, on-premise gateways, and bring-your-own-key encryption.</p><form class="popup-form" onsubmit="event.preventDefault(); this.innerHTML='<p style=color:var(--accent-2)>Thanks! We&rsquo;ll reach out within 24 hours.</p>'"><label class="popup-label" for="contact-email">Work email</label><input id="contact-email" type="email" class="popup-input" placeholder="you@company.com" required /><button type="submit" class="popup-submit">Send</button></form>`,
  },
};

function openPopup(key) {
  const data = popupContent[key];
  if (!data) return;
  popupBody.innerHTML = `<h3>${data.title}</h3>${data.body}`;
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
popupOverlay.addEventListener("click", (e) => {
  if (e.target === popupOverlay) closePopup();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && popupOverlay.classList.contains("is-open")) closePopup();
});

document.querySelectorAll("[data-popup]").forEach((el) => {
  el.addEventListener("click", (e) => {
    e.preventDefault();
    openPopup(el.dataset.popup);
  });
});

// ── Smooth scroll for anchor links inside nav ──

document.querySelectorAll('.primary-nav a[href^="#"]').forEach((link) => {
  link.addEventListener("click", (e) => {
    e.preventDefault();
    const target = document.querySelector(link.getAttribute("href"));
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
});

// ═══════════════════════════════════════════════════
//  AgentOS Integration
// ═══════════════════════════════════════════════════

const AGENTOS_HOST = window.location.hostname === "localhost"
  ? "localhost:8420"
  : window.location.host;

const feedLog = document.getElementById("feed-log");
const feedStatusText = document.getElementById("feed-status-text");
const feedDot = document.querySelector(".feed-dot");
const feedMeta = document.getElementById("feed-meta");
const consoleOutput = document.getElementById("console-output");
const consoleInput = document.getElementById("console-input");
const consoleForm = document.getElementById("console-form");

let lastEventCount = 0;
let pollTimer = null;

function addFeedEntry(tag, tagClass, sender, msg, time) {
  if (!feedLog) return;
  const placeholder = feedLog.querySelector(".feed-placeholder");
  if (placeholder) placeholder.remove();

  const entry = document.createElement("div");
  entry.className = "feed-entry";
  const t = time ? new Date(time).toLocaleTimeString("en-US", { hour12: false }) : new Date().toLocaleTimeString("en-US", { hour12: false });
  entry.innerHTML = `
    <span class="feed-tag ${tagClass}">${tag}</span>
    <span class="feed-time">${t}</span>
    <span class="feed-msg"><span class="agent-name">${sender}</span> ${msg}</span>
  `;
  feedLog.prepend(entry);
  while (feedLog.children.length > 100) feedLog.lastChild.remove();
}

function appendConsole(text, cls = "") {
  if (!consoleOutput) return;
  const pre = document.createElement("pre");
  pre.className = "console-text";
  pre.innerHTML = text;
  if (cls) pre.classList.add(cls);
  consoleOutput.appendChild(pre);
  consoleOutput.scrollTop = consoleOutput.scrollHeight;
}

function setConnected(online) {
  if (feedStatusText) feedStatusText.textContent = online ? "Connected" : "Offline";
  if (feedDot) feedDot.classList.toggle("disconnected", !online);
  if (feedMeta) feedMeta.textContent = "AgentOS v0.1";
}

async function pollEvents() {
  try {
    const resp = await fetch(`/api/events/history?room=grid-ops&limit=60`);
    const events = await resp.json();
    if (events.length > lastEventCount) {
      for (let i = lastEventCount; i < events.length; i++) {
        const msg = events[i];
        const tagMap = {
          agent_online: ["ONLINE", "agent-online"], pool_created: ["POOL", "storage"],
          storage_allocated: ["STORAGE", "storage"], health_report: ["HEALTH", "monitor"],
          node_alert: ["ALERT", "alert"], security_scan: ["SECURITY", "security"],
          txn_committed: ["TXN", "txn"], console_command: ["CMD", "console"],
          status_report: ["STATUS", "monitor"],
        };
        const [tag, tagClass] = tagMap[msg.event_type] || [msg.event_type?.toUpperCase() || "EVENT", "console"];
        addFeedEntry(tag, tagClass, msg.sender, msg.content, msg.timestamp);
      }
      lastEventCount = events.length;
    }
    setConnected(true);
  } catch (e) {
    setConnected(false);
  }
}

async function initConsole() {
  appendConsole('<span class="output success">Connected to AgentOS v0.1</span>');
  try {
    const resp = await fetch(`/api/console`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command: "status" }),
    });
    const data = await resp.json();
    appendConsole(data.output);
    appendConsole('<span class="output muted">Type a command below…</span>');
    setConnected(true);
  } catch (e) {
    setConnected(false);
    appendConsole('<span class="error">Backend unreachable. Is the server running?</span>', "error");
  }
}

async function sendCommand(cmd) {
  if (!cmd.trim()) return;
  appendConsole(`<span class="prompt">$</span> ${cmd}`);
  try {
    const resp = await fetch(`/api/console`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command: cmd }),
    });
    const data = await resp.json();
    const isError = data.output.toLowerCase().includes("error") || data.output.toLowerCase().includes("fail");
    appendConsole(data.output, isError ? "error" : "success");
  } catch (e) {
    appendConsole("Error: AgentOS backend not reachable.", "error");
  }
}

if (consoleForm) {
  consoleForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const cmd = consoleInput.value.trim();
    if (cmd) { sendCommand(cmd); consoleInput.value = ""; }
  });
}

initConsole();
pollEvents();
pollTimer = setInterval(pollEvents, 3000);

async function refreshApiTab() {
  try {
    const resp = await fetch(`/api/state`);
    const state = await resp.json();
    const apiPane = document.querySelector('[data-pane="1"]');
    if (apiPane && state.total_nodes > 0) {
      apiPane.innerHTML = `<pre class="console-text"><span class="prompt">GET</span> /api/state
{
  "<span class="val">total_nodes</span>": <span class="val">${state.total_nodes}</span>,
  "<span class="val">online_nodes</span>": <span class="val">${state.online_nodes}</span>,
  "<span class="val">total_pools</span>": <span class="val">${state.total_pools}</span>,
  "<span class="val">capacity_tb</span>": <span class="val">${state.total_capacity_tb.toFixed(0)}</span>,
  "<span class="val">used_tb</span>": <span class="val">${state.total_used_tb.toFixed(1)}</span>,
  "<span class="val">active_txns</span>": <span class="val">${state.active_transactions}</span>,
  "<span class="val">chain_verified</span>": <span class="val">${state.chain_verified}</span>,
  "<span class="val">regions</span>": [${state.regions.map(r => `"${r}"`).join(", ")}]
}</pre>`;
    }
  } catch (e) { /* offline */ }
}

setInterval(refreshApiTab, 10000);
refreshApiTab();
