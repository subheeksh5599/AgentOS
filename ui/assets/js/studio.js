// ─── SMOOTH SCROLL ───
const lenis = new Lenis({ duration: 1.3, easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)) });
function raf(time) { lenis.raf(time); requestAnimationFrame(raf); }
requestAnimationFrame(raf);

// ─── LOADER ───
setTimeout(function () { document.querySelector("#loader").style.top = "-100%"; }, 4000);

// ─── MENU ───
(function () {
    var menu = document.querySelector("#menu");
    var full = document.querySelector("#full-scr");
    var flag = 0;
    menu.addEventListener("click", function () {
        flag === 0 ? (full.style.top = 0, flag = 1) : (full.style.top = "-100%", flag = 0);
    });
})();

// ─── PROJECT HOVER IMAGES ───
(function () {
    var elemC = document.querySelector("#elem-container");
    var fixed = document.querySelector("#fixed-image");
    if (!elemC || !fixed) return;
    elemC.addEventListener("mouseenter", function () { fixed.style.display = "block"; });
    elemC.addEventListener("mouseleave", function () { fixed.style.display = "none"; });
    elemC.addEventListener("mousemove", function (e) {
        gsap.to(fixed, { x: e.clientX, y: e.clientY, duration: 0.4, ease: "power3.out" });
    });
    document.querySelectorAll(".elem").forEach(function (el) {
        el.addEventListener("mouseenter", function () {
            fixed.style.backgroundImage = "url(" + el.getAttribute("data-image") + ")";
        });
    });
})();

// ─── SWIPER ───
(function () {
    new Swiper(".mySwiper", {
        slidesPerView: "auto", spaceBetween: 50, freeMode: true, grabCursor: true,
    });
})();

// ─── PAGE4 TABS ───
(function () {
    var tabs = document.querySelectorAll("#tabs h2");
    var img = document.querySelector("#page4-img");
    var desc = document.querySelector("#desc");
    var descs = {
        "Design": "The AgentOS pipeline begins with fetching live on-chain state from Sui testnet RPC. Pools, order books, prediction markets, and wallet balances are queried in real-time.",
        "Project": "Structured context is sent to Groq's llama-3.3-70b-versatile model. The LLM returns a JSON decision with action, amount, pool, confidence, and reasoning.",
        "Execution": "Valid decisions are packaged into a Programmable Transaction Block and submitted on-chain. Gas is sponsored — the agent pays nothing.",
        "Guard": "Every decision — action, reasoning, confidence, timestamp — is uploaded to Walrus as a content-addressed blob. Immutable, verifiable, permanent."
    };
    tabs.forEach(function (tab) {
        tab.addEventListener("click", function () {
            tabs.forEach(function (t) { t.querySelector("a").style.color = "#504A45"; });
            tab.querySelector("a").style.color = "#EFEAE3";
            img.src = tab.getAttribute("data-img");
            desc.textContent = descs[tab.id] || desc.textContent;
        });
    });
})();

// ─── BACKEND INTEGRATION ───
var API = window.location.origin;

