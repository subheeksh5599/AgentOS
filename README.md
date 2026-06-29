<div align="center">

# AgentOS

**Move framework for autonomous AI agents on Sui.**

[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)
[![Sui](https://img.shields.io/badge/Sui-Testnet-4da8ff)](https://sui.io)
[![Language](https://img.shields.io/badge/Move-%E2%9C%93-blue)](https://sui.io/move)
[![LLM](https://img.shields.io/badge/Groq-Llama%203.3%2070B-orange)](https://groq.com)
[![Frontend](https://img.shields.io/badge/Frontend-Vanilla%20%2B%20Vite-informational)](https://vite.dev)
[![Runtime](https://img.shields.io/badge/Runtime-Python%203.12%2B-yellow)](https://python.org)

</div>

---

Programmable on-chain agents with Sui wallets, verifiable execution logs, and configurable guardrails. Write a strategy in Move, deploy it via a factory contract, and let the off-chain runtime handle LLM reasoning, chain-state polling, and transaction submission. Every decision is logged to Walrus as a content-addressed blob, making the full agent lifecycle auditable without trusting a centralized executor.

## Architecture

```
zkLogin identity ──→ Agent Factory (PTB) ──→ Agent Wallet (guardrails)
                                     │
                                     ├── Agent Registry (on-chain index)
                                     ├── Action Log (Walrus blobs)
                                     │
Off-chain runtime:
  Sui RPC loop ──→ Groq LLM reasoning ──→ Guardrail validation ──→ Sponsored TX
                                                              ──→ Walrus upload
                                                              ──→ SSE stream to dashboard
```

## Sui primitives

| Primitive | Role |
|-----------|------|
| **Walrus** | Content-addressed blobs for agent decisions, execution traces, and model configuration. Immutable audit trail. |
| **Seal** | Encrypted agent state and private keys at rest. Agents hold funds without exposing signing material on-chain. |
| **DeepBook** | Unified liquidity across Spot, Margin, and Predict. Agents trade through a single interface rather than routing across fragmented venues. |
| **zkLogin** | Google OAuth derives a Sui address. Agent identity is bound to a real user, not a detached keypair. |
| **Sponsored TXs** | Gas station pattern for autonomous execution. Agents do not need to hold SUI for transaction fees. |
| **PTBs** | Multi-step strategies execute atomically in one block. Swap, stake, and log in a single transaction. |
| **Google AP2** | Agent-to-agent payment primitives. Sui is Google's launch partner for the AP2 protocol. |

## Move modules

```
move/sources/
├── agent_registry.move        Agent directory: registration, discovery, owner binding
├── agent_wallet.move          Custody with programmable constraints per agent
├── agent_factory.move         Single-PTB deploy: wallet + registry + funding + guardrails
├── action_log.move            Append-only ledger with Walrus blob references
└── examples/
    ├── yield_agent.move       Pool scanning, APR threshold comparison, rebalancing
    ├── trader_agent.move      Order book arbitrage, stop-loss/take-profit triggers
    └── prediction_agent.move  Kelly criterion sizing, edge detection, confidence gating
```

## Off-chain runtime

```
runtime/
├── llm.py              Groq client — one key drives three agents via distinct prompts
├── sui_client.py       Sui testnet JSON-RPC: pool state, order books, predict markets
├── walrus_client.py    Blob upload with content-addressed hashing
├── event_bus.py        Async pub/sub with SSE fan-out for live dashboard
├── api.py              FastAPI SSE endpoint for streaming agent events
├── agents/
│   ├── yield_agent.py    45s poll loop — fetch state → Groq → validate → execute
│   ├── trader_agent.py   30s poll loop — order book analysis with profit threshold
│   └── prediction_agent.py  60s poll loop — market scoring with confidence floor
└── main.py             uvicorn entry point, agent lifecycle management
```

Agents poll Sui testnet for live chain state, pass structured context to Groq (Llama 3.3 70B via `response_format: json_object`), validate the returned decision against on-chain guardrails, and route valid actions through the sponsored transaction pipeline. Every step — decision, validation, execution — is logged to Walrus and streamed to the dashboard over SSE.

## Run locally

```bash
cd ui && npm install && npm run build && cd ..
uv venv && uv pip install -r requirements.txt
source .venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8420
```

Requires a Groq API key in `runtime/.env`. The runtime needs a persistent process (agents run as async loops in the uvicorn lifespan). Vercel deploys the static frontend and a subset of the API as serverless functions; the full agent loop requires a long-lived process.

## Pages

| Path | Description |
|------|-------------|
| `/` | Landing — strategy overview, pipeline, deploy panel |
| `/dashboard.html` | Live SSE stream of agent decisions, DeepBook market data |
| `/api.html` | REST + SSE endpoint reference |
| `/contracts.html` | Move module documentation with function signatures |

## License

Apache 2.0
