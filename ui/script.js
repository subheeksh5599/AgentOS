// ═══════════════════════════════════════════════════
//  AgentOS — loader · Lenis · GSAP · cursor · WebGL
// ═══════════════════════════════════════════════════

gsap.registerPlugin(ScrollTrigger);

// ═══ Loader ═══
(function loaderSequence() {
  const loader = document.querySelector(".loader");
  const progress = document.querySelector(".loader-progress");
  const nodes = document.querySelectorAll(".lnode");
  if (!loader || !progress) return;

  let p = 0;
  const total = 45; // frames to complete
  const interval = setInterval(() => {
    p++;
    progress.style.transform = `translateX(${Math.min((p / total) * 100, 100) - 100}%)`;
    if (p >= total * 0.25) nodes[0].classList.add("active");
    if (p >= total * 0.50) nodes[1].classList.add("active");
    if (p >= total * 0.75) nodes[2].classList.add("active");

    if (p >= total) {
      clearInterval(interval);
      nodes[3].classList.add("active");
      gsap.to(loader, { opacity: 0, duration: 0.5, onComplete: () => {
        loader.style.display = "none";
        document.body.classList.remove("loading");
        initLenis();
        initScrollTriggers();
        initCursor();
        initHeroShader();
        initAgentCanvases();
        initDeployCanvas();
      }});
    }
  }, 45);
})();

// ═══ Lenis ═══
function initLenis() {
  const lenis = new Lenis({ duration: 1.2, easing: t => Math.min(1, 1.001 - Math.pow(2, -10 * t)) });
  lenis.on("scroll", ScrollTrigger.update);
  gsap.ticker.add(time => lenis.raf(time * 1000));
  gsap.ticker.lagSmoothing(0);
  window.lenis = lenis;
}

// ═══ Scroll animations ═══
function initScrollTriggers() {
  document.querySelectorAll("[data-reveal]").forEach(el => {
    gsap.to(el, {
      scrollTrigger: { trigger: el, start: "top 85%", toggleActions: "play none none none" },
      opacity: 1, y: 0, duration: 1, ease: "power2.out",
    });
  });

  // Hero scroll hint fade
  gsap.to(".hero-scroll", {
    scrollTrigger: { trigger: ".hero", start: "top top", end: "bottom top", scrub: true },
    opacity: 0, y: 20,
  });

  // Work cards hover parallax
  document.querySelectorAll(".work-card[data-scrub]").forEach(card => {
    const visual = card.querySelector(".work-visual");
    gsap.fromTo(visual, { y: 0 }, {
      y: -20,
      scrollTrigger: { trigger: card, start: "top bottom", end: "bottom top", scrub: true },
    });
  });

  // Pipeline steps stagger
  gsap.fromTo(".pstep", { opacity: 0, x: -20 }, {
    opacity: 1, x: 0, duration: 0.7, stagger: 0.1, ease: "power2.out",
    scrollTrigger: { trigger: ".pipe-steps", start: "top 80%" },
  });

  // Stack items
  gsap.fromTo(".stack-item", { opacity: 0, y: 24 }, {
    opacity: 1, y: 0, duration: 0.6, stagger: 0.05, ease: "power2.out",
    scrollTrigger: { trigger: ".stack-grid", start: "top 82%" },
  });
}

