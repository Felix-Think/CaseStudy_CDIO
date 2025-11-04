from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Cấu hình runtime cho Semantic API.
    Ưu tiên đọc từ biến môi trường, fallback giá trị mặc định.
    """

    mongo_uri: str = Field(
        default="mongodb+srv://nvt120205:thang1202@thangnguyen.8aiscbh.mongodb.net/",
        alias="MONGO_URI",
    )
    mongo_db: str = Field(default="case_study_db", alias="MONGO_DB")
    mongo_timeout_ms: int = Field(
        default=2000000,
        alias="MONGO_TIMEOUT_MS",
        description="Mongo client timeout (ms).",
    )

    embedding_model: str = Field(
        default="text-embedding-3-small",
        alias="EMBEDDING_MODEL",
    )
    vector_store_provider: Literal["chroma", "faiss"] = Field(
        default="chroma",
        alias="VECTOR_STORE_PROVIDER",
    )
    semantic_data_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2] / "casestudy" / "agent" / "cases",
        alias="SEMANTIC_DATA_DIR",
    )

    version: str = "1.0.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        frozen = True
        extra = "ignore"
        populate_by_name = True


@lru_cache
def get_settings() -> Settings:
    """
    Trả về singleton Settings.
    """
    settings = Settings()
    settings.semantic_data_dir.mkdir(parents=True, exist_ok=True)
    return settings
