// ─── SMOOTH SCROLL ───
var lenis = new Lenis({ duration: 1.3, easing: function(t) { return Math.min(1, 1.001 - Math.pow(2, -10 * t)); } });
function raf(time) { lenis.raf(time); requestAnimationFrame(raf); }
requestAnimationFrame(raf);

// ─── LOADER ───
setTimeout(function() { var l = document.querySelector("#loader"); if (l) l.style.top = "-100%"; }, 4000);

// ─── MENU TOGGLE ───
(function() {
    var menu = document.querySelector("#menu");
    var full = document.querySelector("#full-scr");
    if (!menu || !full) return;
    var flag = 0;
    menu.addEventListener("click", function() {
        flag === 0 ? (full.style.top = 0, flag = 1) : (full.style.top = "-100%", flag = 0);
    });
    // Close menu when clicking a link
    document.querySelectorAll("#full-div1 a").forEach(function(a) {
        a.addEventListener("click", function() { full.style.top = "-100%"; flag = 0; });
    });
})();

// ── SMOOTH SCROLL FOR ANCHOR LINKS ──
document.querySelectorAll('a[href^="#"]').forEach(function(a) {
    a.addEventListener("click", function(e) {
        var target = document.querySelector(this.getAttribute("href"));
        if (target) {
            e.preventDefault();
            lenis.scrollTo(target, { offset: 0, duration: 1.5 });
        }
    });
});

// ─── PROJECT HOVER IMAGES ───
(function() {
    var elemC = document.querySelector("#elem-container");
    var fixed = document.querySelector("#fixed-image");
    if (!elemC || !fixed) return;
    elemC.addEventListener("mouseenter", function() { fixed.style.display = "block"; });
    elemC.addEventListener("mouseleave", function() { fixed.style.display = "none"; });
    elemC.addEventListener("mousemove", function(e) {
        gsap.to(fixed, { x: e.clientX, y: e.clientY, duration: 0.4, ease: "power3.out" });
    });
    document.querySelectorAll(".elem").forEach(function(el) {
        el.addEventListener("mouseenter", function() {
            fixed.style.backgroundImage = "url(" + el.getAttribute("data-image") + ")";
        });
    });
})();

// ─── SWIPER ───
(function() {
    var swiperEl = document.querySelector(".mySwiper");
    if (swiperEl) {
        new Swiper(".mySwiper", { slidesPerView: "auto", spaceBetween: 50, freeMode: true, grabCursor: true });
    }
})();

// ─── PAGE4 TABS ───
(function() {
    var tabs = document.querySelectorAll("#tabs h2");
    var img = document.querySelector("#page4-img");
    var desc = document.querySelector("#desc");
    if (!tabs.length || !img || !desc) return;
    var descs = {
        "Design": "The pipeline begins with fetching live on-chain state from Sui testnet RPC. Pools, order books, prediction markets, and wallet balances are queried in real-time using JSON-RPC.",
        "Project": "Structured context is sent to Groq's llama-3.3-70b-versatile. The LLM returns a JSON decision with action, amount, pool, confidence, and reasoning — all structured for validation.",
        "Execution": "Valid decisions are packaged into a Programmable Transaction Block and submitted on-chain. Gas is sponsored — the agent pays nothing for transaction execution.",
        "Guard": "Every decision — action, reasoning, confidence, timestamp — is uploaded to Walrus as a content-addressed blob. Immutable, verifiable, permanent audit trail."
    };
    tabs.forEach(function(tab) {
        tab.addEventListener("click", function() {
            tabs.forEach(function(t) { t.querySelector("a").style.color = "#504A45"; });
            tab.querySelector("a").style.color = "#EFEAE3";
            img.src = tab.getAttribute("data-img");
            desc.textContent = descs[tab.id] || desc.textContent;
        });
    });
})();
