// ═══════════════════════════════════════════════════
//  AGENTOS cinematic-dark — loader · scramble · status strip · shader
// ═══════════════════════════════════════════════════

// ── Loader Ritual ──
(function initLoader() {
  const loader = document.getElementById("loader");
  const count = document.getElementById("loader-count");
  if (!loader || !count) return;
  let n = 0;
  const interval = setInterval(() => {
    n = Math.min(n + 1, 100);
    count.textContent = String(n).padStart(2, "0");
    if (n >= 100) {
      clearInterval(interval);
      setTimeout(() => {
        loader.classList.add("is-done");
        document.body.classList.remove("is-loading");
        if (window._initScramble) window._initScramble();
      }, 300);
    }
  }, 22);
})();

// ── Scramble Text ──
window._initScramble = function() {
  const CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?/0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  document.querySelectorAll(".scramble").forEach(el => {
    const target = el.dataset.text || el.textContent;
    if (el.dataset.scrambled === "done") return;
    el.dataset.scrambled = "done";
    let frame = 0;
    const maxFrames = 18;
    const iv = setInterval(() => {
      frame++;
      let result = "";
      for (let i = 0; i < target.length; i++) {
        if (frame > maxFrames - 4 || i < (frame / maxFrames) * target.length) {
          result += target[i];
        } else {
          result += CHARS[Math.floor(Math.random() * CHARS.length)];
        }
      }
      el.textContent = result;
      if (frame >= maxFrames) { el.textContent = target; clearInterval(iv); }
    }, 42);
  });
};

// ── System Status Strip ──
(function statusStrip() {
  const frameEl = document.getElementById("ss-frame");
  const scrollEl = document.getElementById("ss-scroll");
  const timeEl = document.getElementById("ss-time");
  let f = 0;
  function update() {
    f++;
    if (frameEl) frameEl.textContent = `FRAME ${String(f % 10000).padStart(4, "0")}`;
    if (scrollEl) {
      const pct = Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100) || 0;
      scrollEl.textContent = `SCROLL ${String(pct).padStart(2, "0")}%`;
    }
    if (timeEl) timeEl.textContent = `UTC ${new Date().toISOString().slice(11, 19)}`;
    requestAnimationFrame(update);
  }
  update();
})();

// ── WebGL Shader ──
(function initShader() {
  const canvas = document.getElementById("shader");
  if (!canvas) return;
  canvas.width = 1422; canvas.height = 800;
  const gl = canvas.getContext("webgl2", { alpha: true, antialias: false });
  if (!gl) return;
  const vs = gl.createShader(gl.VERTEX_SHADER);
  gl.shaderSource(vs, "#version 300 es\nin vec2 p;void main(){gl_Position=vec4(p,0,1);}");
  gl.compileShader(vs);
  const fs = gl.createShader(gl.FRAGMENT_SHADER);
  gl.shaderSource(fs, `#version 300 es\nprecision highp float;uniform vec2 r;uniform float t,u_scroll;out vec4 c;
float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float n(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(h(i),h(i+vec2(1,0)),f.x),mix(h(i+vec2(0,1)),h(i+vec2(1,1)),f.x),f.y);}
float fbm(vec2 p){float v=0.,a=.5;for(int i=0;i<5;i++){v+=a*n(p);p*=2.;a*=.5;}return v;}
void main(){vec2 uv=gl_FragCoord.xy/r;vec2 p=uv*3.5;p.x+=u_scroll*.2;p.y+=u_scroll*.1;
float n1=fbm(p),n2=fbm(p+vec2(3.7,1.2)+u_scroll*.03),n3=fbm(p*.6+vec2(u_scroll*.05,-u_scroll*.02));
float r2=n1*.12+n3*.06,g=n1*.18+n2*.1,b=n1*.3+n2*.15+n3*.08;
c=vec4(r2,g,b,smoothstep(0.,.7,n1)*.35+r2*.3);}`);
  gl.compileShader(fs);
  const prog = gl.createProgram();
  gl.attachShader(prog, vs); gl.attachShader(prog, fs); gl.linkProgram(prog);
  gl.useProgram(prog);
  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]), gl.STATIC_DRAW);
  const aPos = gl.getAttribLocation(prog, "p");
  const uRes = gl.getUniformLocation(prog, "r");
  const uTime = gl.getUniformLocation(prog, "t");
  const uScroll = gl.getUniformLocation(prog, "u_scroll");
  gl.enableVertexAttribArray(aPos);
  gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);
  function render(time) {
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.uniform2f(uRes, canvas.width, canvas.height);
    gl.uniform1f(uTime, time * 0.001);
    gl.uniform1f(uScroll, window.scrollY * 0.0005);
    gl.drawArrays(gl.TRIANGLES, 0, 6);
    requestAnimationFrame(render);
  }
  requestAnimationFrame(render);
})();

