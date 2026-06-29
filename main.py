import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from apiroutes import router
from runtime.api import router as runtime_router
from runtime.agents import run_yield, run_trader, run_prediction

UI_DIR = Path(__file__).parent / "ui"


@asynccontextmanager
async def lifespan(app: FastAPI):
    tasks = [
        asyncio.create_task(run_yield()),
        asyncio.create_task(run_trader()),
        asyncio.create_task(run_prediction()),
    ]
    print("AgentOS v1.0 — 3 AI agents online (yield, trader, prediction)")
    print("  Groq: llama-3.3-70b-versatile | Sui testnet | Walrus logging")
    yield
    for t in tasks:
        t.cancel()


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
    return FileResponse(UI_DIR / "index.html")


def main():
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8420, reload=True)


if __name__ == "__main__":
    main()
