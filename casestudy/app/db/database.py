from __future__ import annotations

from typing import Optional

import certifi
from pymongo import MongoClient
from pymongo.errors import ConfigurationError, PyMongoError

from casestudy.app.core.config import get_settings

_mongo_client: Optional[MongoClient] = None


def get_mongo_client() -> Optional[MongoClient]:
    """
    Trả về MongoDB client được cache, nếu kết nối thất bại sẽ trả None.
    Luôn bật TLS cùng CA bundle từ certifi để tương thích Atlas.
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
        print(f"⚠️ Không thể khởi tạo MongoClient: {exc}")
        _mongo_client = None
    else:
        _mongo_client = client

    return _mongo_client
