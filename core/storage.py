"""
Storage backend — in-memory + file-persisted storage pool management.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from threading import RLock

from core.models import NodeStatus, NodeType, StorageNode, StoragePool

DATA_DIR = Path(os.environ.get("AGENTOS_DATA_DIR", Path(__file__).parent.parent / "data"))
DATA_FILE = DATA_DIR / "state.json"


class StorageEngine:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._pools: dict[str, StoragePool] = {}
        self._nodes: dict[str, StorageNode] = {}
        self._load()

    def _load(self):
        if DATA_FILE.exists():
            with open(DATA_FILE) as f:
                data = json.load(f)
            for p in data.get("pools", []):
                pool = StoragePool(**p)
                self._pools[pool.id] = pool
            for n in data.get("nodes", []):
                node = StorageNode(**n)
                self._nodes[node.id] = node
        if not self._pools:
            self._seed()

    def _save(self):
        with self._lock:
            data = {
                "pools": [p.model_dump() for p in self._pools.values()],
                "nodes": [n.model_dump() for n in self._nodes.values()],
            }
            with open(DATA_FILE, "w") as f:
                json.dump(data, f, indent=2)

    def _seed(self):
        regions = ["us-east-1", "eu-west-1", "ap-southeast-1"]
        for i, region in enumerate(regions):
            pool = StoragePool(
                name=f"pool-{region}",
                region=region,
                capacity_tb=100.0 + i * 50,
                used_tb=10.0 + i * 3,
            )
            self._pools[pool.id] = pool
            for j in range(4):
                node = StorageNode(
                    name=f"node-{region}-{j:02d}",
                    pool_id=pool.id,
                    region=region,
                    node_type=NodeType.STORAGE if j < 3 else NodeType.CACHE,
                    capacity_tb=25.0,
                    used_tb=2.5 + j * 0.5,
                )
                self._nodes[node.id] = node
        self._save()

    def list_pools(self) -> list[StoragePool]:
        return list(self._pools.values())

    def get_pool(self, pool_id: str) -> StoragePool | None:
        return self._pools.get(pool_id)

    def create_pool(self, name: str, region: str, capacity_tb: float, tier: str = "standard") -> StoragePool:
        with self._lock:
            pool = StoragePool(name=name, region=region, capacity_tb=capacity_tb, tier=tier)
            self._pools[pool.id] = pool
            self._save()
            return pool

    def delete_pool(self, pool_id: str) -> bool:
        with self._lock:
            if pool_id in self._pools:
                del self._pools[pool_id]
                self._nodes = {k: v for k, v in self._nodes.items() if v.pool_id != pool_id}
                self._save()
                return True
            return False

    def list_nodes(self, pool_id: str | None = None) -> list[StorageNode]:
        nodes = list(self._nodes.values())
        if pool_id:
            nodes = [n for n in nodes if n.pool_id == pool_id]
        return nodes

    def get_node(self, node_id: str) -> StorageNode | None:
        return self._nodes.get(node_id)

    def allocate_storage(self, pool_id: str, size_gb: float) -> StorageNode | None:
        with self._lock:
            pool = self._pools.get(pool_id)
            if not pool:
                return None
            available = pool.capacity_tb * 1024 - pool.used_tb * 1024
            if size_gb > available:
                return None
            candidates = [n for n in self._nodes.values()
                          if n.pool_id == pool_id and n.status == NodeStatus.ONLINE]
            if not candidates:
                return None
            target = min(candidates, key=lambda n: n.used_tb)
            target.used_tb += size_gb / 1024
            pool.used_tb += size_gb / 1024
            self._save()
            return target

    def release_storage(self, node_id: str, size_gb: float) -> bool:
        with self._lock:
            node = self._nodes.get(node_id)
            if not node:
                return False
            pool = self._pools.get(node.pool_id)
            if not pool:
                return False
            release = size_gb / 1024
            node.used_tb = max(0, node.used_tb - release)
            pool.used_tb = max(0, pool.used_tb - release)
            self._save()
            return True

    def set_node_status(self, node_id: str, status: NodeStatus):
        node = self._nodes.get(node_id)
        if node:
            node.status = status
            self._save()

    def summary(self) -> dict:
        pools = self.list_pools()
        nodes = self.list_nodes()
        return {
            "total_pools": len(pools),
            "total_nodes": len(nodes),
            "online_nodes": sum(1 for n in nodes if n.status == NodeStatus.ONLINE),
            "total_capacity_tb": sum(p.capacity_tb for p in pools),
            "total_used_tb": sum(p.used_tb for p in pools),
            "regions": sorted(set(p.region for p in pools)),
        }


storage = StorageEngine()