// ═══ Custom cursor ═══
function initCursor() {
  const el = document.querySelector(".cursor");
  if (!el || window.matchMedia("(pointer: coarse)").matches) return;

  let x = 0, y = 0, cx = 0, cy = 0;
  document.addEventListener("pointermove", e => { x = e.clientX; y = e.clientY; el.classList.add("visible"); });
  document.addEventListener("pointerleave", () => el.classList.remove("visible"));

  document.querySelectorAll("a, button, .df-btn, select, input").forEach(t => {
    t.addEventListener("pointerenter", () => el.classList.add("hover"));
    t.addEventListener("pointerleave", () => el.classList.remove("hover"));
  });

  function tick() {
    cx += (x - cx) * 0.12;
    cy += (y - cy) * 0.12;
    el.style.left = cx + "px";
    el.style.top = cy + "px";
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

// ═══ Hero WebGL shader ═══
function initHeroShader() {
  const canvas = document.getElementById("hero-canvas");
  if (!canvas) return;
  canvas.width = canvas.offsetWidth;
  canvas.height = canvas.offsetHeight;

  const gl = canvas.getContext("webgl2", { alpha: true });
  if (!gl) return;

  const vs = gl.createShader(gl.VERTEX_SHADER);
  gl.shaderSource(vs, `#version 300 es
    in vec2 p;
    out vec2 uv;
    void main(){ uv=p*0.5+0.5; gl_Position=vec4(p,0,1); }`);
  gl.compileShader(vs);

  const fs = gl.createShader(gl.FRAGMENT_SHADER);
  gl.shaderSource(fs, `#version 300 es
    precision highp float;
    in vec2 uv;
    uniform vec2 r;
    uniform float t;
    out vec4 c;
    float h(vec2 p){ return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }
    float n(vec2 p){ vec2 i=floor(p),f=fract(p); f=f*f*(3.-2.*f); return mix(mix(h(i),h(i+vec2(1,0)),f.x),mix(h(i+vec2(0,1)),h(i+vec2(1,1)),f.x),f.y); }
    float fbm(vec2 p){ float v=0.,a=.5; for(int i=0;i<5;i++){ v+=a*n(p); p*=2.; a*=.5; } return v; }
    void main(){
      vec2 p=uv*2.5; p.x+=t*.04; p.y+=t*.03;
      float n1=fbm(p), n2=fbm(p+vec2(2.3,.7)+t*.02);
      float r2=n1*.08, g=n1*.12+n2*.06, b2=n1*.18+n2*.1;
      float alpha=smoothstep(0.,.8,n1)*.25;
      c=vec4(r2,g,b2,alpha);
    }`);
  gl.compileShader(fs);

  const prog = gl.createProgram();
  gl.attachShader(prog, vs); gl.attachShader(prog, fs); gl.linkProgram(prog);

  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]), gl.STATIC_DRAW);

  const aPos = gl.getAttribLocation(prog, "p");
  const uRes = gl.getUniformLocation(prog, "r");
  const uTime = gl.getUniformLocation(prog, "t");
  gl.useProgram(prog);
  gl.enableVertexAttribArray(aPos);
  gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);

  function render(time) {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    if (canvas.width !== w) canvas.width = w;
    if (canvas.height !== h) canvas.height = h;
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.uniform2f(uRes, canvas.width, canvas.height);
    gl.uniform1f(uTime, time * 0.001);
    gl.drawArrays(gl.TRIANGLES, 0, 6);
    requestAnimationFrame(render);
  }
  requestAnimationFrame(render);
}

// ═══ Agent card canvases ═══
function initAgentCanvases() {
  document.querySelectorAll(".wc-canvas").forEach(canvas => {
    const agent = canvas.dataset.agent;
    canvas.width = canvas.offsetWidth || 400;
    canvas.height = canvas.offsetHeight || 480;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const colors = { yield: ["#ff3b3b","#ff6b6b","#cc0000"], trader: ["#ff3b3b","#ff8c3b","#cc3300"], prediction: ["#ff3b3b","#ff3b8c","#990033"] };
    const palette = colors[agent] || colors.yield;
    const particles = [];

    for (let i = 0; i < 80; i++) {
      particles.push({
        x: Math.random() * canvas.width, y: Math.random() * canvas.height,
        r: Math.random() * 2 + 0.5, vx: (Math.random() - 0.5) * 0.4, vy: (Math.random() - 0.5) * 0.4,
        color: palette[Math.floor(Math.random() * palette.length)],
      });
    }

    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.globalAlpha = 0.6;
      particles.forEach(p => {
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.fill();

        // connections
        particles.forEach(p2 => {
          const d = Math.hypot(p.x - p2.x, p.y - p2.y);
          if (d < 60) { ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(p2.x, p2.y); ctx.strokeStyle = p.color; ctx.globalAlpha = 0.04; ctx.stroke(); ctx.globalAlpha = 0.6; }
        });

        p.x += p.vx; p.y += p.vy;
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;
      });
      requestAnimationFrame(draw);
    }
    requestAnimationFrame(draw);
  });
}

// ═══ Deploy section canvas ═══
function initDeployCanvas() {
  const canvas = document.getElementById("deploy-canvas");
  if (!canvas) return;
  canvas.width = canvas.offsetWidth;
  canvas.height = canvas.offsetHeight;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const nodes = [];
  for (let i = 0; i < 30; i++) {
    nodes.push({ x: Math.random() * canvas.width, y: Math.random() * canvas.height, r: 3 + Math.random() * 4, pulse: Math.random() * Math.PI * 2 });
  }

  function draw(time) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    nodes.forEach(n => {
      const s = 1 + Math.sin(time * 0.002 + n.pulse) * 0.3;
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r * s, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(255,59,59,0.3)";
      ctx.fill();
    });
    // connecting lines
    nodes.slice(0, 12).forEach((a, i) => {
      if (i + 1 < 12) {
        ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(nodes[i + 1].x, nodes[i + 1].y);
        ctx.strokeStyle = "rgba(255,59,59,0.06)"; ctx.stroke();
      }
    });
    requestAnimationFrame(draw);
  }
  requestAnimationFrame(draw);
}

// ═══ Nav scroll behavior ═══
window.addEventListener("scroll", () => {
  const nav = document.querySelector(".nav");
  if (nav) {
    nav.style.borderBottom = window.scrollY > 40 ? "1px solid rgba(255,255,255,0.06)" : "1px solid transparent";
  }
}, { passive: true });
