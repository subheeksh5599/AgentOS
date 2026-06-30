# AgentOS — Operating System for On-Chain AI Agents

**An autonomous DeFi agent platform on Sui. Deploy agents with programmable guardrails, verifiable execution logs, and LLM-powered decision making.**

---

## Problem

DeFi is a 24/7 job. Normal users cannot:
- Monitor yield pools around the clock to rebalance optimally
- Scan order books in real-time for arbitrage opportunities  
- Apply Kelly criterion math to prediction market bets manually
- Trust that an automated strategy actually followed the rules

**Manual DeFi is exhausting. Autonomous DeFi with verifiable guardrails is the solution.**

## What AgentOS Does

AgentOS lets anyone deploy autonomous AI agents on Sui that:

| | |
|---|---|
| **Fetch** | Real on-chain state from Sui testnet RPC (balances, pools, epoch data) |
| **Reason** | Groq llama-3.3-70b analyzes the state and returns structured JSON decisions |
| **Guard** | On-chain guardrails (max TX, daily limit, allowed actions) prevent misbehavior |
| **Execute** | Valid decisions are submitted via sponsored Programmable Transaction Blocks |
| **Seal** | Every decision is logged immutably to Walrus as a content-addressed blob |

## Architecture

```
    ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
    │  Sui Testnet │────▶│  Python Agent │────▶│  Groq LLM   │
    │  RPC + Move  │     │  Runtime      │     │  (llama-3.3) │
    └─────────────┘     └──────┬────────┘     └─────────────┘
                               │
                    ┌──────────┼──────────┐
                    ▼          ▼          ▼
              ┌─────────┐ ┌───────┐ ┌──────────┐
              │ Walrus  │ │  SSE  │ │  Sui TX  │
              │ Logs    │ │ Feed  │ │ (PTB)    │
              └─────────┘ └───────┘ └──────────┘
```

## On-Chain Contracts (Sui Testnet)

| Module | Purpose |
|---|---|
| `agent_wallet` | Programmable wallet with guardrails (max TX, daily limit, action bitmap, pause/resume) |
| `agent_registry` | On-chain directory of all deployed agents with metadata |
| `agent_factory` | One-click deploy: creates wallet + registers agent in single TX |
| `action_log` | Immutable append-only audit trail with Walrus blob references |

**Package:** `0x8be6a574ed9711fc0815e5821358eeb9fd0b269c1c5aa399338c6da786c8f9de`

### Verifiable On-Chain Transactions

All operations submit real transactions on Sui testnet. Judges can verify every TX on SuiVision:

| Transaction | Digest | SuiVision |
|---|---|---|
| Package published (4 modules) | `HNwuoagayN7...` | [View](https://testnet.suivision.xyz/txblock/HNwuoagayN7YcMVSPWZ11dBAviejcF4XdG7SesZCcPpZ) |
| Agent deployed via factory | `5KdueWK7fWH...` | [View](https://testnet.suivision.xyz/txblock/5KdueWK7fWH9BaDXFq5kGLFYZ5dNR9cTuQuFxEan5qK) |
| Agent transfer (0.001 SUI) | `4ZA1G7A8btk...` | [View](https://testnet.suivision.xyz/txblock/4ZA1G7A8btk9iuLXgGJJGwt5jKMjSHiA6v7ppVPPUWGq) |
| Wallet created (AgentWallet) | `FQ1s56HMV1Z...` | [View](https://testnet.suivision.xyz/txblock/FQ1s56HMV1Zi3w2A1opAGzJqmxCq7htSjea4fgaPdvjt) |
| Agent deployed (AgentEntry) | `Hj7asve32xZk...` | [View](https://testnet.suivision.xyz/txblock/Hj7asve32xZkUhYFtBC82NuP6dHgP9FYHyKUVkAHq3Ge) |
| Real agent transfer | `qKgTLJhiyfqa...` | [View](https://testnet.suivision.xyz/txblock/qKgTLJhiyfqaUUxVK3LJGq2DbUY3spAKegSyPY9UWUS) |
| Factory deploy (Trader wallet) | `Gk55eX6NbJA...` | [View](https://testnet.suivision.xyz/txblock/Gk55eX6NbJAevwm25zw6ttVEVNCcHt72uoB3DfVqzSNq) |

**Wallet:** `0xfc7567d27098037e971f8d4d4c06a96f4ea51cf5da0149e7429033446019503c` (0.87 SUI on testnet)

## Three Agent Types

### Yield Agent
Scans DeepBook LP pools. Rebalances when APR differential exceeds threshold. Auto-compounds rewards. Max 50% single-pool exposure.

### Trader Agent
Arbitrage across DeepBook Spot and Margin order books. Stop-loss and take-profit guardrails. Only executes when profit > fees.

### Prediction Agent  
Uses Kelly criterion to size bets on DeepBook Predict markets. Only bets when estimated probability exceeds market-implied by configurable edge threshold.

## Quick Start

```bash
# Install
cd agentos
uv sync

# Run (port 8420)
.venv/bin/python main.py
```

Open http://localhost:8420

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Service health |
| GET | `/api/runtime/agents` | Agent list with live chain data |
| GET | `/api/runtime/events` | SSE stream of agent decisions |
| GET | `/api/runtime/market` | SUI price from CoinGecko |
| GET | `/api/runtime/history` | Recent agent events |
| POST | `/api/runtime/agents/deploy` | Deploy a new agent |
| POST | `/api/runtime/agents/start` | Start a stopped agent |
| POST | `/api/runtime/agents/stop` | Stop a running agent |

## Pages

| Route | Description |
|---|---|
| `/` | Landing — live feed, pipeline, Sui stack |
| `/yield` | Yield agent — configure and deploy |
| `/trader` | Trader agent — with live SUI price |
| `/prediction` | Prediction agent — with Kelly calculator |
| `/dashboard` | Live monitor — SSE feed with start/stop |
| `/deploy` | Deploy form — connect wallet, configure guardrails |

## Tech Stack

- **Blockchain:** Sui Testnet (Move contracts, RPC, PTBs)
  - Package: [`0x8be6...f9de`](https://testnet.suivision.xyz/package/0x8be6a574ed9711fc0815e5821358eeb9fd0b269c1c5aa399338c6da786c8f9de)
  - Wallet: [`0xfc75...503c`](https://testnet.suivision.xyz/address/0xfc7567d27098037e971f8d4d4c06a96f4ea51cf5da0149e7429033446019503c)
  - Epoch 1146, 3.67B transactions
- **AI:** Groq API (llama-3.3-70b-versatile, json_object mode)  
- **Storage:** Walrus (content-addressed blob logs)
- **Market Data:** CoinGecko (real-time SUI price)
- **Backend:** FastAPI + Uvicorn (Python 3.12)
- **Frontend:** Vanilla JS with GSAP animations
- **Deployment:** Vercel (serverless) + local (persistent agents)


## License

Apache 2.0
