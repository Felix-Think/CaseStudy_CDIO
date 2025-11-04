from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from casestudy.app.api import api_router
from casestudy.app.core.config import get_settings

app = FastAPI(title="CaseStudy API", version="1.0.0")

settings = get_settings()
FRONTEND_DIR = settings.frontend_dir

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR, html=False), name="static")


@app.get("/", response_class=FileResponse)
async def serve_frontend() -> FileResponse:
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found.")
    return FileResponse(index_path)


@app.get("/nhap-case", response_class=FileResponse)
async def serve_nhap_case() -> FileResponse:
    nhap_case_path = FRONTEND_DIR / "nhap-case.html"
    if not nhap_case_path.exists():
        raise HTTPException(status_code=404, detail="nhap-case.html not found.")
    return FileResponse(nhap_case_path)


@app.get("/chatframe", response_class=FileResponse)
async def serve_chatframe() -> FileResponse:
    chatframe_path = FRONTEND_DIR / "chatframe.html"
    if not chatframe_path.exists():
        raise HTTPException(status_code=404, detail="chatframe.html not found.")
    return FileResponse(chatframe_path)


@app.get("/case-list", response_class=FileResponse)
async def serve_case_list() -> FileResponse:
    case_list_path = FRONTEND_DIR / "listOfCase.html"
    if not case_list_path.exists():
        raise HTTPException(status_code=404, detail="listOfCase.html not found.")
    return FileResponse(case_list_path)

app.include_router(api_router, prefix="/api")
