"""
SSE API endpoint — stream agent events to the dashboard.
"""
import asyncio
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from runtime.event_bus import bus

router = APIRouter(prefix="/api/runtime")


@router.get("/events")
async def event_stream():
    """SSE stream of agent events."""
    queue = bus.subscribe()

    async def generate():
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=25)
                    data = json.dumps({
                        "agent_type": event.agent_type,
                        "agent_name": event.agent_name,
                        "event_type": event.event_type,
                        "summary": event.summary,
                        "details": event.details,
                        "txn_digest": event.txn_digest,
                        "walrus_blob_id": event.walrus_blob_id,
                        "timestamp": event.timestamp,
                    })
                    yield f"data: {data}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'event_type': 'heartbeat'})}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            bus.unsubscribe(queue)

    return StreamingResponse(generate(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/history")
async def event_history(limit: int = 50):
    return bus.to_json(limit)


@router.get("/agents")
async def agent_status():
    return {
        "agents": [
            {"name": "Alpha Yield", "type": "yield", "status": "running", "interval_sec": 45},
            {"name": "Arb Hunter v2", "type": "trader", "status": "running", "interval_sec": 30},
            {"name": "Prediction Scout", "type": "prediction", "status": "running", "interval_sec": 60},
        ],
        "groq_model": "llama-3.3-70b-versatile",
        "sui_network": "testnet",
    }
