// ═══════════════════════════════════════════════════
//  AGENTOS editorial-interference
//  Scroll-driven hero shatter · custom cursor · reveals
// ═══════════════════════════════════════════════════

// ── Custom cursor ──
const cursor = document.getElementById("cursor");
let mx = 0, my = 0, cx = 0, cy = 0;

document.addEventListener("pointermove", e => { mx = e.clientX; my = e.clientY; });

function animateCursor() {
  cx += (mx - cx) * 0.18;
  cy += (my - cy) * 0.18;
  if (cursor) cursor.style.transform = `translate(${cx - 14}px, ${cy - 14}px)`;
  requestAnimationFrame(animateCursor);
}
requestAnimationFrame(animateCursor);

document.querySelectorAll("a, button, .cta, input, select").forEach(el => {
  el.addEventListener("mouseenter", () => cursor?.classList.add("drag"));
  el.addEventListener("mouseleave", () => cursor?.classList.remove("drag"));
});
document.querySelectorAll(".strat, .prim, .pipe-step, .shard, .ishard, .image-shatter").forEach(el => {
  el.addEventListener("mouseenter", () => cursor?.classList.add("drag"));
  el.addEventListener("mouseleave", () => cursor?.classList.remove("drag"));
});

// ── Scroll-driven hero shatter ──
const heroShatter = document.getElementById("hero-shatter");
let shatterActive = false;
window.addEventListener("scroll", () => {
  const should = window.scrollY > 60;
  if (should !== shatterActive) {
    shatterActive = should;
    if (heroShatter) heroShatter.classList.toggle("shatter-active", should);
  }
}, { passive: true });

// ── Reveal observer ──
const revealObs = new IntersectionObserver(entries => {
  entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add("is-visible"); revealObs.unobserve(e.target); } });
}, { threshold: 0.12 });
document.querySelectorAll(".reveal").forEach(el => revealObs.observe(el));

// ── Deploy ──
function handleDeploy() {
  const name = document.getElementById("agent-name").value;
  const type = document.getElementById("agent-type").value;
  const maxTx = document.getElementById("max-tx").value;
  const daily = document.getElementById("daily-limit").value;
  const fund = document.getElementById("initial-fund").value;
  const types = { yield: "Yield Agent", trader: "Trader Agent", prediction: "Prediction Agent" };
  document.getElementById("success-details").innerHTML = `
    Agent: ${name} | Type: ${types[type]} | Max TX: ${maxTx} SUI | Daily: ${daily} SUI | Fund: ${fund} SUI
    TXN: 0x${Array.from({length:64},()=>Math.random().toString(16)[2]).join('').slice(0,64)}
    Status: ✓ Deployed on Sui Testnet`;
  document.getElementById("success-modal").classList.add("is-open");
}
document.addEventListener("keydown", e => { if (e.key === "Escape") document.querySelectorAll(".modal-overlay").forEach(m => m.classList.remove("is-open")); });
document.querySelectorAll(".modal-overlay").forEach(o => o.addEventListener("click", e => { if (e.target === o) o.classList.remove("is-open"); }));

// ── Marquee double-up ──
const bleed = document.querySelector(".bleed-text");
if (bleed) { bleed.textContent = bleed.textContent.repeat(4); }
