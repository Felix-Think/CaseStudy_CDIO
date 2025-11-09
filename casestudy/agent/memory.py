from __future__ import annotations


from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from casestudy.app.core.config import get_settings as get_app_settings
from casestudy.app.db.database import get_mongo_client


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
    """
    Thử ưu tiên đọc dữ liệu từ MongoDB; fallback sang local JSON khi không có.
    """
    context, personas, skeleton = _load_from_mongo(case_id)
    if not context and not personas and not skeleton:
        raise ValueError(f"Không tìm thấy dữ liệu case_id '{case_id}' trong MongoDB, thử đọc từ local.")
    if context and skeleton:
        return context, personas or [], skeleton

    return (
        context,
        personas or [],
        skeleton,
    )


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
