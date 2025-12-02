from __future__ import annotations

from langchain_core.runnables import RunnableConfig

from ..state import RuntimeState
from typing import Any

def _append(history, speaker, content):
    if not content:
        return
    if history and history[-1] == {"speaker": speaker, "content": content}:
        return
    history.append({"speaker": speaker, "content": content})


def build_state_update_node(*, policy_penalty: float = 0.1) -> Any:
    """
    Synchronise dialogue history and apply simple trust adjustments.
    """

    def _latest_score(event_summary: dict) -> float | None:
        scores = event_summary.get("scores") or []
        numeric = None
        for entry in scores:
            if isinstance(entry, dict) and isinstance(entry.get("score"), (int, float)):
                numeric = float(entry.get("score"))
        return numeric

    def _is_harsh_text(text: str) -> bool:
        lowered = (text or "").lower()
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

    def update(state: RuntimeState, _: RunnableConfig = None) -> RuntimeState:
        _append(state.dialogue_history, "user", state.user_action)

        persona_dialogue = state.event_summary.get("_last_persona_dialogue") or []
        latest_score = _latest_score(state.event_summary)
        if isinstance(persona_dialogue, list) and latest_score is not None and latest_score >= 4:
            softened = []
            for line in persona_dialogue:
                if not isinstance(line, dict):
                    continue
                content = (line.get("content") or "").strip()
                emotion = (line.get("emotion") or "").strip().lower()
                if emotion in {"tức giận", "angry"} or _is_harsh_text(content):
                    line["emotion"] = "hài lòng"
                    line["content"] = (
                        "Cảm ơn đã xử lý, tôi sẽ chờ thêm vài phút để phòng được dọn sạch. "
                        "Nếu cần hỗ trợ thêm tôi sẽ báo."
                    )
                softened.append(line)
            state.event_summary["_last_persona_dialogue"] = softened
            persona_dialogue = softened

        if isinstance(persona_dialogue, list):
            for line in persona_dialogue:
                if not isinstance(line, dict):
                    continue
                speaker = line.get("speaker") or "NPC"
                content = line.get("content")
                _append(state.dialogue_history, speaker, content)

        num_flags = len(state.policy_flags or [])
        if num_flags:
            for persona in state.active_personas.values():
                persona.trust = max(0.0, persona.trust - policy_penalty * num_flags)
                persona.emotion = persona.emotion or "neutral"
                if persona.trust < 0.3:
                    persona.emotion = "lo lắng"

        state.user_action = None
        return state

    return update
