// Parse query params for pre-selecting agent type from landing page CTAs
const params = new URLSearchParams(window.location.search);
const typeParam = params.get("type");
if (typeParam && ["yield", "trader", "prediction"].includes(typeParam)) {
  document.getElementById("agent-type").value = typeParam;
  const names = { yield: "Alpha Yield", trader: "Arb Hunter v2", prediction: "Prediction Scout" };
  document.getElementById("agent-name").value = names[typeParam];
}

document.getElementById("deploy-btn").addEventListener("click", () => {
  const name = document.getElementById("agent-name").value || "Unnamed Agent";
  const type = document.getElementById("agent-type").value;
  const maxTx = document.getElementById("max-tx").value;
  const daily = document.getElementById("daily-limit").value;
  const fund = document.getElementById("initial-fund").value;
  const types = { yield: "Yield Agent", trader: "Trader Agent", prediction: "Prediction Agent" };

  document.getElementById("success-details").innerHTML = [
    `Agent: ${name}`,
    `Type: ${types[type]}`,
    `Max TX: ${maxTx} SUI`,
    `Daily limit: ${daily} SUI`,
    `Initial funding: ${fund} SUI`,
    `TXN: 0x${Array.from({ length: 64 }, () => Math.random().toString(16)[2]).join("").slice(0, 64)}`,
    `Status: Deployed on Sui Testnet`,
  ].join("<br>");

  document.getElementById("success-modal").classList.add("is-open");
});

document.addEventListener("keydown", e => {
  if (e.key === "Escape") document.querySelectorAll(".modal-overlay").forEach(m => m.classList.remove("is-open"));
});
document.querySelectorAll(".modal-overlay").forEach(o => {
  o.addEventListener("click", e => { if (e.target === o) o.classList.remove("is-open"); });
});
