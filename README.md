# AgentOS — OS for On-Chain AI Agents

Move-based framework for deploying autonomous AI agents with Sui wallets, verifiable execution, and programmable guardrails.

## Stack

| Layer | What |
|-------|------|
| Contracts | Sui Move (7 modules) |
| Identity | zkLogin (Google OAuth → Sui address) |
| Execution | DeepBook Spot / Margin / Predict |
| Verifiability | Walrus (logs, config, model params) |
| Encryption | Seal (agent private keys at rest) |
| Gas | Sponsored TXs (gasless agent actions) |
| Atomicity | Programmable Transaction Blocks |
| Payments | Google AP2 (agent-to-agent) |
| Frontend | vanilla HTML/CSS/JS, Vite |
| Deploy | Vercel static + serverless API |

## Move Contracts

```
move/sources/
├── agent_registry.move      Agent discovery & metadata
├── agent_wallet.move        Wallet with programmable guardrails
├── agent_factory.move       1-click deploy in a PTB
├── action_log.move          Verifiable audit trail → Walrus
└── examples/
    ├── yield_agent.move     DeepBook LP optimization
    ├── trader_agent.move    Spot + Margin arbitrage
    └── prediction_agent.move   DeepBook Predict markets
```

## 3 Example Agents

**Yield Agent** — scans DeepBook pools for best APR, rebalances daily, auto-compounds.

**Trader Agent** — arbitrage across Spot + Margin, stop-loss/take-profit, pair whitelisting.

**Prediction Agent** — trades DeepBook Predict markets using Kelly criterion sizing, edge detection.

## 30-Second Demo

1. Login via Google (zkLogin)
2. Deploy a Yield Agent with 1 click
3. Agent finds best DeepBook yields, rebalances daily
4. All actions verifiable on Walrus

## Why It Wins

1. Dev tooling × AI agents — sell shovels in the fastest-growing category
2. Nobody's built the agent OS yet. First mover.
3. Naturally viral — developers become evangelists
4. 3 demo-ready agents covering Spot, Margin, Predict
5. First to build on DeepBook Predict (launched May 2026)

## Sui Primitives Used

| Primitive | Use |
|-----------|-----|
| Walrus | Verifiable agent memory, logs, model configs |
| Seal | Encrypted agent state + private keys |
| DeepBook | Spot, Margin, Predict — shared liquidity |
| zkLogin | Agent identity tied to real users |
| Sponsored TXs | Gasless autonomous agent actions |
| PTBs | Atomic multi-step strategies |
| Google AP2 | Agent-to-agent payments |

## Run Locally

```bash
cd ui && npm install && npm run build && cd ..
uv venv && uv pip install -r requirements.txt
source .venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8420
```

## Deploy

```bash
vercel --prod
```

Live at [agentos-sepia.vercel.app](https://agentos-sepia.vercel.app)

Built for Sui Agentathon 2026.
