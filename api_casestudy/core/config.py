from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Cấu hình runtime cho Agent API.
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
    state_db: str = Field(
        default="case_state_store",
        alias="STATE_DB",
        description="Tên MongoDB database dùng để lưu runtime state/logs.",
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
    return settings
