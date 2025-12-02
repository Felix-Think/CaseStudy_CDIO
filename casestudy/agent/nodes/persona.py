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

def _format_score_summary(event_summary: Dict[str, Any]) -> str:
    """
    Tóm tắt điểm số/nhận xét ngắn gọn để persona điều chỉnh cảm xúc theo lượt.
    """
    scores = event_summary.get("scores") or []
    if not scores:
        return "Chưa có điểm."
    lines: List[str] = []
    for entry in scores:
        if not isinstance(entry, dict):
            continue
        criterion = entry.get("criterion") or entry.get("description") or "Tiêu chí"
        score_val = entry.get("score")
        analysis = entry.get("analysis") or ""
        if score_val is None:
            continue
        lines.append(f"{criterion}: {score_val}/5{' - ' + analysis if analysis else ''}")
    return "\n".join(lines) or "Chưa có điểm."

def _latest_score_value(event_summary: Dict[str, Any]) -> str:
    scores = event_summary.get("scores") or []
    numeric = None
    for entry in scores:
        if isinstance(entry, dict) and isinstance(entry.get("score"), (int, float)):
            numeric = entry.get("score")
    return str(numeric) if numeric is not None else "Chưa có điểm."

def _latest_score_number(event_summary: Dict[str, Any]) -> float | None:
    scores = event_summary.get("scores") or []
    numeric = None
    for entry in scores:
        if isinstance(entry, dict) and isinstance(entry.get("score"), (int, float)):
            numeric = float(entry.get("score"))
    return numeric

def _preadjust_emotion_by_score(active_personas: Dict[str, PersonaState], latest_score: float | None) -> None:
    """
    Cập nhật emotion trước khi gọi LLM để prompt sử dụng trạng thái mới.
    score >=4: dịu/hài lòng; score=3: trung tính; score<=2: bức xúc.
    """
    if latest_score is None:
        return
    for persona in active_personas.values():
        if latest_score >= 4:
            persona.emotion = "hài lòng"
        elif latest_score == 3:
            persona.emotion = "trung tính"
        else:
            persona.emotion = "tức giận"

def _is_harsh_text(text: str) -> bool:
    lowered = text.lower()
    harsh_keywords = [
        "không thể chờ",
        "phải hoàn tiền",
        "không chấp nhận",
        "tức giận",
        "bức xúc",
        "khiếu nại",
        "đòi bồi thường",
        "bất tiện",
    ]
    return any(keyword in lowered for keyword in harsh_keywords)


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
        score_summary = _format_score_summary(state.event_summary)
        latest_score = _latest_score_value(state.event_summary)
        latest_score_num = _latest_score_number(state.event_summary)
        _preadjust_emotion_by_score(state.active_personas, latest_score_num)
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
                "turn_count": state.turn_count,
                "score_summary": score_summary,
                "latest_score": latest_score,
            }
        )

        persona_lines = _parse_persona_dialogue(raw_output)
        existing_contents = {
            (turn.get("content") or "").strip().lower()
            for turn in state.dialogue_history
            if isinstance(turn, dict)
        }
        persona_lines = [
            line for line in persona_lines
            if (line.get("content") or "").strip().lower() not in existing_contents
        ]
        if latest_score_num is not None and latest_score_num >= 4:
            adjusted_lines = []
            for line in persona_lines:
                content = (line.get("content") or "").strip()
                emotion = (line.get("emotion") or "").strip().lower()
                if emotion in {"tức giận", "angry"} or _is_harsh_text(content):
                    # Cưỡng ép trạng thái hợp tác khi điểm cao.
                    line["emotion"] = "hài lòng"
                    line["content"] = (
                        "Cảm ơn đã xử lý, tôi sẽ chờ thêm vài phút để phòng được dọn sạch. "
                        "Nếu có gì cần thêm tôi sẽ báo."
                    )
                adjusted_lines.append(line)
            persona_lines = adjusted_lines
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
                # Chuẩn hoá persona_id/speaker để khớp với active_personas, tránh mismatch (P1 vs lan_1).
                line["persona_id"] = target.id
                line["speaker"] = target.name
                new_emotion = (line.get("emotion") or "").strip()
                if new_emotion:
                    target.emotion = new_emotion

        if not persona_lines:
            state.event_summary["_last_persona_dialogue"] = []
            return state

        state.event_summary["_last_persona_dialogue"] = persona_lines
        return state

    return persona_dialogue
