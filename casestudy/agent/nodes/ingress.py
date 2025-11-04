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
            remaining_key = f"{state.current_event}_remaining_success_criteria"
            completed_key = f"{state.current_event}_completed_success_criteria"
            partial_key = f"{state.current_event}_partial"

            state.event_summary.setdefault(
                remaining_key, list(current_event.get("success_criteria", []))
            )
            state.event_summary.setdefault(completed_key, [])
            state.event_summary.setdefault(partial_key, [])

        return state

    return ingress
