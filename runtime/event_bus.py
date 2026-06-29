"""
Shared event bus — agents push events, dashboard pulls via SSE.
"""
import asyncio
import json
from datetime import datetime, timezone
from dataclasses import dataclass, field


@dataclass
class AgentEvent:
    agent_type: str
    agent_name: str
    event_type: str         # "decision", "txn", "error", "guardrail_hit", "walrus_log"
    summary: str            # one-line for dashboard
    details: dict = field(default_factory=dict)
    txn_digest: str = ""
    walrus_blob_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EventBus:
    def __init__(self):
        self._events: list[AgentEvent] = []
        self._queues: list[asyncio.Queue] = []

    def emit(self, event: AgentEvent):
        self._events.append(event)
        if len(self._events) > 500:
            self._events = self._events[-500:]
        for q in self._queues:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass

    def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue(maxsize=100)
        self._queues.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self._queues:
            self._queues.remove(q)

    def get_recent(self, limit: int = 50) -> list[AgentEvent]:
        return self._events[-limit:]

    def to_json(self, limit: int = 50) -> list[dict]:
        return [
            {
                "agent_type": e.agent_type,
                "agent_name": e.agent_name,
                "event_type": e.event_type,
                "summary": e.summary,
                "details": e.details,
                "txn_digest": e.txn_digest,
                "walrus_blob_id": e.walrus_blob_id,
                "timestamp": e.timestamp,
            }
            for e in self._events[-limit:]
        ]


bus = EventBus()
