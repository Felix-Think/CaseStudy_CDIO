from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List

from langchain_core.runnables import RunnableConfig

from ..memory import LogicMemory
from ..state import PersonaState, RuntimeState


def _format_recent_history(history: Iterable[Dict[str, str]], limit: int = 5) -> str:
    window = list(history)[-limit:]
    if not window:
        return "Chưa có hội thoại."
    return "\n".join(f"{turn.get('speaker', 'unknown')}: {turn.get('content', '')}" for turn in window)


def _format_persona_slate(personas: Dict[str, PersonaState]) -> str:
    if not personas:
        return "Không có nhân vật."
    lines: List[str] = []
    for persona in personas.values():
        profile = persona.profile or "Không có ghi chú."
        lines.append(
            f"- {persona.name} ({persona.role}) | cảm xúc: {persona.emotion} | trust: {persona.trust:.2f} | ghi chú: {profile}"
        )
    return "\n".join(lines)


def _parse_persona_dialogue(raw_output: str) -> List[Dict[str, str]]:
    raw_output = raw_output.strip()
    if not raw_output:
        return []

    if raw_output.startswith("```"):
        lines = []
        for line in raw_output.splitlines():
            stripped = line.strip()
            if stripped.startswith("```"):
                continue
            lines.append(line)
        raw_output = "\n".join(lines).strip()

    parsed: List[Dict[str, str]] = []
    try:
        data = json.loads(raw_output)
        if isinstance(data, dict):
            data = data.get("responses") or data.get("dialogue") or data
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                persona_id = item.get("persona_id") or ""
                persona_name = item.get("persona_name") or persona_id or "NPC"
                utterance = item.get("utterance") or item.get("text") or ""
                if utterance:
                    parsed.append(
                        {
                            "persona_id": persona_id,
                            "speaker": persona_name,
                            "content": utterance.strip(),
                        }
                    )
    except json.JSONDecodeError:
        for line in raw_output.splitlines():
            stripped = line.strip()
            if ":" not in stripped:
                continue
            speaker, content = stripped.split(":", 1)
            if content.strip():
                parsed.append(
                    {
                        "persona_id": "",
                        "speaker": speaker.strip(),
                        "content": content.strip(),
                    }
                )

    return parsed


def build_persona_dialogue_node(
    logic_memory: LogicMemory,
    persona_dialogue_chain,
) -> Any:
    """
    Generate NPC dialogue snippets in reaction to the learner action.
    """

    def persona_dialogue(state: RuntimeState, _: RunnableConfig = None) -> RuntimeState:
        if not state.active_personas:
            return state

        user_action = state.user_action or ""
        if not user_action.strip():
            return state

        event = logic_memory.get_event(state.current_event)
        event_title = event.get("title", state.current_event) if event else state.current_event

        persona_slate = _format_persona_slate(state.active_personas)
        recent_history = _format_recent_history(state.dialogue_history)

        raw_output = persona_dialogue_chain(
            {
                "event_title": event_title,
                "scene_summary": state.scene_summary or "Chưa có dữ liệu.",
                "user_action": user_action,
                "persona_slate": persona_slate,
                "recent_history": recent_history,
            }
        )

        persona_lines = _parse_persona_dialogue(raw_output)
        if not persona_lines:
            state.event_summary["_last_persona_dialogue"] = []
            return state

        state.event_summary["_last_persona_dialogue"] = persona_lines
        return state

    return persona_dialogue
