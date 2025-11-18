from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ứng dụng FastAPI sử dụng cấu hình tập trung qua lớp Settings."""

    # ====== MongoDB Configuration ======
    mongo_uri: str = Field(
        default="mongodb+srv://nvt120205:thang1202@thangnguyen.8aiscbh.mongodb.net/",
        alias="MONGO_URI",
    )
    mongo_db: str = Field(default="case_study_db", alias="MONGO_DB")
    mongo_user_db: str = Field(default="User", alias="MONGO_USER_DB")
    mongo_timeout_ms: int = Field(
        default=2_000, alias="MONGO_TIMEOUT_MS", description="Mongo client timeout (ms)."
    )

    # ====== Directory Configuration ======
    frontend_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[1] / "frontend"
    )
    case_data_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2] / "cases"
    )

    # ====== Gemini API Configuration ======
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-flash", alias="GEMINI_MODEL")
    gemini_endpoint: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta",
        alias="GEMINI_ENDPOINT",
    )

    # ====== OpenAI Configuration ======
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_endpoint: str = Field(
        default="https://api.openai.com/v1/chat/completions",
        alias="OPENAI_ENDPOINT",
    )

    # ====== Pinecone Configuration ======
    pinecone_api_key: Optional[str] = Field(default=None, alias="PINECONE_API_KEY")
    pinecone_environment: Optional[str] = Field(default=None, alias="PINECONE_ENVIRONMENT")
    pinecone_scene_index: Optional[str] = Field(default=None, alias="PINECONE_SCENE_INDEX")
    pinecone_persona_index: Optional[str] = Field(default=None, alias="PINECONE_PERSONA_INDEX")
    pinecone_policy_index: Optional[str] = Field(default=None, alias="PINECONE_POLICY_INDEX")

    # ====== Pydantic Settings ======
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    """Cache settings để dùng lại trong toàn ứng dụng."""
    return Settings()
