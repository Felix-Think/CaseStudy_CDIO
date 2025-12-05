from __future__ import annotations

from langchain_core.runnables import RunnableConfig
from ..memory import LogicMemory
from ..state import RuntimeState
from typing import Any
from ..chains.action import normalize_success_criteria

def build_action_node(
    logic_memory: LogicMemory,
    action_chain,
) -> Any:
    """
    Evaluate learner actions against the current canon event requirements.
    """

    def _compute_rating(scores: list[dict], total_criteria: int) -> int | None:
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

    def evaluate(state: RuntimeState, config: RunnableConfig = None) -> RuntimeState:
        cfg = dict(config or {})
        cfg_configurable = cfg.get("configurable") or {}
        skip_action = bool(cfg.get("skip_action") or cfg_configurable.get("skip_action"))

        event_id = state.current_event
        event = logic_memory.get_event(event_id)

        success_criteria_source = normalize_success_criteria(event.get("success_criteria", [])) if event else []
        remaining_key = "remaining_success_criteria"
        completed_key = "completed_success_criteria"

        remaining_success_criteria = state.event_summary.get(remaining_key)
        if remaining_success_criteria is None:
            remaining_success_criteria = list(success_criteria_source)
        else:
            remaining_success_criteria = normalize_success_criteria(remaining_success_criteria)

        existing_completed = state.event_summary.get(completed_key, [])

        # Cho phép bỏ qua chấm điểm ở lượt khởi tạo (skip_action=True).
        if skip_action:
            result = {
                "status": "pending",
                "matched_actions": [],
                "remaining_success_criteria": remaining_success_criteria,
                "scores": [],
                "satisfied_success_criteria": [],
            }
        else:
            result = action_chain(
                {
                    "user_action": state.user_action,
                    "success_criteria": remaining_success_criteria,
                }
            )

        updated_remaining = result.get("remaining_success_criteria", remaining_success_criteria)
        satisfied_now = result.get("satisfied_success_criteria", [])

        updated_completed = [
            *existing_completed,
            *(criterion for criterion in satisfied_now if criterion not in existing_completed),
        ]

        state.event_summary[event_id] = result.get("status", "pending")
        state.event_summary["matched_actions"] = result.get("matched_actions", [])
        current_scores = result.get("scores", [])
        state.event_summary["scores"] = current_scores
        rating = _compute_rating(current_scores, len(success_criteria_source))
        state.event_summary["last_score"] = rating
        history = state.event_summary.get("score_history")
        if not isinstance(history, list):
            history = []
        history.append(
            {
                "event_id": event_id,
                "turn_count": state.turn_count,
                "scores": current_scores,
                "rating": rating,
            }
        )
        state.event_summary["score_history"] = history
        state.event_summary[remaining_key] = updated_remaining
        state.event_summary[completed_key] = updated_completed

        return state

    return evaluate
