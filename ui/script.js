// ═══════════════════════════════════════════════════
//  AGENTOS editorial-interference
//  Scroll-driven hero shatter · reveals · deploy
// ═══════════════════════════════════════════════════

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

// ── Marquee double-up ──
const bleed = document.querySelector(".bleed-text");
if (bleed) { bleed.textContent = bleed.textContent.repeat(4); }
