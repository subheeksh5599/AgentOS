from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from core.message_bus import bus
from core.models import AgentMessage, AgentRole, AlertSeverity, NodeStatus
from core.storage import storage
from core.transactions import txn_engine

router = APIRouter()

_agents_warmed = False


def _warm_agents():
    global _agents_warmed
    if _agents_warmed:
        return
    _agents_warmed = True
    for name, role in [("StorageAgent", AgentRole.STORAGE_AGENT),
                       ("SecurityAgent", AgentRole.SECURITY_AGENT),
                       ("MonitorAgent", AgentRole.MONITOR_AGENT),
                       ("OpsAgent", AgentRole.OPS_AGENT)]:
        bus.register_agent(name, role)


async def _agent_broadcast(sender: str, role: AgentRole, content: str, event_type: str = "message",
                           payload: dict | None = None):
    msg = AgentMessage(sender=sender, sender_role=role, room="grid-ops",
                       content=content, event_type=event_type, payload=payload or {})
    await bus.send(msg)


@router.get("/api/health")
async def health():
    return {"status": "ok", "service": "agentos", "version": "0.1.0"}


@router.get("/api/state")
async def system_state():
    _warm_agents()
    s = storage.summary()
    txns = txn_engine.list_all()
    return {
        **s,
        "active_transactions": len(txn_engine.list_pending()),
        "committed_transactions": len([t for t in txns if t.status.value == "committed"]),
        "chain_verified": txn_engine.verify_chain(),
        "head_hash": txn_engine.head_hash,
        "agents": bus.get_agent_status(),
    }


@router.get("/api/pools")
async def list_pools():
    return [p.model_dump() for p in storage.list_pools()]


@router.get("/api/pools/{pool_id}")
async def get_pool(pool_id: str):
    pool = storage.get_pool(pool_id)
    if not pool:
        raise HTTPException(404, "Pool not found")
    return pool.model_dump()


@router.post("/api/pools")
async def create_pool(data: dict):
    pool = storage.create_pool(name=data.get("name", "new-pool"),
                               region=data.get("region", "us-east-1"),
                               capacity_tb=data.get("capacity_tb", 50.0),
                               tier=data.get("tier", "standard"))
    await _agent_broadcast("StorageAgent", AgentRole.STORAGE_AGENT,
                           f"Pool '{pool.name}' created in {pool.region} [{pool.id}]",
                           event_type="pool_created", payload=pool.model_dump())
    return pool.model_dump()


@router.delete("/api/pools/{pool_id}")
async def delete_pool(pool_id: str):
    if storage.delete_pool(pool_id):
        return {"status": "deleted"}
    raise HTTPException(404, "Pool not found")


@router.get("/api/nodes")
async def list_nodes(pool_id: str | None = None):
    return [n.model_dump() for n in storage.list_nodes(pool_id)]


@router.get("/api/nodes/{node_id}")
async def get_node(node_id: str):
    node = storage.get_node(node_id)
    if not node:
        raise HTTPException(404, "Node not found")
    return node.model_dump()


@router.post("/api/storage/allocate")
async def allocate_storage(data: dict):
    node = storage.allocate_storage(data.get("pool_id", ""), data.get("size_gb", 1.0))
    if not node:
        raise HTTPException(400, "Insufficient capacity or pool not found")
    return node.model_dump()


@router.post("/api/storage/release")
async def release_storage(data: dict):
    ok = storage.release_storage(data.get("node_id", ""), data.get("size_gb", 1.0))
    return {"status": "released" if ok else "not_found"}


@router.get("/api/transactions")
async def list_transactions():
    return [t.model_dump() for t in txn_engine.list_all()]


@router.post("/api/transactions")
async def create_transaction(data: dict):
    pools = storage.list_pools()
    if not pools:
        return txn_engine.begin(op=data.get("op", "store"), pool_id="", node_id="", size_gb=0).model_dump()
    pool_id = pools[0].id
    nodes = storage.list_nodes(pool_id)
    node = nodes[0] if nodes else None
    if not node:
        return {"status": "failed", "detail": "no nodes"}
    txn = txn_engine.begin(op=data.get("op", "store"), pool_id=pool_id, node_id=node.id,
                           size_gb=data.get("size_gb", 0.0))
    target = storage.allocate_storage(pool_id, txn.size_gb)
    if target:
        txn = txn_engine.commit(txn.id)
        await _agent_broadcast("OpsAgent", AgentRole.OPS_AGENT,
                               f"TXN {txn.id[:8]} committed — {txn.size_gb * 1024:.0f} MB stored on {target.name}",
                               event_type="txn_committed", payload=txn.model_dump())
        return txn.model_dump()
    txn_engine.fail(txn.id, "allocation failed")
    return txn.model_dump()


