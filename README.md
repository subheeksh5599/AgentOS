# AgentOS

Autonomous cloud operations platform. 4 agents manage storage, security, monitoring, and ops across a 3-region topology. Nimbus Grid is the UI.

## Stack

| Layer | What |
|-------|------|
| API | FastAPI (Python) |
| UI | vanilla HTML/CSS/JS, Vite |
| Agents | async message bus, room-based pub/sub |
| TXNs | SHA-256 hash-chained ledger |
| Deploy | Vercel serverless + static |

## Run locally

```bash
cd ui && npm install && npm run build && cd ..
uv venv && uv pip install -r requirements.txt
source .venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8420 --reload
```

Open `http://localhost:8420`. The CLI in the hero console talks directly to the agents. Try `store 500`, `status`, `scan`.

## Deploy

```bash
vercel --prod
```

Static UI from `ui/dist/`, API routes via `api/index.py` as serverless functions. No database, no external services — everything is in-memory.

## API

```
GET  /api/health
GET  /api/state
GET  /api/pools
POST /api/pools
GET  /api/nodes
GET  /api/transactions
POST /api/transactions
POST /api/console        { "command": "status" }
GET  /api/events/history  ?room=grid-ops&limit=50
```

## Agents

| Agent | Role |
|-------|------|
| StorageAgent | pool provisioning, allocation |
| SecurityAgent | encryption audit, threat scan |
| MonitorAgent | node health, latency, alerts |
| OpsAgent | CLI bridge, transaction execution |

Agents communicate over a room-based message bus and record everything to an append-only audit trail.

## Architecture

```
agentos/
├── api/index.py        # Vercel ASGI entry
├── apiroutes.py        # all REST endpoints
├── main.py             # local dev (uvicorn + UI serving + live agents)
├── core/
│   ├── models.py       # Pydantic models
│   ├── storage.py      # 3 pools, 12 nodes, in-memory + JSON
│   ├── transactions.py # SHA-256 hash chain
│   └── message_bus.py  # room-based pub/sub
├── agents/             # 4 agent implementations
└── ui/                 # Nimbus Grid frontend
```
