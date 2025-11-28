from __future__ import annotations

from langchain_core.runnables import RunnableConfig
from ..memory import LogicMemory
from ..state import RuntimeState
from typing import Any, Callable, Optional


def _append(history, speaker, content):
    if not content:
        return
    if history and history[-1] == {"speaker": speaker, "content": content}:
        return
    history.append({"speaker": speaker, "content": content})


def build_transition_node(
    logic_memory: LogicMemory,
    *,
    semantic_refresher: Optional[Callable[[RuntimeState, Optional[RunnableConfig]], RuntimeState]] = None,
    persona_refresher: Optional[Callable[[RuntimeState, Optional[RunnableConfig]], RuntimeState]] = None,
) -> Any:
    """
    Decide the next canon event based on evaluation status.
    """

    def _compute_score_rating(scores, total_criteria: int) -> int | None:
        if not scores:
            return None
        numeric_scores = [
            entry.get("score")
            for entry in scores
            if isinstance(entry, dict) and isinstance(entry.get("score"), (int, float))
        ]
        if not numeric_scores:
            return None
        divisor = total_criteria if total_criteria else len(numeric_scores)
        if divisor <= 0:
            return None
        average = sum(numeric_scores) / divisor
        rating = round(max(1.0, min(5.0, average)))
        return int(rating)

    def _pick_score_branch(event_summary: dict, total_criteria: int) -> tuple[int | None, str | None]:
        branches = event_summary.get("on_score_branches") or {}
        branch_map = {}
        if isinstance(branches, dict):
            for key, value in branches.items():
                try:
                    score_key = int(key)
                except (TypeError, ValueError):
                    continue
                if isinstance(value, str) and value.strip():
                    branch_map[score_key] = value.strip()
        rating = _compute_score_rating(event_summary.get("scores") or [], total_criteria)
        if rating is None:
            return None, None
        return rating, branch_map.get(rating)

    def transition(state: RuntimeState, _: RunnableConfig = None) -> RuntimeState:
        event_id = state.current_event
        event = logic_memory.get_event(event_id)
        if not event:
            state.system_notice = None
            state.max_turns = 0
            return state

        timeout_limit = event.get("timeout_turn")
        if timeout_limit:
            state.max_turns = timeout_limit
        else:
            state.max_turns = 0

        status = state.event_summary.get(event_id, "pending")
        total_criteria = len(event.get("success_criteria", [])) if event else 0
        remaining_success = state.event_summary.get("remaining_success_criteria", [])
        timeout_reached = (
            isinstance(timeout_limit, int)
            and timeout_limit > 0
            and state.turn_count >= timeout_limit
            and status != "pass"
        )

        next_event_id = event_id
        score_rating = None
        score_branch_target = None

        if timeout_reached:
            state.event_summary["last_result"] = "timeout_fail"
            state.event_summary[event_id] = "fail"
            state.event_summary["reason"] = "timeout"
            state.event_summary["remaining_success_criteria"] = list(
                event.get("success_criteria", [])
            ) if event else []
            state.event_summary["completed_success_criteria"] = []
            state.event_summary["partial_success_criteria"] = []
            score_rating, score_branch_target = _pick_score_branch(state.event_summary, total_criteria)
            if score_branch_target:
                state.system_notice = (
                    f"Hết lượt ({timeout_limit}). Chọn nhánh theo điểm {score_rating}/5 -> '{score_branch_target}'."
                )
                next_event_id = score_branch_target
            else:
                state.system_notice = (
                    f"Hết lượt ({timeout_limit}) nhưng không tìm thấy nhánh on_score_branches phù hợp."
                )
            state.turn_count = 0
        elif not remaining_success:
            score_rating, score_branch_target = _pick_score_branch(state.event_summary, total_criteria)
            if score_branch_target:
                state.system_notice = None
                next_event_id = score_branch_target
            else:
                state.system_notice = "Không tìm thấy nhánh on_score_branches phù hợp."
        else:
            state.system_notice = None
        if next_event_id != event_id:
            previous_persona_lines = (
                state.event_summary.get("_last_persona_dialogue") if isinstance(state.event_summary, dict) else []
            )
            if not isinstance(previous_persona_lines, list):
                previous_persona_lines = []
            # Đưa lời thoại cũ vào history để persona mới vẫn biết ngữ cảnh
            for line in previous_persona_lines:
                if not isinstance(line, dict):
                    continue
                speaker = line.get("speaker") or "NPC"
                content = line.get("content")
                _append(state.dialogue_history, speaker, content)

            state.current_event = next_event_id
            state.turn_count = 0
            state.event_summary["_last_scene_event"] = None
            state.event_summary[next_event_id] = "pending"
            state.event_summary["last_result"] = None
            state.event_summary["reason"] = None
            next_event = logic_memory.get_event(next_event_id)
            next_timeout = next_event.get("timeout_turn") if next_event else None
            state.max_turns = next_timeout if next_timeout else 0
            success_list = list(next_event.get("success_criteria", [])) if next_event else []
            state.event_summary["remaining_success_criteria"] = success_list
            state.event_summary["completed_success_criteria"] = []
            state.event_summary["partial_success_criteria"] = []
            state.event_summary["matched_actions"] = []
            state.event_summary["scores"] = []
            # Xóa cache lời thoại để tránh ghép 2 lần khi làm mới
            state.event_summary["_last_persona_dialogue"] = []

            # Làm mới scene/persona ngay trong lượt chuyển CE để có thoại tức thì
            if semantic_refresher:
                state = semantic_refresher(state, None)
            if persona_refresher:
                state = persona_refresher(state, None)

            # Chỉ giữ lời thoại mới của CE mới để trả về/append
            refreshed_lines = state.event_summary.get("_last_persona_dialogue")
            if not isinstance(refreshed_lines, list):
                refreshed_lines = []
            state.event_summary["_last_persona_dialogue"] = refreshed_lines
        return state

    return transition
