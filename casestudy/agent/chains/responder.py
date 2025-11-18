from __future__ import annotations

from typing import Any, Dict, List, Sequence, Union

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from ..const import DEFAULT_CASE_ID


def _stringify_criteria(values: Union[str, Sequence[Any], None]) -> str:
    if isinstance(values, str):
        return values or "Không còn."
    if isinstance(values, Sequence):
        parts: List[str] = []
        for item in values:
            if isinstance(item, dict):
                description = str(item.get("description", "")).strip()
                if description:
                    parts.append(description)
            else:
                text = str(item).strip()
                if text:
                    parts.append(text)
        return "; ".join(parts) if parts else "Không còn."
    return "Không còn."


def create_responder_chain(
    llm,
    *,
    case_id: str = DEFAULT_CASE_ID,
) -> Runnable:
    """
    Generate facilitator-style feedback for the trainee using the consolidated state.
    The prompt emphasises coaching language that should transfer across case studies.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "Bạn là AI facilitator hỗ trợ học viên trong mô phỏng tình huống y khoa. "
                    "Hãy phản hồi súc tích, hướng dẫn tiếp theo và giữ thái độ hỗ trợ."
                ),
            ),
            (
                "human",
                (
                    "Case ID: {case_id}\n"
                    "Canon Event: {event_title}\n"
                    "Tóm tắt bối cảnh: {scene_summary}\n"
                    "Tiêu chí còn lại: {success_criteria}\n"
                    "Tiêu chí đã đạt: {completed_success_criteria}\n"
                    "Tiêu chí cần chú ý: {partial_success_criteria}\n"
                    "Nhân vật đang hiện diện: {persona_overview}\n"
                    "Lịch sử hội thoại: {dialogue_history}\n"
                    "Vi phạm hoặc lưu ý policy: {policy_flags}\n"
                    "Số lượt đã dùng: {turn_count}\n"
                    "Giới hạn lượt: {max_turns}\n"
                    "Thông báo hệ thống: {system_notice}\n"
                    "Hành động gần nhất của học viên: {user_action}\n\n"
                    "Nếu có thông báo hệ thống, hãy ghi nhận rõ tình trạng và hướng dẫn cách bắt đầu lại.\n"
                    "Hãy trả lời tối đa 4 câu tiếng Việt:\n"
                    "1. Nhận xét nhanh về tình hình hiện tại.\n"
                    "2. Đánh giá hành động học viên (nếu có) dựa trên yêu cầu.\n"
                    "3. Gợi ý bước tiếp theo cụ thể.\n"
                    "4. Nhắc nhở an toàn hoặc policy nếu cần."
                ),
            ),
        ]
    )
    chain = prompt | llm | StrOutputParser()

    def respond(payload: Dict[str, Any]) -> str:
        dialogue_history: List[Dict[str, str]] = payload.get("dialogue_history", [])
        history_text = "\n".join(
            f"{turn.get('speaker', 'unknown')}: {turn.get('content', '')}"
            for turn in dialogue_history
        ) or "Chưa có hội thoại."

        success_criteria = payload.get("success_criteria")
        if success_criteria is None:
            # Backwards compatibility for older payloads.
            success_criteria = payload.get("required_actions", [])
        success_criteria_text = _stringify_criteria(success_criteria)

        completed_success = payload.get("completed_success_criteria", [])
        if isinstance(completed_success, list):
            completed_text = "; ".join(completed_success) or "Chưa đạt."
        else:
            completed_text = completed_success or "Chưa đạt."

        partial_success = payload.get("partial_success_criteria", [])
        if isinstance(partial_success, list):
            partial_text = "; ".join(partial_success) or "Không có."
        else:
            partial_text = partial_success or "Không có."

        policy_flags = payload.get("policy_flags")
        if isinstance(policy_flags, list) and policy_flags:
            policy_text = "; ".join(flag.get("policy_text", "") for flag in policy_flags)
        else:
            policy_text = "Không có."

        max_turns_value = payload.get("max_turns")
        if isinstance(max_turns_value, int) and max_turns_value > 0:
            max_turns_text = str(max_turns_value)
        elif isinstance(max_turns_value, str) and max_turns_value:
            max_turns_text = max_turns_value
        else:
            max_turns_text = "Không giới hạn"

        turn_count = payload.get("turn_count", 0)
        system_notice = payload.get("system_notice") or "Không có."

        return chain.invoke(
            {
                "case_id": case_id,
                "event_title": payload.get("event_title", "Sự kiện"),
                "scene_summary": payload.get("scene_summary", "Chưa có dữ liệu."),
                "success_criteria": success_criteria_text,
                "completed_success_criteria": completed_text,
                "partial_success_criteria": partial_text,
                "persona_overview": payload.get("persona_overview", "Không có."),
                "dialogue_history": history_text,
                "policy_flags": policy_text,
                "user_action": payload.get("user_action", "Chưa ghi nhận."),
                "turn_count": turn_count,
                "max_turns": max_turns_text,
                "system_notice": system_notice,
            }
        )

    return respond
