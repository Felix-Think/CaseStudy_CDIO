from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class CaseDocument:
    """Biểu diễn tối giản của bản ghi Case lưu trong MongoDB."""

    case_id: str
    topic: Optional[str]
    summary: Optional[str]
    location: Optional[str]
    time: Optional[str]
    who_first_on_scene: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CaseDocument":
        initial_context = data.get("initial_context") or {}
        index_event = initial_context.get("index_event") or {}
        scene = initial_context.get("scene") or {}

        return cls(
            case_id=data.get("case_id") or "",
            topic=data.get("topic"),
            summary=index_event.get("summary"),
            location=scene.get("location"),
            time=scene.get("time"),
            who_first_on_scene=index_event.get("who_first_on_scene"),
        )
