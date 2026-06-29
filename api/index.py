import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from apiroutes import router

UI_DIR = Path(__file__).parent.parent / "ui"


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="AgentOS", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)

app.mount("/assets", StaticFiles(directory=UI_DIR / "assets"), name="assets")


@app.get("/{full_path:path}")
async def serve(full_path: str = ""):
    fp = UI_DIR / (full_path or "index.html")
    if fp.is_file():
        return FileResponse(fp)
    return FileResponse(UI_DIR / "index.html")
