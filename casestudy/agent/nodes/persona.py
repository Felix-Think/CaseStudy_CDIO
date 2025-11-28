from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List

from langchain_core.runnables import RunnableConfig

from ..chains.action import format_rubric_for_prompt, normalize_success_criteria
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


def _format_rubric_context(event_summary: Dict[str, Any]) -> str:
    remaining = normalize_success_criteria(event_summary.get("remaining_success_criteria") or [])
    completed = event_summary.get("completed_success_criteria") or []
    scores = event_summary.get("scores") or []

    parts: List[str] = []

    if remaining:
        parts.append("Tiêu chí còn lại:\n" + format_rubric_for_prompt(remaining))
    else:
        parts.append("Tất cả tiêu chí đã đạt.")

    if completed:
        completed_lines = "\n".join(f"- {item}" for item in completed)
        parts.append("Đã hoàn thành:\n" + completed_lines)

    score_lines: List[str] = []
    for score_entry in scores:
        if not isinstance(score_entry, dict):
            continue
        criterion = score_entry.get("criterion") or score_entry.get("description") or "Tiêu chí"
        score_value = score_entry.get("score")
        if score_value is None:
            continue
        analysis = score_entry.get("analysis")
        analysis_part = f" ({analysis})" if analysis else ""
        score_lines.append(f"- {criterion}: {score_value}/5{analysis_part}")
    if score_lines:
        parts.append("Điểm & nhận xét gần nhất:\n" + "\n".join(score_lines))

    return "\n".join(parts).strip() or "Chưa có rubric."


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
                emotion = item.get("emotion") or item.get("emotion_update") or ""
                if utterance:
                    parsed.append(
                        {
                            "persona_id": persona_id,
                            "speaker": persona_name,
                            "content": utterance.strip(),
                            "emotion": emotion.strip(),
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

        event_status = state.event_summary.get(state.current_event, "pending")
        rubric_context = _format_rubric_context(state.event_summary)
        persona_slate = _format_persona_slate(state.active_personas)
        recent_history = _format_recent_history(state.dialogue_history)
        allowed_personas = "\n".join(
            f"{persona.id} - {persona.name} ({persona.role})" for persona in state.active_personas.values()
        ) or "Không có nhân vật."

        raw_output = persona_dialogue_chain(
            {
                "event_title": event_title,
                "scene_summary": state.scene_summary or "Chưa có dữ liệu.",
                "event_status": event_status,
                "rubric_context": rubric_context,
                "user_action": user_action,
                "persona_slate": persona_slate,
                "allowed_personas": allowed_personas,
                "recent_history": recent_history,
            }
        )

        persona_lines = _parse_persona_dialogue(raw_output)
        allowed_ids = set(state.active_personas.keys())
        allowed_names = {persona.name for persona in state.active_personas.values()}
        persona_lines = [
            line
            for line in persona_lines
            if (
                (line.get("persona_id") in allowed_ids)
                or (line.get("speaker") in allowed_names and allowed_ids)
            )
        ]
        for line in persona_lines:
            target = None
            persona_id = line.get("persona_id") or ""
            speaker = line.get("speaker") or ""
            if persona_id and persona_id in state.active_personas:
                target = state.active_personas[persona_id]
            elif speaker:
                target = next(
                    (persona for persona in state.active_personas.values() if persona.name == speaker),
                    None,
                )
            if target:
                new_emotion = (line.get("emotion") or "").strip()
                if new_emotion:
                    target.emotion = new_emotion

        if not persona_lines:
            state.event_summary["_last_persona_dialogue"] = []
            return state

        state.event_summary["_last_persona_dialogue"] = persona_lines
        return state

    return persona_dialogue
