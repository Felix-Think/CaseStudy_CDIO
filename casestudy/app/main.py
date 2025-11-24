from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import logging
import sys
import traceback
import os
from bson.objectid import ObjectId

from casestudy.app.api import api_router
from api_casestudy.routers import agent_router, health_router
from casestudy.app.core.config import get_settings

# Configure root logging to ensure stdout/stderr capture on hosts like Render
LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "DEBUG")
# Force root logger configuration even if Uvicorn already configured.
root_logger = logging.getLogger()
for h in list(root_logger.handlers):
    root_logger.removeHandler(h)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('[%(levelname)s] %(asctime)s %(name)s: %(message)s'))
root_logger.addHandler(handler)
root_logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.DEBUG))

# Also raise levels for uvicorn internal loggers if needed.
logging.getLogger("uvicorn").setLevel(logging.INFO)
logging.getLogger("uvicorn.error").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("app.middleware").setLevel(logging.DEBUG)
root_logger.debug("Logging initialized (APP_LOG_LEVEL=%s)", LOG_LEVEL)
app = FastAPI(title="CaseStudy Unified API", version="1.0.0")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger = logging.getLogger("app.middleware")
    logger.debug("--> %s %s", request.method, request.url.path)
    try:
        response = await call_next(request)
    except Exception as exc:
        # Log full traceback and re-raise after returning helpful response
        logger.error("Unhandled exception processing request %s %s: %s", request.method, request.url.path, exc, exc_info=True)
        # Optionally return structured JSON for debugging when DEBUG enabled
        if os.getenv("APP_DEBUG_ERRORS", "1") == "1":
            tb = traceback.format_exc()
            return JSONResponse(status_code=500, content={"detail": str(exc), "traceback": tb})
        raise
    logger.debug("<-- %s %s %s", request.method, request.url.path, response.status_code)
    try:
        print(f"[REQ] {request.method} {request.url.path} {response.status_code}")
    except Exception:
        pass
    return response

settings = get_settings()
FRONTEND_DIR = settings.frontend_dir

# ----------------------- Session + CORS Middlewares ------------------------ #
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    # Keep explicit log to avoid silent misconfig in production
    root_logger.warning("SECRET_KEY is not set – SessionMiddleware will use a weak key.")
    SECRET_KEY = os.getenv("FALLBACK_SECRET_KEY", "dev-insecure-secret-key-change-me")

# Session must be added BEFORE CORS and routers
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="none",
    https_only=True,
)

# CORS should be after Session, before routers
frontend_origins = os.getenv("FRONTEND_ORIGINS")
if frontend_origins:
    allowed = [o.strip() for o in frontend_origins.split(",") if o.strip()]
else:
    allowed = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR, html=False), name="static")
else:
    root_logger.warning("FRONTEND_DIR does not exist: %s", FRONTEND_DIR)


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
app.include_router(agent_router, prefix="/api/agent")
app.include_router(health_router, prefix="/api")

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

# Duplicate include removed; agent + health routers already mounted.
