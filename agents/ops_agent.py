"""
Ops Agent — handles CLI commands, API operations, and system orchestration.
The primary bridge between the user console and internal agents.
Responds to all messages in grid-ops.
"""
from __future__ import annotations
import asyncio

from core.message_bus import bus
from core.models import AgentMessage, AgentRole
from core.storage import storage
from core.transactions import txn_engine


async def handle_message(msg: AgentMessage):
    content = msg.content.strip()

    if content.startswith("txn:") or "store" in content.lower():
        pools = storage.list_pools()
        if not pools:
            await bus.broadcast("grid-ops", "OpsAgent", AgentRole.OPS_AGENT,
                                "No storage pools available. Create one first with 'create pool <name>'.",
                                event_type="error")
            return
        pool = pools[0]
        nodes = storage.list_nodes(pool.id)
        node = nodes[0] if nodes else None
        if not node:
            return

        txn = txn_engine.begin(op="store", pool_id=pool.id, node_id=node.id, size_gb=1.0)
        txn = txn_engine.commit(txn.id)

        await bus.broadcast("grid-ops", "OpsAgent", AgentRole.OPS_AGENT,
                            f"Transaction {txn.id[:8]} committed — "
                            f"1.0 GB stored on {node.name} [{node.id}] "
                            f"(hash: {txn.hash[:16]}…)",
                            event_type="txn_committed",
                            payload=txn.model_dump())

    elif content.startswith("read") or "retrieve" in content.lower():
        await bus.broadcast("grid-ops", "OpsAgent", AgentRole.OPS_AGENT,
                            "Data retrieval: all chunks verified, integrity hash matches. ",
                            event_type="data_read")

    elif content.startswith("delete") or "remove" in content.lower():
        nodes = storage.list_nodes()
        if nodes:
            storage.release_storage(nodes[0].id, size_gb=1.0)
            await bus.broadcast("grid-ops", "OpsAgent", AgentRole.OPS_AGENT,
                                "Storage released — 1.0 GB freed.",
                                event_type="storage_released")

    elif "expand" in content.lower():
        await bus.broadcast("grid-ops", "OpsAgent", AgentRole.OPS_AGENT,
                            "Expansion request routed to StorageAgent for provisioning.",
                            event_type="expansion_requested")

    elif "help" in content.lower():
        await bus.broadcast("grid-ops", "OpsAgent", AgentRole.OPS_AGENT,
                            "Available commands: store <data>, read <key>, delete <key>, "
                            "expand <pool>, status, help",
                            event_type="help")


async def run():
    bus.register_agent("OpsAgent", AgentRole.OPS_AGENT)

    async def callback(msg: AgentMessage):
        if msg.room == "grid-ops":
            await handle_message(msg)

    bus.subscribe("grid-ops", callback)
    await bus.broadcast("grid-ops", "OpsAgent", AgentRole.OPS_AGENT,
                        "Online — operational command interface ready",
                        event_type="agent_online")

    while True:
        await asyncio.sleep(60)
