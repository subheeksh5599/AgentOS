from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from apiroutes import router
from runtime.api import router as runtime_router

UI_DIR = Path(__file__).parent.parent / "ui"

app = FastAPI(title="AgentOS", version="1.0.0")
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