// ── Magnetic Buttons ──
document.querySelectorAll(".magnetic").forEach(btn => {
  btn.addEventListener("pointermove", e => {
    const rect = btn.getBoundingClientRect();
    const x = (e.clientX - rect.left - rect.width / 2) * 0.15;
    const y = (e.clientY - rect.top - rect.height / 2) * 0.15;
    btn.style.transform = `translate(${x}px, ${y}px)`;
  });
  btn.addEventListener("pointerleave", () => { btn.style.transform = "translate(0, 0)"; });
});

// ── Scroll Reveal ──
(function reveal() {
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add("is-visible"); obs.unobserve(e.target); } });
  }, { threshold: 0.15 });
  document.querySelectorAll(".reveal-up").forEach(el => obs.observe(el));
})();

// ── Scroll Hint ──
window.addEventListener("scroll", () => {
  const hint = document.getElementById("scroll-hint");
  if (hint) hint.style.opacity = String(Math.max(0, 1 - window.scrollY / 400));
}, { passive: true });

// ── zkLogin Modal ──
function toggleLogin() {
  const m = document.getElementById("login-modal");
  m.classList.toggle("is-open");
  m.setAttribute("aria-hidden", String(!m.classList.contains("is-open")));
}
function handleZkLogin() {
  const btn = document.querySelector(".btn-google");
  btn.textContent = "Redirecting to Google…"; btn.disabled = true;
  setTimeout(() => {
    document.getElementById("login-text").textContent = "0x7a9b…3f2c";
    document.getElementById("login-btn").classList.add("connected");
    document.querySelector(".login-icon").textContent = "●";
    toggleLogin();
    btn.textContent = "Sign in with Google (zkLogin)"; btn.disabled = false;
  }, 1200);
}
function handleSuiWallet() {
  toggleLogin();
  document.getElementById("login-text").textContent = "0x7a9b…3f2c";
  document.getElementById("login-btn").classList.add("connected");
  document.querySelector(".login-icon").textContent = "●";
}

// ── Deploy ──
function scrollToDeploy() { document.getElementById("deploy").scrollIntoView({ behavior: "smooth" }); }
function deployAgent(type) {
  const names = { yield: "Alpha Yield", trader: "Arb Hunter v2", prediction: "Prediction Scout" };
  document.getElementById("agent-type").value = type;
  document.getElementById("agent-name").value = names[type];
  scrollToDeploy();
}
function handleDeploy() {
  const name = document.getElementById("agent-name").value;
  const type = document.getElementById("agent-type").value;
  const maxTx = document.getElementById("max-tx").value;
  const daily = document.getElementById("daily-limit").value;
  const fund = document.getElementById("initial-fund").value;
  const typeNames = { yield: "Yield Agent", trader: "Trader Agent", prediction: "Prediction Agent" };
  document.getElementById("success-details").innerHTML = `
    Agent: ${name} | Type: ${typeNames[type]} | Max TX: ${maxTx} SUI | Daily Limit: ${daily} SUI | Initial: ${fund} SUI
    TXN: 0x${crypto.randomUUID().replace(/-/g,'')} | Status: ✓ Deployed on Sui Testnet`;
  document.getElementById("success-modal").classList.add("is-open");
}
function closeSuccess() { document.getElementById("success-modal").classList.remove("is-open"); }
document.addEventListener("keydown", e => { if (e.key === "Escape") document.querySelectorAll(".modal-overlay.is-open").forEach(m => m.classList.remove("is-open")); });
document.querySelectorAll(".modal-overlay").forEach(o => o.addEventListener("click", e => { if (e.target === o) o.classList.remove("is-open"); }));
