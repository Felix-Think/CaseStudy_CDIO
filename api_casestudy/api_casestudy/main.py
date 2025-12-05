from __future__ import annotations

import logging

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from api_casestudy.core.config import get_settings
from api_casestudy.routers import agent_router

# Import thêm router từ casestudy.app
from casestudy.app.api.v1.routes import cases, auth

logger = logging.getLogger(__name__)
LOG_BODY_LIMIT = 20000  # tăng giới hạn log body để không bị cắt mất phần score


def create_app() -> FastAPI:
    """
    Factory khởi tạo FastAPI cho dịch vụ CaseStudy Agent.
    """
    settings = get_settings()

    app = FastAPI(
        title="CaseStudy Agent API",
        version=settings.version,
        description="Dịch vụ điều phối agent hội thoại cho từng case.",
    )

    # Router Agent (giữ nguyên)
    app.include_router(agent_router, prefix="/api")
    
    # Thêm router Cases và Auth
    app.include_router(cases.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    
    return app


app = create_app()

# Cập nhật CORS cho frontend port 
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",      # Thêm các port frontend khác nếu cần
    "http://127.0.0.1:8000",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_request_response(request: Request, call_next):
    """
    Ghi log input request và output response (trừ stream) để tiện debug.
    """
    body_bytes = await request.body()
    body_text = body_bytes.decode("utf-8", errors="ignore") if body_bytes else ""
    if LOG_BODY_LIMIT and len(body_text) > LOG_BODY_LIMIT:
        body_text = body_text[:LOG_BODY_LIMIT] + "...[truncated]"
    
    logger.info("REQUEST %s %s body=%s", request.method, request.url.path, body_text)
    
    response = await call_next(request)
    
    content_type = response.headers.get("content-type", "")
    if content_type.startswith("text/event-stream"):
        logger.info(
            "RESPONSE %s %s status=%s [streaming]",
            request.method,
            request.url.path,
            response.status_code,
        )
        return response
    
    try:
        response_body = b"".join([chunk async for chunk in response.body_iterator])  # type: ignore[attr-defined]
    except Exception:
        logger.exception("Không thể đọc response body cho %s %s", request.method, request.url.path)
        return response
    
    response_text = response_body.decode("utf-8", errors="ignore")
    if LOG_BODY_LIMIT and len(response_text) > LOG_BODY_LIMIT:
        response_text = response_text[:LOG_BODY_LIMIT] + "...[truncated]"
    
    logger.info(
        "RESPONSE %s %s status=%s body=%s",
        request.method,
        request.url.path,
        response.status_code,
        response_text,
    )
    
    return Response(
        content=response_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
        background=response.background,
    )

@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    """
    Endpoint kiểm tra tình trạng chạy của service.
    """
    return {"status": "ok"}
