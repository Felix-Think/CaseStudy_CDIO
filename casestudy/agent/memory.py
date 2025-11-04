from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .const import get_case_dir, get_logic_memory_dir


@dataclass
class LogicMemory:
    case_id: str
    canon_events: Dict[str, Dict[str, Any]]
    event_sequence: List[str]
    personas: Dict[str, Dict[str, Any]]
    context: Dict[str, Any]

    @classmethod
    def load(cls, case_id: str) -> "LogicMemory":
        logic_dir = get_logic_memory_dir(case_id)
        if not logic_dir.exists():
            logic_dir = get_case_dir(case_id)
            if not logic_dir.exists():
                raise FileNotFoundError(f"Không tìm thấy dữ liệu cho case_id '{case_id}'.")

        skeleton = _read_json(logic_dir / "skeleton.json")
        personas_payload = _read_json(logic_dir / "personas.json")
        context_payload = _read_json(logic_dir / "context.json")

        events = skeleton.get("canon_events", [])

        return cls(
            case_id=case_id,
            canon_events={event["id"]: event for event in events},
            event_sequence=[event["id"] for event in events if "id" in event],
            personas={
                persona["id"]: persona
                for persona in personas_payload.get("personas", [])
            },
            context=context_payload.get("initial_context", {}),
        )

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        return self.canon_events.get(event_id)

    def get_persona(self, persona_id: str) -> Optional[Dict[str, Any]]:
        return self.personas.get(persona_id)

    @property
    def first_event(self) -> Optional[str]:
        return self.event_sequence[0] if self.event_sequence else None


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
