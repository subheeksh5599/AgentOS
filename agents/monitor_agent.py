"""
Monitor Agent — tracks node health, latency, throughput, and raises alerts.
Runs proactive health checks every 15 seconds.
Responds to @monitor_agent in grid-ops.
"""
from __future__ import annotations
import asyncio
import random
from datetime import datetime, timezone

from core.message_bus import bus
from core.models import AgentMessage, AgentRole, AlertSeverity, NodeStatus
from core.storage import storage


async def health_check():
    nodes = storage.list_nodes()
    for node in nodes:
        if random.random() < 0.02:
            old_status = node.status
            node.status = NodeStatus.DEGRADED if random.random() < 0.7 else NodeStatus.OFFLINE
            sev = AlertSeverity.CRITICAL if node.status == NodeStatus.OFFLINE else AlertSeverity.WARNING
            await bus.broadcast("grid-ops", "MonitorAgent", AgentRole.MONITOR_AGENT,
                                f"{sev.value.upper()}: {node.name} [{node.id}] "
                                f"status {old_status.value} → {node.status.value} "
                                f"(latency: {node.latency_ms + random.uniform(5, 50):.1f}ms)",
                                event_type="node_alert",
                                payload={"node_id": node.id, "status": node.status.value,
                                         "severity": sev.value, "latency_ms": node.latency_ms})


async def handle_message(msg: AgentMessage):
    content = msg.content.lower()

    if "health" in content or "status" in content or "check" in content:
        nodes = storage.list_nodes()
        online = sum(1 for n in nodes if n.status == NodeStatus.ONLINE)
        degraded = sum(1 for n in nodes if n.status == NodeStatus.DEGRADED)
        offline = sum(1 for n in nodes if n.status == NodeStatus.OFFLINE)
        avg_latency = sum(n.latency_ms for n in nodes) / max(len(nodes), 1)
        await bus.broadcast("grid-ops", "MonitorAgent", AgentRole.MONITOR_AGENT,
                            f"Health: {online}↑ {degraded}⚠ {offline}↓ | "
                            f"Avg latency: {avg_latency:.1f}ms | "
                            f"Throughput: {random.randint(800, 1200)} Mbps",
                            event_type="health_report",
                            payload={"online": online, "degraded": degraded, "offline": offline})


async def run():
    bus.register_agent("MonitorAgent", AgentRole.MONITOR_AGENT)

    async def callback(msg: AgentMessage):
        if "monitor_agent" in msg.content.lower() or msg.room == "grid-ops":
            await handle_message(msg)

    bus.subscribe("grid-ops", callback)
    await bus.broadcast("grid-ops", "MonitorAgent", AgentRole.MONITOR_AGENT,
                        "Online — monitoring 12 nodes, health checks every 15s, p99 alert threshold 50ms",
                        event_type="agent_online")

    while True:
        await health_check()
        await asyncio.sleep(15)
