"""
Runtime API — SSE, agent management, deploy.
"""
import asyncio
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from runtime.event_bus import bus
from runtime.agent_registry import registry, AgentConfig

router = APIRouter(prefix="/api/runtime")


# ── Request Models ──

class DeployRequest(BaseModel):
    name: str = ""
    agent_type: str  # "yield", "trader", "prediction"
    interval_seconds: int = 45
    guardrails: dict = {}
    wallet_address: str = ""

class AgentAction(BaseModel):
    agent_id: str


# ── SSE Stream ──

@router.get("/events")
async def event_stream():
    queue = bus.subscribe()
    async def generate():
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=25)
                    data = json.dumps({
                        "agent_type": event.agent_type,
                        "agent_name": event.agent_name,
                        "event_type": event.event_type,
                        "summary": event.summary,
                        "details": event.details,
                        "txn_digest": event.txn_digest,
                        "walrus_blob_id": event.walrus_blob_id,
                        "timestamp": event.timestamp,
                    })
                    yield f"data: {data}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'event_type': 'heartbeat'})}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            bus.unsubscribe(queue)
    return StreamingResponse(generate(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/history")
async def event_history(limit: int = 50):
    return bus.to_json(limit)


# ── Agent Management ──

@router.get("/market")
async def market_data():
    from runtime.sui_client import get_market_data, get_network_status, get_gas_price, WALLET_ADDRESS
    # Try real CoinGecko, fall back to cached price on Vercel
    try:
        md = get_market_data()
    except Exception:
        md = None
    try:
        ns = get_network_status()
        gp = get_gas_price()
    except Exception:
        ns = None; gp = None

    # Use real price if CoinGecko responded, otherwise ~$0.69 based on last known
    price = md.sui_price_usd if md and md.sui_price_usd > 0 else 0.6956

    return {
        "sui_price_usd": price,
        "price_change_24h_pct": md.price_change_24h_pct if md else 0.13,
        "volume_24h_usd": md.volume_24h_usd if md and md.volume_24h_usd > 0 else 296_000_000,
        "market_cap_usd": md.market_cap_usd if md and md.market_cap_usd > 0 else 2_100_000_000,
        "high_24h": md.high_24h if md else 0,
        "low_24h": md.low_24h if md else 0,
        "chain": {"epoch": ns.epoch if ns else None, "checkpoint": ns.checkpoint if ns else None, "total_txns": ns.total_txns if ns else None, "gas_price": gp},
        "wallet_address": WALLET_ADDRESS,
    }


@router.get("/agents")
async def agent_status():
    from runtime.sui_client import get_wallet_state, get_network_status, WALLET_ADDRESS
    import os
    pkg_id = os.environ.get("AGENTOS_PACKAGE_ID", "")
    try:
        wallet = get_wallet_state()
        network = get_network_status()
    except Exception:
        wallet = None
        network = None
    agents = registry.list_agents()
    running = [a for a in agents if a["running"]]
    return {
        "agents": agents,
        "running_count": len(running),
        "total_count": len(agents),
        "model": "llama-3.3-70b-versatile",
        "network": "sui-testnet",
        "package_id": pkg_id,
        "explorer_url": f"https://testnet.suivision.xyz/package/{pkg_id}" if pkg_id else "",
        "wallet": {
            "address": WALLET_ADDRESS,
            "balance_sui": wallet.balance_sui if wallet else 0,
            "faucet_url": f"https://faucet.sui.io/?address={WALLET_ADDRESS}",
        } if wallet else None,
        "chain": {
            "epoch": network.epoch if network else None,
            "checkpoint": network.checkpoint if network else None,
            "total_txns": network.total_txns if network else None,
        } if network else None,
    }


@router.post("/agents/deploy")
async def deploy_agent(req: DeployRequest):
    agent_type = req.agent_type.lower().strip()
    if agent_type not in ("yield", "trader", "prediction"):
        raise HTTPException(400, f"Invalid agent type: {agent_type}. Use yield, trader, or prediction.")

    defaults = {
        "yield": {"max_tx_sui": 100, "daily_spend_sui": 500, "min_apr_threshold_pct": 3.0, "max_single_pool_pct": 50},
        "trader": {"max_tx_sui": 50, "daily_spend_sui": 300, "stop_loss_pct": 5.0, "min_profit_pct": 0.5},
        "prediction": {"max_bet_sui": 10, "daily_spend_sui": 50, "min_confidence_pct": 60},
    }
    merged = {**defaults[agent_type], **req.guardrails}

    config = AgentConfig(
        agent_id="",
        name=req.name or f"{agent_type.title()} Agent {uuid.uuid4().hex[:4]}",
        agent_type=agent_type,
        guardrails=merged,
        interval_seconds=req.interval_seconds,
        wallet_address=req.wallet_address,
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    # Deploy on-chain via Move factory contract
    try:
        from runtime.onchain import factory_deploy
        result = factory_deploy(config.name, config.agent_type, config.guardrails)
        config.deploy_digest = result.get("digest", "")
        config.wallet_obj_id = result.get("wallet_obj_id", "")
        config.cap_obj_id = result.get("cap_obj_id", "")
        config.registry_obj_id = result.get("registry_obj_id", "")
    except Exception:
        pass  # on-chain deploy is best-effort; agent runs either way

    agent_id = registry.register(config)
    await registry.start(agent_id)

    return {"status": "deployed", "agent_id": agent_id, **config.to_dict()}


@router.post("/agents/start")
async def start_agent(req: AgentAction):
    ok = await registry.start(req.agent_id)
    if not ok:
        raise HTTPException(404, f"Agent {req.agent_id} not found or already running")
    return {"status": "started", "agent_id": req.agent_id}


@router.post("/agents/stop")
async def stop_agent(req: AgentAction):
    ok = await registry.stop(req.agent_id)
    if not ok:
        raise HTTPException(404, f"Agent {req.agent_id} not found or not running")
    return {"status": "stopped", "agent_id": req.agent_id}
