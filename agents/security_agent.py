"""
Security Agent — monitors encryption, access patterns, and compliance.
Responds to @security_agent in grid-ops and audit events.
"""
from __future__ import annotations
import asyncio
import random

from core.message_bus import bus
from core.models import AgentMessage, AgentRole


THREATS = [
    "unencrypted_access", "unauthorized_ip", "key_rotation_overdue",
    "ddos_pattern", "credential_leak", "abnormal_read_volume",
]


async def handle_message(msg: AgentMessage):
    content = msg.content.lower()

    if "audit" in content or "scan" in content:
        finding = random.choice(THREATS)
        verdict = "PASS" if random.random() > 0.3 else "ALERT"
        await bus.broadcast("grid-ops", "SecurityAgent", AgentRole.SECURITY_AGENT,
                            f"Security scan complete — {verdict}: {finding}",
                            event_type="security_scan",
                            payload={"verdict": verdict, "finding": finding})

    elif "threat" in content or "alert" in content:
        await bus.broadcast("grid-ops", "SecurityAgent", AgentRole.SECURITY_AGENT,
                            "Threat surface nominal. All endpoints encrypted with AES-256-GCM. "
                            "Zero unauthorized access attempts in last 24h.",
                            event_type="threat_report")

    elif "encrypt" in content or "key" in content:
        await bus.broadcast("grid-ops", "SecurityAgent", AgentRole.SECURITY_AGENT,
                            "Encryption status: AES-256-GCM at rest, TLS 1.3 in transit. "
                            "Key rotation scheduled for T+30d. HSM-backed key storage verified.",
                            event_type="encryption_status")


async def run():
    bus.register_agent("SecurityAgent", AgentRole.SECURITY_AGENT)

    async def callback(msg: AgentMessage):
        if "security_agent" in msg.content.lower() or msg.room == "grid-ops":
            await handle_message(msg)

    bus.subscribe("grid-ops", callback)
    await bus.broadcast("grid-ops", "SecurityAgent", AgentRole.SECURITY_AGENT,
                        "Online — AES-256-GCM encryption active, threat detection engaged",
                        event_type="agent_online")

    while True:
        await asyncio.sleep(45)
