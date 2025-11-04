from __future__ import annotations

from typing import Any, Dict, List

from langchain_core.runnables import RunnableConfig

from ..memory import LogicMemory
from ..state import PersonaState, RuntimeState


def _extract_persona_profiles(digest_text: str) -> Dict[str, str]:
    profiles: Dict[str, str] = {}
    for line in digest_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        persona_id, _, description = stripped[2:].partition(":")
        persona_id = persona_id.strip()
        description = description.strip()
        if persona_id:
            profiles[persona_id] = description or "Chưa có mô tả."
    return profiles


def build_semantic_node(
    logic_memory: LogicMemory,
    scene_chain,
    persona_chain,
) -> Any:
    """
    Populate scene summary and active persona states using semantic memory chains.
    """

    def semantic(state: RuntimeState, _: RunnableConfig = None) -> RuntimeState:
        event = logic_memory.get_event(state.current_event)
        if not event:
            return state

        last_event_with_summary = state.event_summary.get("_last_scene_event")
        if last_event_with_summary != state.current_event:
            previous_summary = None
        else:
            previous_summary = state.scene_summary

        description = event.get("description", "")
        scene_summary = scene_chain(
            {
                "query": description,
                "event_title": event.get("title", state.current_event),
                "event_description": description,
                "previous_summary": previous_summary or "Chưa có dữ liệu.",
                "user_action": state.user_action or "Chưa ghi nhận.",
            }
        )
        state.scene_summary = scene_summary
        state.event_summary["_last_scene_event"] = state.current_event

        persona_ids: List[str] = [
            appearance["persona_id"]
            for appearance in event.get("npc_appearance", [])
            if appearance.get("persona_id") in logic_memory.personas
        ]

        if persona_ids:
            digest_text = persona_chain({"persona_ids": persona_ids})
            persona_profiles = _extract_persona_profiles(digest_text)
        else:
            persona_profiles = {}

        active_personas: Dict[str, PersonaState] = {}
        for persona_id in persona_ids:
            persona_data = logic_memory.get_persona(persona_id) or {}
            active_personas[persona_id] = PersonaState(
                id=persona_id,
                name=persona_data.get("name", persona_id),
                role=persona_data.get("role", "NPC"),
                emotion=persona_data.get("emotion_init", "neutral") or "neutral",
                trust=0.5,
                profile=persona_profiles.get(persona_id),
            )

        state.active_personas = active_personas
        return state

    return semantic
