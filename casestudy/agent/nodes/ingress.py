from __future__ import annotations

from langchain_core.runnables import RunnableConfig

from ..memory import LogicMemory
from ..runtime_store import RuntimeStateStore
from ..state import RuntimeState
from typing import Any

def build_ingress_node(
    _state_store: RuntimeStateStore,
    logic_memory: LogicMemory,
    *,
    default_event: str,
) -> Any:
    """
    Load an existing runtime state if available; otherwise initialise with defaults.
    """

    def _apply_event_limits(state: RuntimeState, event_id: str) -> None:
        event = logic_memory.get_event(event_id) if event_id else None
        state.max_turns = event.get("timeout_turn", 0) if event else 0

    def ingress(state: RuntimeState, config: RunnableConfig = None) -> RuntimeState:
        cfg = dict(config or {})

        explicit_start = cfg.get("start_event")
        should_reset = cfg.get("reset_state", False)

        if should_reset:
            target_event = explicit_start or default_event
            state.current_event = target_event
            state.turn_count = 0
            state.dialogue_history.clear()
            state.event_summary.clear()
        elif explicit_start:
            state.current_event = explicit_start
            state.turn_count = 0
            state.dialogue_history.clear()

        if not state.current_event:
            state.current_event = default_event

        state.system_notice = None
        state.event_summary["_last_persona_dialogue"] = []
        _apply_event_limits(state, state.current_event)

        current_event = logic_memory.get_event(state.current_event)
        if current_event:
            success_list = list(current_event.get("success_criteria", []))
            score_branches = current_event.get("on_score_branches") or {}

            state.event_summary[state.current_event] = state.event_summary.get(state.current_event, "pending")
            state.event_summary["remaining_success_criteria"] = success_list
            state.event_summary["completed_success_criteria"] = []
            state.event_summary["partial_success_criteria"] = []
            state.event_summary["matched_actions"] = []
            state.event_summary["scores"] = []
            state.event_summary["on_score_branches"] = score_branches
            state.event_summary["last_result"] = None
            state.event_summary["reason"] = None
        print("ingress","="*50)
        print(state)
        print("="*50)
        return state

    return ingress
