from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class NodeType(StrEnum):
    STORAGE = "storage"
    COMPUTE = "compute"
    GATEWAY = "gateway"
    CACHE = "cache"


class NodeStatus(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    PROVISIONING = "provisioning"


class TxnStatus(StrEnum):
    PENDING = "pending"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class AgentRole(StrEnum):
    STORAGE_AGENT = "storage_agent"
    SECURITY_AGENT = "security_agent"
    MONITOR_AGENT = "monitor_agent"
    OPS_AGENT = "ops_agent"


class AlertSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class StoragePool(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    name: str
    region: str
    tier: str = "standard"
    capacity_tb: float
    used_tb: float = 0.0
    status: str = "active"
    encryption: str = "aes-256-gcm"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class StorageNode(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    name: str
    pool_id: str
    node_type: NodeType = NodeType.STORAGE
    status: NodeStatus = NodeStatus.ONLINE
    region: str
    capacity_tb: float
    used_tb: float = 0.0
    throughput_mbps: float = 1000.0
    latency_ms: float = 12.0
    uptime_pct: float = 99.99
    last_heartbeat: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:16])
    op: str
    pool_id: str
    node_id: str
    size_gb: float = 0.0
    status: TxnStatus = TxnStatus.PENDING
    hash: str = ""
    prev_hash: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    committed_at: Optional[str] = None
    details: dict = Field(default_factory=dict)


class AuditEntry(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:16])
    agent: str
    action: str
    room: str
    payload: dict = Field(default_factory=dict)
    hash: str = ""
    prev_hash: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgentMessage(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    room: str
    sender: str
    sender_role: AgentRole | str
    content: str
    event_type: str = "message"
    payload: dict = Field(default_factory=dict)
    mentions: list[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SystemState(BaseModel):
    total_nodes: int = 0
    online_nodes: int = 0
    total_pools: int = 0
    total_capacity_tb: float = 0.0
    total_used_tb: float = 0.0
    active_transactions: int = 0
    committed_transactions: int = 0
    agents_online: list[str] = Field(default_factory=list)
    alerts: list[dict] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)
