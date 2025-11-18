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

    def evaluate(state: RuntimeState, _: RunnableConfig = None) -> RuntimeState:
        event_id = state.current_event
        event = logic_memory.get_event(event_id)

        success_criteria_source = normalize_success_criteria(event.get("success_criteria", [])) if event else []
        remaining_key = f"{event_id}_remaining_success_criteria"
        completed_key = f"{event_id}_completed_success_criteria"

        remaining_success_criteria = state.event_summary.get(remaining_key)
        if remaining_success_criteria is None:
            remaining_success_criteria = list(success_criteria_source)
        else:
            remaining_success_criteria = normalize_success_criteria(remaining_success_criteria)

        existing_completed = state.event_summary.get(completed_key, [])

        result = action_chain(
            {
                "user_action": state.user_action,
                "success_criteria": remaining_success_criteria,
            }
        )

        updated_remaining = result.get("remaining_success_criteria", remaining_success_criteria)
        satisfied_now = result.get("satisfied_success_criteria", [])
        partial_matches = result.get("partial_success_criteria", [])

        updated_completed = [
            *existing_completed,
            *(criterion for criterion in satisfied_now if criterion not in existing_completed),
        ]

        state.event_summary[event_id] = result.get("status", "pending")
        state.event_summary[f"{event_id}_matched"] = result.get("matched_actions", [])
        state.event_summary[f"{event_id}_scores"] = result.get("scores", [])
        state.event_summary[remaining_key] = updated_remaining
        state.event_summary[completed_key] = updated_completed
        state.event_summary[f"{event_id}_partial"] = partial_matches

        return state

    return evaluate