function fmtTime(iso) {
    var d = new Date(iso);
    return d.toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function iconForType(t) {
    if (t === "yield") return "\u{1F4B0}";
    if (t === "trader") return "\u{1F4C8}";
    if (t === "prediction") return "\u{1F3AF}";
    return "\u{1F916}";
}

function createCard(ev) {
    var d = document.createElement("div");
    d.className = "feed-card";
    var typeClass = ev.agent_type || "";
    d.innerHTML =
        '<div class="fc-header">' +
        '<span class="fc-agent">' + iconForType(ev.agent_type) + " " + (ev.agent_name || ev.agent_type || "unknown") + "</span>" +
        '<span class="fc-type ' + typeClass + '">' + (ev.event_type || "") + "</span>" +
        "</div>" +
        '<div class="fc-summary">' + (ev.summary || "No summary") + "</div>" +
        '<div class="fc-detail">' +
        (ev.details && ev.details.action ? "<span>Action: " + ev.details.action + "</span>" : "") +
        (ev.details && ev.details.confidence ? "<span>Confidence: " + (ev.details.confidence * 100).toFixed(0) + "%</span>" : "") +
        (ev.details && ev.details.amount ? "<span>Amount: " + ev.details.amount + "</span>" : "") +
        (ev.walrus_blob_id ? "<span>Walrus: " + ev.walrus_blob_id.substring(0, 12) + "...</span>" : "") +
        (ev.txn_digest ? "<span>TXN: " + ev.txn_digest.substring(0, 10) + "...</span>" : "") +
        "</div>" +
        '<div class="fc-time">' + fmtTime(ev.timestamp) + "</div>";
    return d;
}

function renderFeed(events) {
    var container = document.getElementById("feed-container");
    if (!container) return;
    container.innerHTML = "";
    if (!events || events.length === 0) {
        container.innerHTML = '<div class="feed-card empty">No agent events yet. Agents are starting up...</div>';
        return;
    }
    for (var i = events.length - 1; i >= 0; i--) {
        container.appendChild(createCard(events[i]));
    }
}

var feedEvents = [];
var maxFeed = 30;

function addEvent(ev) {
    var dup = feedEvents.find(function (e) { return e.timestamp === ev.timestamp && e.summary === ev.summary; });
    if (dup) return;
    feedEvents.push(ev);
    if (feedEvents.length > maxFeed) feedEvents.shift();
    renderFeed(feedEvents);
}

function connectSSE() {
    try {
        var sse = new EventSource(API + "/api/runtime/events");
        sse.onmessage = function (e) {
            try {
                var ev = JSON.parse(e.data);
                if (ev && ev.event_type && ev.event_type !== "heartbeat") addEvent(ev);
            } catch (_) {}
        };
        sse.onerror = function () { sse.close(); setTimeout(connectSSE, 5000); };
    } catch (_) { setTimeout(connectSSE, 3000); }
}

function fetchHistory() {
    fetch(API + "/api/runtime/history?limit=20")
        .then(function (r) { return r.json(); })
        .then(function (events) { renderFeed(events); feedEvents = events || []; })
        .catch(function () {});
}

function fetchAgents() {
    fetch(API + "/api/runtime/agents")
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var heroStatus = document.getElementById("hero-status");
            var agentBar = document.getElementById("agent-bar");
            if (!data || !data.agents) return;
            var names = Object.keys(data.agents);
            var count = names.length;
            if (heroStatus) heroStatus.innerHTML = '<span class="dot"></span>' + count + " Agent" + (count !== 1 ? "s" : "") + " Live — " + (data.model || "Groq llama-3.3-70b");
            if (agentBar) {
                agentBar.innerHTML = "";
                names.forEach(function (name) {
                    var a = data.agents[name];
                    var chip = document.createElement("span");
                    chip.className = "agent-chip";
                    var color = a.type === "yield" ? "#10B981" : a.type === "trader" ? "#E63A1B" : "#3B82F6";
                    chip.innerHTML = '<span class="chip-dot" style="background:' + color + '"></span>' +
                        '<span class="chip-name">' + name + "</span>" +
                        '<span class="chip-interval">' + (a.interval_seconds || "?") + "s</span>";
                    agentBar.appendChild(chip);
                });
            }
        })
        .catch(function () {});
}

function fetchState() {
    fetch(API + "/api/health")
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data && data.service) console.log("Backend:", data.service, data.version);
        })
        .catch(function () {});
}

// Kick everything off
fetchState();
fetchAgents();
fetchHistory();
connectSSE();

// Poll for agent status every 30s
setInterval(fetchAgents, 30000);

// Remove placeholder on first real event
setTimeout(function () {
    if (feedEvents.length === 0) {
        document.getElementById("feed-container").innerHTML =
            '<div class="feed-card empty">Waiting for agent decisions... (agents run every 30-60 seconds)</div>';
    }
}, 8000);
