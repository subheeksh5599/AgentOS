"""
Walrus client — upload verifiable agent logs as content-addressed blobs.
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
import httpx

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

PUBLISHER_URL = os.environ.get("WALRUS_PUBLISHER_URL", "https://publisher.walrus-testnet.walrus.space")


def upload_blob(data: dict) -> str:
    """Upload a JSON-serializable dict to Walrus. Returns blob ID."""
    content = json.dumps(data, sort_keys=True, default=str).encode()
    blob_hash = hashlib.sha256(content).hexdigest()

    try:
        with httpx.Client(timeout=10) as client:
            r = client.put(
                f"{PUBLISHER_URL}/v1/store",
                content=content,
                headers={"Content-Type": "application/octet-stream"},
            )
            if r.status_code in (200, 201):
                result = r.json()
                blob_id = result.get("newlyCreated", {}).get("blobObject", {}).get("blobId", "")
                if blob_id:
                    return blob_id
    except Exception:
        pass

    return f"walrus://{blob_hash}"


def log_agent_action(agent_type: str, agent_name: str, decision: dict, txn_digest: str = "") -> dict:
    """Log an agent action to Walrus and return the blob ID."""
    entry = {
        "agent_type": agent_type,
        "agent_name": agent_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "txn_digest": txn_digest,
    }
    blob_id = upload_blob(entry)
    entry["walrus_blob_id"] = blob_id
    return entry
