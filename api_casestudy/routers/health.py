from __future__ import annotations

import os
import time
import socket
from typing import Any, Dict

from fastapi import APIRouter

from casestudy.app.db.database import get_mongo_client
from casestudy.app.core.config import get_settings as get_app_settings

router = APIRouter(prefix="/health", tags=["health"])


def _check_mongo() -> Dict[str, Any]:
    start = time.time()
    client = get_mongo_client()
    ok = client is not None
    latency_ms = int((time.time() - start) * 1000)
    db_name = None
    if ok:
        try:
            db_name = get_app_settings().mongo_db
        except Exception:
            db_name = None
    return {"connected": ok, "latency_ms": latency_ms, "db": db_name}


def _env_flag(name: str) -> bool:
    return bool(os.getenv(name))


def _check_pinecone() -> Dict[str, Any]:
    # Chỉ kiểm tra có API key & index env; không gọi mạng (nhẹ).
    api_key = _env_flag("PINECONE_API_KEY")
    scene_index = os.getenv("PINECONE_SCENE_INDEX")
    persona_index = os.getenv("PINECONE_PERSONA_INDEX")
    policy_index = os.getenv("PINECONE_POLICY_INDEX")
    return {
        "api_key": api_key,
        "scene_index": bool(scene_index),
        "persona_index": bool(persona_index),
        "policy_index": bool(policy_index),
    }


def _runtime_info() -> Dict[str, Any]:
    return {
        "hostname": socket.gethostname(),
        "allow_pinecone_fallback": os.getenv("ALLOW_PINECONE_FALLBACK", "1"),
    }


@router.get("", summary="Extended health status")
async def health_root() -> Dict[str, Any]:
    return {
        "status": "ok",
        "mongo": _check_mongo(),
        "pinecone": _check_pinecone(),
        "runtime": _runtime_info(),
    }
