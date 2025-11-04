from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .memory import LogicMemory

class PersonaState(BaseModel):
    id: str
    name: str
    role: str
    emotion: str = "neutral"
    trust: float = 0.5
    profile: Optional[str] = None

class RuntimeState(BaseModel):
    case_id: str
    current_event: str
    turn_count: int = 0
    max_turns: int = 0
    scene_summary: Optional[str] = None
    active_personas: Dict[str, PersonaState] = Field(default_factory=dict) 
    dialogue_history: List[Dict[str, str]] = Field(default_factory=list)
    user_action: Optional[str] = None
    event_summary: Dict[str, Any] = Field(default_factory=dict)  # CE1, CE2...: pass/fail
    policy_flags: List[Dict[str, str]] = Field(default_factory=list)
    ai_reply: Optional[str] = None
    system_notice: Optional[str] = None

    def to_serializable(self) -> Dict[str, Any]:
        data = self.model_dump()
        data["active_personas"] = {
            persona_id: persona.model_dump()
            for persona_id, persona in self.active_personas.items()
        }
        return data

    @classmethod
    def from_serialized(cls, payload: Dict[str, Any]) -> "RuntimeState":
        payload = dict(payload)
        active_personas = payload.get("active_personas", {})
        normalized_personas: Dict[str, PersonaState] = {}
        for persona_id, persona_payload in active_personas.items():
            if isinstance(persona_payload, PersonaState):
                normalized_personas[persona_id] = persona_payload
            else:
                normalized_personas[persona_id] = PersonaState(**persona_payload)
        payload["active_personas"] = normalized_personas
        event_summary = payload.get("event_summary")
        if event_summary is None or not isinstance(event_summary, dict):
            event_summary = {}
        event_summary.setdefault("_last_scene_event", None)
        event_summary.setdefault("_last_persona_dialogue", [])
        payload["event_summary"] = event_summary
        return cls(**payload)

    @classmethod
    def initialize(
        cls,
        *,
        logic_memory: "LogicMemory",
        start_event: str,
        user_action: Optional[str] = None,
    ) -> "RuntimeState":
        event = logic_memory.get_event(start_event) or {}
        success_list = list(event.get("success_criteria", [])) if event else []

        event_summary: Dict[str, Any] = {
            "_last_scene_event": None,
            "_last_persona_dialogue": [],
            start_event: "pending",
            f"{start_event}_remaining_success_criteria": list(success_list),
            f"{start_event}_completed_success_criteria": [],
            f"{start_event}_partial": [],
            f"{start_event}_matched": [],
            f"{start_event}_scores": [],
            f"{start_event}_last_result": None,
            f"{start_event}_reason": None,
        }

        max_turns = event.get("timeout_turn", 0) if event else 0

        return cls(
            case_id=logic_memory.case_id,
            current_event=start_event,
            max_turns=max_turns or 0,
            user_action=user_action,
            event_summary=event_summary,
        )
