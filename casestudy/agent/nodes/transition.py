from __future__ import annotations

from langchain_core.runnables import RunnableConfig
from ..memory import LogicMemory
from ..state import RuntimeState
from typing import Any

def build_transition_node(logic_memory: LogicMemory) -> Any:
    """
    Decide the next canon event based on evaluation status.
    """

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
        remaining_success = state.event_summary.get("remaining_success_criteria", [])
        timeout_reached = (
            isinstance(timeout_limit, int)
            and timeout_limit > 0
            and state.turn_count >= timeout_limit
            and status != "pass"
        )

        next_event_id = event_id

        if timeout_reached:
            state.event_summary["last_result"] = "timeout_fail"
            state.event_summary[event_id] = "fail"
            state.event_summary["reason"] = "timeout"
            state.event_summary["remaining_success_criteria"] = list(
                event.get("success_criteria", [])
            ) if event else []
            state.event_summary["completed_success_criteria"] = []
            state.event_summary["partial_success_criteria"] = []
            retry_event_id = event.get("on_fail") or logic_memory.first_event or event_id
            retry_event = logic_memory.get_event(retry_event_id)
            retry_title = retry_event.get("title", retry_event_id) if retry_event else retry_event_id
            state.system_notice = (
                f"Bạn đã hết lượt ({timeout_limit}) cho sự kiện "
                f"'{event.get('title', event_id)}'. Hệ thống chuyển sang nhánh retry "
                f"'{retry_title}'."
            )
            next_event_id = retry_event_id
            state.turn_count = 0
        elif status == "pass" and event.get("on_success"):
            state.system_notice = None
            next_event_id = event["on_success"]
        elif not remaining_success:
            state.system_notice = None
            next_event_id = event.get("on_success") or event_id
        else:
            state.system_notice = None

        if next_event_id != event_id:
            state.current_event = next_event_id
            state.turn_count = 0
            state.event_summary["_last_scene_event"] = None
            state.event_summary["_last_persona_dialogue"] = []
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

        return state

    return transition
