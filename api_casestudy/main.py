from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api_casestudy.core.config import get_settings
from api_casestudy.routers import agent_router, semantic_router


def create_app() -> FastAPI:
    """
    Factory khởi tạo FastAPI cho dịch vụ CaseStudy Agent & Semantic.
    """
    settings = get_settings()

    app = FastAPI(
        title="CaseStudy Agent API",
        version=settings.version,
        description="Dịch vụ quản lý semantic store và điều phối agent cho từng case.",
    )

    app.include_router(semantic_router, prefix="/api")
    app.include_router(agent_router, prefix="/api")
    return app


app = create_app()
origins = [
    "http://localhost:8000",      # web chạy port 8000
    "http://127.0.0.1:8000",      # đôi khi trình duyệt dùng 127.0.0.1 thay vì localhost
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # hoặc ["*"] nếu chỉ dev local
    allow_credentials=True,
    allow_methods=["*"],          # Cho phép GET, POST, OPTIONS,...
    allow_headers=["*"],          # Cho phép Content-Type, Authorization,...
)

@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    """
    Endpoint kiểm tra tình trạng chạy của service.
    """
    return {"status": "ok"}