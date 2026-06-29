// ── WebGL Shader Background ──
const canvas = document.getElementById("shader");
if (canvas) {
  canvas.width = 1422; canvas.height = 800;
  const gl = canvas.getContext("webgl", { alpha: true, antialias: false });
  if (gl) {
    const vs = gl.createShader(gl.VERTEX_SHADER);
    gl.shaderSource(vs, "attribute vec2 p;void main(){gl_Position=vec4(p,0,1);}");
    gl.compileShader(vs);
    const fs = gl.createShader(gl.FRAGMENT_SHADER);
    gl.shaderSource(fs, `precision highp float;uniform vec2 r;uniform float t;
float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float n(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(h(i),h(i+vec2(1,0)),f.x),mix(h(i+vec2(0,1)),h(i+vec2(1,1)),f.x),f.y);}
float fbm(vec2 p){float v=0.,a=.5;for(int i=0;i<5;i++){v+=a*n(p);p*=2.;a*=.5;}return v;}
void main(){vec2 uv=gl_FragCoord.xy/r;vec2 p=uv*3.5;p.x+=t*.06;p.y+=t*.04;
float n1=fbm(p),n2=fbm(p+vec2(3.7,1.2)+t*.03),n3=fbm(p*.6+vec2(t*.05,-t*.02));
float r2=n1*.12+n3*.06,g=n1*.18+n2*.1,b=n1*.3+n2*.15+n3*.08;
gl_FragColor=vec4(r2,g,b,smoothstep(0.,.7,n1)*.35+r2*.3);}`);
    gl.compileShader(fs);
    const prog = gl.createProgram();
    gl.attachShader(prog, vs); gl.attachShader(prog, fs); gl.linkProgram(prog);
    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]), gl.STATIC_DRAW);
    const aPos = gl.getAttribLocation(prog, "p");
    const uRes = gl.getUniformLocation(prog, "r");
    const uTime = gl.getUniformLocation(prog, "t");
    function render(time) {
      gl.viewport(0, 0, canvas.width, canvas.height);
      gl.useProgram(prog);
      gl.uniform2f(uRes, canvas.width, canvas.height);
      gl.uniform1f(uTime, time * 0.001);
      gl.bindBuffer(gl.ARRAY_BUFFER, buf);
      gl.enableVertexAttribArray(aPos);
      gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);
      gl.drawArrays(gl.TRIANGLES, 0, 6);
      requestAnimationFrame(render);
    }
    requestAnimationFrame(render);
  }
}

// ── Login Modal ──
function toggleLogin() {
  document.getElementById("login-modal").classList.toggle("is-open");
  document.getElementById("login-modal").setAttribute("aria-hidden",
    document.getElementById("login-modal").classList.contains("is-open") ? "false" : "true");
}

function handleZkLogin() {
  const btn = document.querySelector(".btn-google");
  btn.textContent = "Redirecting to Google…";
  btn.disabled = true;
  setTimeout(() => {
    document.getElementById("login-text").textContent = "0x7a9b…3f2c";
    document.getElementById("login-btn").classList.add("connected");
    document.querySelector(".login-icon").textContent = "●";
    toggleLogin();
    btn.textContent = "Sign in with Google (zkLogin)";
    btn.disabled = false;
  }, 1200);
}

function handleSuiWallet() {
  toggleLogin();
  document.getElementById("login-text").textContent = "0x7a9b…3f2c";
  document.getElementById("login-btn").classList.add("connected");
  document.querySelector(".login-icon").textContent = "●";
}

// ── Deploy ──
function scrollToDeploy() {
  document.getElementById("deploy").scrollIntoView({ behavior: "smooth" });
}

function deployAgent(type) {
  const names = { yield: "My Yield Agent", trader: "My Trader Agent", prediction: "My Prediction Agent" };
  document.getElementById("agent-type").value = type;
  document.getElementById("agent-name").value = names[type];
  document.getElementById("deploy").scrollIntoView({ behavior: "smooth" });
}

function handleDeploy() {
  const name = document.getElementById("agent-name").value;
  const type = document.getElementById("agent-type").value;
  const maxTx = document.getElementById("max-tx").value;
  const daily = document.getElementById("daily-limit").value;
  const fund = document.getElementById("initial-fund").value;

  const typeNames = { yield: "Yield Agent", trader: "Trader Agent", prediction: "Prediction Agent" };

  document.getElementById("success-details").innerHTML = `
    <strong>Agent:</strong> ${name}<br>
    <strong>Type:</strong> ${typeNames[type]}<br>
    <strong>Max TX:</strong> ${maxTx} SUI<br>
    <strong>Daily Limit:</strong> ${daily} SUI<br>
    <strong>Initial Funding:</strong> ${fund} SUI<br>
    <strong>TXN Hash:</strong> 0x${Array.from({length:64},()=>Math.random().toString(16)[2]).join('').slice(0,64)}<br>
    <strong>Walrus Blob:</strong> walrus://${Array.from({length:43},()=>Math.random().toString(16)[2]).join('').slice(0,43)}<br>
    <strong>Status:</strong> ✓ Deployed on Sui Testnet
  `;

  document.getElementById("success-modal").classList.add("is-open");

  // Simulate updating stats
  setTimeout(() => {
    const agentsEl = document.getElementById("stat-agents");
    if (agentsEl) agentsEl.textContent = String(Math.floor(Math.random() * 900 + 100));
    const volEl = document.getElementById("stat-volume");
    if (volEl) volEl.textContent = (Math.random() * 5 + 1).toFixed(1) + "M SUI";
  }, 500);
}

function closeSuccess() {
  document.getElementById("success-modal").classList.remove("is-open");
}

// ── Close modals on Escape ──
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    document.querySelectorAll(".modal-overlay.is-open").forEach(m => m.classList.remove("is-open"));
  }
});

document.querySelectorAll(".modal-overlay").forEach(overlay => {
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) overlay.classList.remove("is-open");
  });
});
