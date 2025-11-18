from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from bson.objectid import ObjectId

from casestudy.app.api import api_router
from casestudy.app.core.config import get_settings

app = FastAPI(title="CaseStudy API", version="1.0.0")

settings = get_settings()
FRONTEND_DIR = settings.frontend_dir

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR, html=False), name="static")


def ensure_authenticated(request: Request) -> str:
    user_id = request.cookies.get("user_id")
    if not user_id or not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"},
            detail="Requires login",
        )
    return user_id


@app.get("/", response_class=FileResponse)
async def serve_frontend() -> FileResponse:
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found.")
    return FileResponse(index_path)


@app.get("/nhap-case", response_class=FileResponse)
async def serve_nhap_case(request: Request) -> FileResponse:
    ensure_authenticated(request)
    nhap_case_path = FRONTEND_DIR / "nhap-case.html"
    if not nhap_case_path.exists():
        raise HTTPException(status_code=404, detail="nhap-case.html not found.")
    return FileResponse(nhap_case_path)


@app.get("/chatframe", response_class=FileResponse)
async def serve_chatframe(request: Request) -> FileResponse:
    ensure_authenticated(request)
    chatframe_path = FRONTEND_DIR / "chatframe.html"
    if not chatframe_path.exists():
        raise HTTPException(status_code=404, detail="chatframe.html not found.")
    return FileResponse(chatframe_path)


@app.get("/case-list", response_class=FileResponse)
async def serve_case_list(request: Request) -> FileResponse:
    ensure_authenticated(request)
    case_list_path = FRONTEND_DIR / "listOfCase.html"
    if not case_list_path.exists():
        raise HTTPException(status_code=404, detail="listOfCase.html not found.")
    return FileResponse(case_list_path)


@app.get("/quan-ly-case", response_class=FileResponse)
async def serve_manage_case() -> FileResponse:
    manage_path = FRONTEND_DIR / "quan-ly-case.html"
    if not manage_path.exists():
        raise HTTPException(status_code=404, detail="quan-ly-case.html not found.")
    return FileResponse(manage_path)

app.include_router(api_router, prefix="/api")

@app.get("/login", response_class=FileResponse)
async def serve_case_list() -> FileResponse:
    login_path = FRONTEND_DIR / "login.html"
    if not login_path.exists():
        raise HTTPException(status_code=404, detail="login.html not found.")
    return FileResponse(login_path)

@app.get("/register", response_class=FileResponse)
async def serve_register() -> FileResponse:
    register_path = FRONTEND_DIR / "register.html"
    if not register_path.exists():
        raise HTTPException(status_code=404, detail="register.html not found.")
    return FileResponse(register_path)

@app.get("/user", response_class=FileResponse)
async def serve_user(request: Request) -> FileResponse:
    ensure_authenticated(request)
    user_path = FRONTEND_DIR / "user.html"
    if not user_path.exists():
        raise HTTPException(status_code=404, detail="user.html not found.")
    return FileResponse(user_path)

app.include_router(api_router, prefix="/api")
