from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api_casestudy.core.config import get_settings
from api_casestudy.routers import agent_router

# Import thêm router từ casestudy.app
from casestudy.app.api.v1.routes import cases, auth


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
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    """
    Endpoint kiểm tra tình trạng chạy của service.
    """
    return {"status": "ok"}