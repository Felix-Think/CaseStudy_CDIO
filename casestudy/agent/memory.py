from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from casestudy.app.core.config import get_settings as get_app_settings
from casestudy.app.db.database import get_mongo_client
from .const import AGENT_CASE_ROOT

logger = logging.getLogger(__name__)


@dataclass
class LogicMemory:
    case_id: str
    canon_events: Dict[str, Dict[str, Any]]
    event_sequence: List[str]
    personas: Dict[str, Dict[str, Any]]
    context: Dict[str, Any]

    @classmethod
    def load(cls, case_id: str) -> "LogicMemory":
        context, personas, skeleton = _load_case_payload(case_id)
        events = skeleton.get("canon_events", [])

        return cls(
            case_id=case_id,
            canon_events={event["id"]: event for event in events if event.get("id")},
            event_sequence=[event["id"] for event in events if event.get("id")],
            personas={persona["id"]: persona for persona in personas if persona.get("id")},
            context=context.get("initial_context") or context,
        )

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        return self.canon_events.get(event_id)

    def get_persona(self, persona_id: str) -> Optional[Dict[str, Any]]:
        return self.personas.get(persona_id)

    @property
    def first_event(self) -> Optional[str]:
        return self.event_sequence[0] if self.event_sequence else None


def _load_case_payload(case_id: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Dict[str, Any]]:
    """Load case payload using a priority order:
    1. MongoDB (preferred for dynamic updates)
    2. Local JSON files under cases/<case_id>/ (fallback when Mongo absent)

    Local file convention (all optional but skeleton + context recommended):
      cases/<case_id>/context.json
      cases/<case_id>/personas.json  (array of persona objects)
      cases/<case_id>/skeleton.json  (contains canon_events[])
    """
    context, personas, skeleton = _load_from_mongo(case_id)
    if context and skeleton:
        return context, personas or [], skeleton

    if not context and not skeleton:
        logger.warning("MongoDB không có dữ liệu cho case_id '%s', thử đọc local JSON.", case_id)
        try:
            local_context, local_personas, local_skeleton = _load_from_local(case_id)
        except FileNotFoundError as exc:
            raise ValueError(
                f"Không tìm thấy dữ liệu case_id '{case_id}' trong MongoDB hoặc local." 
            ) from exc
        if local_context and local_skeleton:
            logger.info("Đã load dữ liệu case_id '%s' từ local JSON.", case_id)
            return local_context, local_personas, local_skeleton
        raise ValueError(
            f"Case '{case_id}' thiếu context hoặc skeleton (Mongo & local đều trống)."
        )

    # Partial data (ví dụ có context nhưng thiếu skeleton) vẫn trả về để lớp trên quyết định.
    logger.warning(
        "Dữ liệu MongoDB cho case_id '%s' không đầy đủ (context=%s, skeleton=%s).", case_id, bool(context), bool(skeleton)
    )
    return context, personas or [], skeleton


def _load_from_mongo(case_id: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Dict[str, Any]]:
    client = get_mongo_client()
    if client is None:
        return {}, [], {}

    settings = get_app_settings()
    db = client[settings.mongo_db]

    context = db.contexts.find_one({"case_id": case_id}, {"_id": 0}) or {}
    personas = list(db.personas.find({"case_id": case_id}, {"_id": 0}) or [])
    skeleton = db.skeletons.find_one({"case_id": case_id}, {"_id": 0}) or {}
    return context, personas, skeleton


def _load_from_local(case_id: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Dict[str, Any]]:
    base = AGENT_CASE_ROOT / case_id
    if not base.exists():
        raise FileNotFoundError(f"Thư mục case local không tồn tại: {base}")

    def _read_json(path: Path) -> Dict | List | None:
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Không thể đọc file JSON '%s': %s", path, exc)
            return None

    context = _read_json(base / "context.json") or {}
    personas_raw = _read_json(base / "personas.json") or []
    skeleton = _read_json(base / "skeleton.json") or {}

    # Personas file có thể là dict với key "personas" hoặc list.
    if isinstance(personas_raw, dict):
        if "personas" in personas_raw and isinstance(personas_raw["personas"], list):
            personas_list = personas_raw["personas"]
        else:
            personas_list = []
    elif isinstance(personas_raw, list):
        personas_list = personas_raw
    else:
        personas_list = []

    return context, personas_list, skeleton
