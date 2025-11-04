from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Ứng dụng FastAPI sử dụng cấu hình tập trung qua lớp Settings."""

    mongo_uri: str = Field(
        default="mongodb+srv://nvt120205:thang1202@thangnguyen.8aiscbh.mongodb.net/",
        alias="MONGO_URI",
    )
    mongo_db: str = Field(default="case_study_db", alias="MONGO_DB")
    mongo_timeout_ms: int = Field(
        default=2_000, alias="MONGO_TIMEOUT_MS", description="Mongo client timeout (ms)."
    )
    frontend_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[1] / "frontend"
    )
    case_data_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2] / "cases"
    )

    class Config:
        frozen = True
        extra = "ignore"
        populate_by_name = True


@lru_cache
def get_settings() -> Settings:
    """Cache settings để dùng lại trong toàn ứng dụng."""
    return Settings()
