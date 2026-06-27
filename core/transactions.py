from __future__ import annotations

import hashlib
import json

from core.models import TxnStatus, Transaction


class TxnEngine:
    def __init__(self):
        self._chain: list[Transaction] = []
        self._by_id: dict[str, Transaction] = {}
        self._head_hash: str = hashlib.sha256(b"agentos-genesis").hexdigest()

    def begin(self, op: str, pool_id: str, node_id: str, size_gb: float = 0.0, **kwargs) -> Transaction:
        txn = Transaction(
            op=op,
            pool_id=pool_id,
            node_id=node_id,
            size_gb=size_gb,
            status=TxnStatus.PENDING,
            details=kwargs,
            prev_hash=self._head_hash,
        )
        payload = json.dumps(txn.model_dump(exclude={"hash"}), sort_keys=True, default=str)
        txn.hash = hashlib.sha256(payload.encode()).hexdigest()
        self._by_id[txn.id] = txn
        return txn

    def commit(self, txn_id: str) -> Transaction | None:
        txn = self._by_id.get(txn_id)
        if txn and txn.status == TxnStatus.PENDING:
            txn.status = TxnStatus.COMMITTED
            txn.committed_at = txn.model_fields_set  # timestamp already set, just mark
            from datetime import datetime, timezone
            txn.committed_at = datetime.now(timezone.utc).isoformat()
            self._chain.append(txn)
            self._head_hash = txn.hash
            return txn
        return None

    def rollback(self, txn_id: str) -> Transaction | None:
        txn = self._by_id.get(txn_id)
        if txn and txn.status == TxnStatus.PENDING:
            txn.status = TxnStatus.ROLLED_BACK
            return txn
        return None

    def fail(self, txn_id: str, reason: str = "") -> Transaction | None:
        txn = self._by_id.get(txn_id)
        if txn:
            txn.status = TxnStatus.FAILED
            txn.details["fail_reason"] = reason
            return txn
        return None

    def get(self, txn_id: str) -> Transaction | None:
        return self._by_id.get(txn_id)

    def list_pending(self) -> list[Transaction]:
        return [t for t in self._by_id.values() if t.status == TxnStatus.PENDING]

    def list_all(self) -> list[Transaction]:
        return list(self._chain) + self.list_pending()

    @property
    def head_hash(self) -> str:
        return self._head_hash

    def verify_chain(self) -> bool:
        for i in range(1, len(self._chain)):
            if self._chain[i].prev_hash != self._chain[i - 1].hash:
                return False
        return True


txn_engine = TxnEngine()