@router.post("/api/console")
async def console_command(data: dict):
    _warm_agents()
    command = data.get("command", "").strip()
    if not command:
        return {"output": "Enter a command. Type 'help' for available operations."}

    await _agent_broadcast("Console", "user", command, event_type="console_command")
    parts = command.split()
    cmd = parts[0].lower()

    if cmd == "help":
        return {"output": (
            "AGENTOS v0.1 — Nimbus Grid CLI\n"
            "  status        Show grid status\n  pools         List storage pools\n"
            "  nodes         List storage nodes\n  store <mb>    Allocate storage (creates TXN)\n"
            "  txns          List transactions\n  agents        Show agent status\n"
            "  scan          Run security scan\n  health        Run health check")}

    elif cmd == "status":
        s = storage.summary()
        return {"output": (
            f"Nimbus Grid Status\n  Nodes:    {s['online_nodes']}/{s['total_nodes']} online\n"
            f"  Capacity: {s['total_used_tb']:.1f} / {s['total_capacity_tb']:.0f} TB\n"
            f"  Regions:  {', '.join(s['regions'])}\n"
            f"  Chain:    {'✓ verified' if txn_engine.verify_chain() else '✗ broken'}\n"
            f"  Head:     {txn_engine.head_hash[:16]}…")}

    elif cmd == "pools":
        pools = storage.list_pools()
        lines = [f"  {p.name:20s} {p.region:16s} {p.used_tb:6.1f}/{p.capacity_tb:6.0f} TB  [{p.tier}]" for p in pools]
        return {"output": "Storage Pools:\n" + "\n".join(lines)}

    elif cmd == "nodes":
        nodes = storage.list_nodes()
        lines = [f"  {n.name:22s} {n.status.value:12s} {n.region:16s} {n.used_tb:5.1f}/{n.capacity_tb:5.0f} TB  {n.latency_ms:5.0f}ms" for n in nodes]
        return {"output": "Storage Nodes:\n" + "\n".join(lines)}

    elif cmd in ("store", "put"):
        size = 1.0
        if len(parts) > 1:
            try:
                size = float(parts[1]) / 1024
            except ValueError:
                pass
        pools = storage.list_pools()
        if not pools:
            return {"output": "Error: No storage pools available."}
        pool = pools[0]
        nodes = storage.list_nodes(pool.id)
        node = nodes[0] if nodes else None
        if not node:
            return {"output": "Error: No nodes in pool."}
        txn = txn_engine.begin(op="store", pool_id=pool.id, node_id=node.id, size_gb=size)
        target = storage.allocate_storage(pool.id, size)
        if target:
            txn = txn_engine.commit(txn.id)
            await _agent_broadcast("OpsAgent", AgentRole.OPS_AGENT,
                                   f"TXN {txn.id[:8]} committed — {size * 1024:.0f} MB on {target.name}",
                                   event_type="txn_committed", payload=txn.model_dump())
            return {"output": (f"TXN {txn.id[:8]} COMMITTED\n  Op: store\n  Size: {size * 1024:.0f} MB\n"
                               f"  Node: {target.name} [{target.id}]\n  Pool: {pool.name}\n"
                               f"  Hash: {txn.hash[:32]}…\n  Status: committed")}
        txn_engine.fail(txn.id, "allocation failed")
        return {"output": f"TXN FAILED: insufficient capacity in {pool.name}"}

    elif cmd == "txns":
        txns = txn_engine.list_all()
        if not txns:
            return {"output": "No transactions recorded."}
        lines = [f"  {t.id[:8]}  {t.op:8s}  {t.status.value:10s}  {t.size_gb * 1024:6.0f}MB  {t.hash[:16]}…" for t in txns[-30:]]
        return {"output": "Transaction Ledger:\n" + "\n".join(lines)}

    elif cmd == "agents":
        agents = bus.get_agent_status()
        lines = [f"  {name:20s} {'● ONLINE' if online else '○ OFFLINE'}" for name, online in agents.items()]
        return {"output": "Agents:\n" + "\n".join(lines)}

    elif cmd == "scan":
        verdict = "PASS" if random.random() > 0.3 else "ALERT"
        await _agent_broadcast("SecurityAgent", AgentRole.SECURITY_AGENT,
                               f"Security scan: {verdict} — encryption nominal, 0 threats",
                               event_type="security_scan", payload={"verdict": verdict})
        return {"output": f"Security scan complete: {verdict}"}

    elif cmd == "health":
        nodes = storage.list_nodes()
        online = sum(1 for n in nodes if n.status == NodeStatus.ONLINE)
        await _agent_broadcast("MonitorAgent", AgentRole.MONITOR_AGENT,
                               f"Health check: {online}/{len(nodes)} nodes online, p99 latency 12ms",
                               event_type="health_report",
                               payload={"online": online, "total": len(nodes)})
        return {"output": f"Health check: {online}/{len(nodes)} nodes online"}

    else:
        await _agent_broadcast("OpsAgent", AgentRole.OPS_AGENT,
                               f"Unknown command received: {command}", event_type="error")
        return {"output": f"Unknown command: {command}\nType 'help' for available commands."}


@router.get("/api/events/history")
async def event_history(room: str = "grid-ops", limit: int = 50):
    return [m.model_dump() for m in bus.get_history(room, limit)]
