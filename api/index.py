import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from apiroutes import router
from runtime.api import router as runtime_router
from runtime.agent_registry import registry, AgentConfig
from runtime.agents.yield_agent import make_loop as yield_loop
from runtime.agents.trader_agent import make_loop as trader_loop
from runtime.agents.prediction_agent import make_loop as pred_loop

UI_DIR = Path(__file__).parent.parent / "ui"

DEFAULTS = {
    "yield": {"name": "Alpha Yield", "interval": 45, "guardrails": {"max_tx_sui": 100, "daily_spend_sui": 500, "min_apr_threshold_pct": 3.0, "max_single_pool_pct": 50}},
    "trader": {"name": "Arb Hunter v2", "interval": 30, "guardrails": {"max_tx_sui": 50, "daily_spend_sui": 300, "stop_loss_pct": 5.0, "min_profit_pct": 0.5}},
    "prediction": {"name": "Prediction Scout", "interval": 60, "guardrails": {"max_bet_sui": 10, "daily_spend_sui": 50, "min_confidence_pct": 60}},
}
LOOP_MAP = {"yield": yield_loop, "trader": trader_loop, "prediction": pred_loop}


async def _start_defaults():
    for atype, cfg in DEFAULTS.items():
        config = AgentConfig(agent_id="", name=cfg["name"], agent_type=atype, guardrails=cfg["guardrails"], interval_seconds=cfg["interval"])
        aid = registry.register(config)
        task = asyncio.create_task(LOOP_MAP[atype](cfg["name"], atype, cfg["guardrails"], cfg["interval"]))
        registry._agents[aid]["task"] = task
        config.status = "running"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _start_defaults()
    yield


app = FastAPI(title="AgentOS", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
app.include_router(runtime_router)
app.mount("/assets", StaticFiles(directory=UI_DIR / "assets"), name="assets")


@app.get("/{full_path:path}")
async def serve(full_path: str = ""):
    fp = UI_DIR / (full_path or "index.html")
    if fp.is_file():
        return FileResponse(fp)
    html_fp = UI_DIR / (full_path + ".html")
    if html_fp.is_file():
        return FileResponse(html_fp)
    return FileResponse(UI_DIR / "index.html")
