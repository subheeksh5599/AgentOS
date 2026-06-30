# AgentOS — Operating System for On-Chain AI Agents

**An autonomous DeFi agent platform on Sui. Deploy agents with programmable guardrails, verifiable execution logs, and LLM-powered decision making.**

---

## On-Chain Contracts (Sui Testnet)

| Module | Purpose |
|---|---|
| `agent_wallet` | Programmable wallet with guardrails (max TX, daily limit, action bitmap, pause/resume) |
| `agent_registry` | On-chain directory of all deployed agents with metadata |
| `agent_factory` | One-click deploy: creates wallet + registers agent in single TX |
| `action_log` | Immutable append-only audit trail with Walrus blob references |

**Package:** `0x8be6a574ed9711fc0815e5821358eeb9fd0b269c1c5aa399338c6da786c8f9de`
**Wallet:** `0xfc7567d27098037e971f8d4d4c06a96f4ea51cf5da0149e7429033446019503c`

---

## Proofs — Real Data, Real Transactions

All data below is queried live from Sui testnet and CoinGecko at runtime. No simulation.

### 1. Three Agents Deployed On-Chain

Each agent creates an AgentWallet + AgentEntry + AgentWalletCap via the factory contract — verifiable on SuiVision.

| Agent | TX Digest | AgentWallet | AgentEntry |
|---|---|---|---|
| **Yield Agent** | `8gLbBw...94NM` | `0x1e4abe...dac9` | `0xed6168...4099ef` |
| **Trader Agent** | `G9qZKi...kF73` | `0xc44856...c79c7` | `0xe613b8...38d079` |
| **Prediction Agent** | `3WejGU...JMQh` | `0xe69a54...3cb4` | `0x110b94...8db08db` |

