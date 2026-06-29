"""
Dynamic agent registry — tracks, starts, and stops agent loops at runtime.
"""
import asyncio
from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class AgentConfig:
    agent_id: str
    name: str
    agent_type: str  # "yield", "trader", "prediction"
    guardrails: dict
    interval_seconds: int
    wallet_address: str = ""
    created_at: str = ""
    status: str = "stopped"  # "running", "stopped", "error"

    def to_dict(self):
        return {
            "id": self.agent_id,
            "name": self.name,
            "type": self.agent_type,
            "guardrails": self.guardrails,
            "interval_seconds": self.interval_seconds,
            "wallet_address": self.wallet_address,
            "created_at": self.created_at,
            "status": self.status,
        }


class AgentRegistry:
    """Singleton registry for managing agent lifecycles."""

    def __init__(self):
        self._agents: dict[str, dict] = {}  # agent_id -> {config, task}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"agent-{self._counter:04d}"

    def register(self, config: AgentConfig) -> str:
        """Register a new agent configuration. Returns agent_id."""
        config.agent_id = self._next_id()
        self._agents[config.agent_id] = {"config": config, "task": None}
        return config.agent_id

    async def start(self, agent_id: str) -> bool:
        """Start a registered agent's loop."""
        entry = self._agents.get(agent_id)
        if not entry or entry["task"] is not None:
            return False

        cfg = entry["config"]
        loop_fn = _agent_loop_for_type(cfg.agent_type)
        if not loop_fn:
            return False

        task = asyncio.create_task(
            loop_fn(cfg.name, cfg.agent_type, cfg.guardrails, cfg.interval_seconds)
        )
        entry["task"] = task
        cfg.status = "running"
        return True

    async def stop(self, agent_id: str) -> bool:
        """Stop a running agent."""
        entry = self._agents.get(agent_id)
        if not entry or entry["task"] is None:
            return False
        entry["task"].cancel()
        entry["task"] = None
        entry["config"].status = "stopped"
        return True

    def list_agents(self) -> list[dict]:
        """Return all registered agents with status."""
        return [
            {**entry["config"].to_dict(), "running": entry["task"] is not None}
            for entry in self._agents.values()
        ]

    def get_running(self) -> list[dict]:
        """Return only running agents."""
        return [a for a in self.list_agents() if a["running"]]


def _agent_loop_for_type(agent_type: str):
    """Return the agent loop function for a given type."""
    if agent_type == "yield":
        from runtime.agents.yield_agent import make_loop
        return make_loop
    elif agent_type == "trader":
        from runtime.agents.trader_agent import make_loop
        return make_loop
    elif agent_type == "prediction":
        from runtime.agents.prediction_agent import make_loop
        return make_loop
    return None


# Singleton
registry = AgentRegistry()
