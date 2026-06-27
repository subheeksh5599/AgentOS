"""
Storage Agent — manages storage pool allocation, provisioning, and decommissioning.
Responds to @storage_agent mentions in grid-ops room.
"""
from __future__ import annotations
import asyncio

from core.message_bus import bus
from core.models import AgentMessage, AgentRole, NodeStatus
from core.storage import storage


async def handle_message(msg: AgentMessage):
    content = msg.content.lower()

    if "create pool" in content or "new pool" in content:
        parts = msg.content.split()
        name = "new-pool"
        region = "us-east-1"
        for i, w in enumerate(parts):
            if w == "pool" and i + 1 < len(parts):
                name = parts[i + 1]
            if w == "region" and i + 1 < len(parts):
                region = parts[i + 1]
        pool = storage.create_pool(name=name, region=region, capacity_tb=50.0)
        await bus.broadcast("grid-ops", "StorageAgent", AgentRole.STORAGE_AGENT,
                            f"Pool '{pool.name}' created in {pool.region} [{pool.id}] — {pool.capacity_tb:.0f} TB",
                            event_type="pool_created", payload=pool.model_dump())

    elif "provision" in content or "allocate" in content:
        pools = storage.list_pools()
        if not pools:
            await bus.broadcast("grid-ops", "StorageAgent", AgentRole.STORAGE_AGENT,
                                "No pools available for provisioning. Create a pool first.",
                                event_type="error")
            return
        pool = pools[0]
        node = storage.allocate_storage(pool.id, size_gb=10.0)
        if node:
            await bus.broadcast("grid-ops", "StorageAgent", AgentRole.STORAGE_AGENT,
                                f"Provisioned 10GB on {node.name} [{node.id}] — {node.used_tb:.2f} TB used",
                                event_type="storage_allocated",
                                payload={"node_id": node.id, "pool_id": pool.id, "size_gb": 10.0})
        else:
            await bus.broadcast("grid-ops", "StorageAgent", AgentRole.STORAGE_AGENT,
                                "Insufficient capacity. Expand pool or free space.",
                                event_type="error")

    elif "status" in content or "summary" in content:
        s = storage.summary()
        await bus.broadcast("grid-ops", "StorageAgent", AgentRole.STORAGE_AGENT,
                            f"Grid: {s['total_nodes']} nodes, {s['online_nodes']} online, "
                            f"{s['total_used_tb']:.1f}/{s['total_capacity_tb']:.0f} TB used across {s['regions']}",
                            event_type="status_report", payload=s)


async def run():
    bus.register_agent("StorageAgent", AgentRole.STORAGE_AGENT)
    s = storage.summary()

    async def callback(msg: AgentMessage):
        if "storage_agent" in msg.content.lower() or msg.room == "grid-ops":
            await handle_message(msg)

    bus.subscribe("grid-ops", callback)
    await bus.broadcast("grid-ops", "StorageAgent", AgentRole.STORAGE_AGENT,
                        f"Online — {s['total_nodes']} nodes, {s['total_capacity_tb']:.0f} TB across {s['regions']}",
                        event_type="agent_online")

    while True:
        await asyncio.sleep(30)