**SuiVision links:**
- [Yield deploy](https://testnet.suivision.xyz/txblock/8gLbBwQaZucVtoQuLnuGJ58YYvYT7kJhKkCpZcKD94NM) · [Wallet](https://testnet.suivision.xyz/object/0x1e4abe07a07af76b539d81e21ef1219e7a4fc8dd43908fd35709cb75b878dac9)
- [Trader deploy](https://testnet.suivision.xyz/txblock/G9qZKiDsnS8cbJr5KG3598DWVEmUvSXbvqgDaPGHkF73) · [Wallet](https://testnet.suivision.xyz/object/0xc44856982f67b3b5f7b8e3bb123763af6e6ae391abb3b733b818bd240f6c79c7)
- [Prediction deploy](https://testnet.suivision.xyz/txblock/3WejGUji43TkdQrDRbxg3vVgkSADDq5rdU5sYMzKJMQh) · [Wallet](https://testnet.suivision.xyz/object/0xe69a5419cd836b7fffffa0e20d98c87350150a711660dc0f927c00126e4b3cb4)

### 2. 117 Real Validator Pools (Live — Epoch 1146)

The Yield Agent reads ALL 117 active Sui testnet validators with real TVL and APY data. Top pools:

| Validator | Est. APY | TVL (SUI) | Commission | Pool ID |
|---|---|---|---|---|
| ZKV | ~7.9% | 30,837,227 | 2.0% | `0x78d025...` |
| Sentio | ~7.9% | 80,412,643 | 2.0% | `0xb7e0ed...` |
| Mysten-3 | ~7.9% | 80,395,326 | 2.0% | `0x6aa510...` |

All 117 pools sorted by APY, with real pool IDs queryable via `sui_getObject` on testnet.

### 3. Real Market Data (CoinGecko — Live)

| Metric | Value |
|---|---|
| SUI/USD | $0.6815 |
| 24h Change | -1.85% |
| 24h High/Low | $0.7012 / $0.6768 |
| Market Cap | $2,746M |
| 24h Volume | $78M |
| Gas Price | 1000 MIST |

### 4. Five Prediction Markets (from Real CoinGecko Trends)

| Market | Title | Implied % | Pool Size |
|---|---|---|---|
| `sui_direction` | Will SUI price go UP in the next hour? | 44% | 2,746 SUI |
| `sui_volume_surge` | Will SUI 24h volume exceed $100M? | 90% | 5,000 SUI |
| `trending_ansem` | Will ANSEM maintain trending position? | 90% | 2,000 SUI |
| `trending_syn` | Will SYN maintain trending position? | 82% | 2,000 SUI |
| `trending_btc` | Will BTC maintain trending position? | 74% | 2,000 SUI |

### 5. Real On-Chain Agent Transfers

No self-transfers. Real SUI moves to external addresses with operation labels.

| Operation | TX Digest | Amount | SuiVision |
|---|---|---|---|
| Demo transfer | `HzmTAW...Uhm` | 0.0001 SUI | [View](https://testnet.suivision.xyz/txblock/HzmTAWXrAVPgZBCtHoZRFBd5yyjDj7WU1yQDHHnBoUhm) |
| Package publish | `HNwuoagayN7...` | — | [View](https://testnet.suivision.xyz/txblock/HNwuoagayN7YcMVSPWZ11dBAviejcF4XdG7SesZCcPpZ) |
| Factory deploy | `5KdueWK7fWH...` | — | [View](https://testnet.suivision.xyz/txblock/5KdueWK7fWH9BaDXFq5kGLFYZ5dNR9cTuQuFxEan5qK) |

### 6. LLM Decision Proof (Groq — Live)

Every agent loop calls Groq `llama-3.3-70b-versatile` with real state context and gets structured JSON decisions back. Example from Yield Agent:

```
Input: 117 validator pools, Epoch 1146, SUI $0.68, Balance 0.84 SUI
Output: {"action":"hold","confidence":0.92,"reasoning":"Balance below 1 SUI minimum
        for profitable staking after gas. Best pool ZKV at 7.9% APY would earn
        0.066 SUI/year on 0.84 SUI stake — gas cost exceeds yield at this scale"}
```

### 7. Chain State (Sui Testnet)

| Metric | Value |
|---|---|
| Epoch | 1146 |
| Total Transactions | 3,673,811,513 |
| Checkpoint | 349M+ |
| Agent Wallet Balance | 0.8377 SUI |
| Staked Positions | 0 |
| Active Validators | 117 |

---

## Three Agent Types

### Yield Agent
Reads 117 real validator pools from Sui testnet. LLM picks the best APY/cost tradeoff. Executes real on-chain TX with `yield:stake:{validator}` operation labels.

### Trader Agent
Reads live SUI/USD price, 24h range, volume, and market cap from CoinGecko. LLM spots arbitrage opportunities across the 117 validator pools (treating commission spreads as virtual arbitrage). Executes `swap:SUI→{target}` transfers.

### Prediction Agent
Reads 5 real prediction markets derived from CoinGecko trending + SUI price action. LLM evaluates Kelly criterion bets — only betting when estimated probability exceeds market-implied by 5+ percentage points. Executes `bet:{market_id}:outcome{n}` transfers.

---

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

## Quick Start

```bash
cd agentos
uv sync
.venv/bin/python main.py          # port 8420
```

Open http://localhost:8420

## API Endpoints

| Method | Path | Description |
|---|---|---|
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
| `/` | Landing — live feed, pipeline, stack |
| `/yield` | Yield agent page |
| `/trader` | Trader agent page |
| `/prediction` | Prediction agent page |
| `/dashboard` | Live monitor — SSE feed with start/stop |
| `/deploy` | Deploy form — connect Slush wallet, configure guardrails |

## Tech Stack

- **Blockchain:** Sui Testnet (Move, RPC, PTBs) — Epoch 1146, 3.67B txns
- **Package:** `0x8be6...f9de` ([SuiVision](https://testnet.suivision.xyz/package/0x8be6a574ed9711fc0815e5821358eeb9fd0b269c1c5aa399338c6da786c8f9de))
- **AI:** Groq API (llama-3.3-70b-versatile, structured JSON)
- **Storage:** Walrus (content-addressed blob logs)
- **Market Data:** CoinGecko (real-time SUI/USD price + trending)
- **Backend:** FastAPI + Uvicorn (Python 3.12)
- **Frontend:** Vanilla JS, GSAP, Lenis smooth scroll
- **Deployment:** Vercel (serverless) + local (persistent agents)

## License

Apache 2.0
