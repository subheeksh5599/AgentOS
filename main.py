import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from apiroutes import router
from agents import run_ops, run_monitor, run_security, run_storage

UI_DIR = Path(__file__).parent / "ui"


@asynccontextmanager
async def lifespan(app: FastAPI):
    tasks = [
        asyncio.create_task(run_storage()),
        asyncio.create_task(run_security()),
        asyncio.create_task(run_monitor()),
        asyncio.create_task(run_ops()),
    ]
    print("AgentOS v0.1 — 4 agents online, Nimbus Grid operational")
    yield
    for t in tasks:
        t.cancel()


app = FastAPI(title="AgentOS", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)

if (UI_DIR / "dist").exists():
    app.mount("/assets", StaticFiles(directory=UI_DIR / "dist" / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve(full_path: str = ""):
        fp = UI_DIR / "dist" / (full_path or "index.html")
        if fp.is_file():
            return FileResponse(fp)
        return FileResponse(UI_DIR / "dist" / "index.html")
else:
    @app.get("/")
    async def root():
        return {"agentos": "0.1.0", "tip": "cd ui && npm run build"}


def main():
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8420, reload=True)


if __name__ == "__main__":
    main()
