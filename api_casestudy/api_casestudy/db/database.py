from __future__ import annotations

from typing import Optional

import certifi
from pymongo import MongoClient
from pymongo.errors import ConfigurationError, PyMongoError

from api_casestudy.core.config import get_settings

_mongo_client: Optional[MongoClient] = None


def get_mongo_client() -> MongoClient:
    """
    Tạo hoặc trả về MongoDB client dùng chung cho Agent API.
    """
    global _mongo_client
    if _mongo_client is not None:
        return _mongo_client

    settings = get_settings()
    try:
        client = MongoClient(
            settings.mongo_uri,
            tls=True,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=settings.mongo_timeout_ms,
        )
        client.admin.command("ping")
    except (ConfigurationError, PyMongoError, OSError) as exc:
        raise RuntimeError(f"Không thể kết nối MongoDB: {exc}") from exc

    _mongo_client = client
    return _mongo_client
