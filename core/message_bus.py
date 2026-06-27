"""
Agent message bus — room-based pub/sub with @mentions.
Mirrors the Band platform pattern used by FusionGrid.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from uuid import uuid4

from core.models import AgentMessage, AgentRole


class MessageBus:
    def __init__(self):
        self._rooms: dict[str, list[callable]] = defaultdict(list)
        self._history: dict[str, list[AgentMessage]] = defaultdict(list)
        self._agent_status: dict[str, bool] = {}
        self._event_listeners: list[callable] = []

    def register_agent(self, name: str, role: AgentRole | str):
        self._agent_status[name] = True

    def set_agent_offline(self, name: str):
        self._agent_status[name] = False

    def subscribe(self, room: str, callback: callable):
        self._rooms[room].append(callback)

    def on_event(self, callback: callable):
        self._event_listeners.append(callback)

    async def _notify_event(self, event: AgentMessage):
        for cb in self._event_listeners:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(event)
                else:
                    cb(event)
            except Exception:
                pass

    async def send(self, msg: AgentMessage):
        msg.timestamp = datetime.now(timezone.utc).isoformat()
        self._history[msg.room].append(msg)
        await self._notify_event(msg)

        room_subscribers = self._rooms.get(msg.room, [])
        has_mentions = bool(msg.mentions)

        for cb in room_subscribers:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(msg)
                else:
                    cb(msg)
            except Exception:
                pass

    async def broadcast(self, room: str, sender: str, sender_role: AgentRole | str,
                        content: str, event_type: str = "broadcast",
                        payload: dict | None = None):
        msg = AgentMessage(
            room=room, sender=sender, sender_role=sender_role,
            content=content, event_type=event_type,
            payload=payload or {},
        )
        await self.send(msg)
        return msg

    def get_history(self, room: str, limit: int = 50) -> list[AgentMessage]:
        return self._history.get(room, [])[-limit:]

    def get_agent_status(self) -> dict:
        return dict(self._agent_status)


bus = MessageBus()
