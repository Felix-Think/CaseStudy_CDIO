from __future__ import annotations

from langchain_core.runnables import RunnableConfig
from ..memory import LogicMemory
from ..state import RuntimeState
from typing import Any

def build_responder_node(
    logic_memory: LogicMemory,
    responder_chain,
) -> Any:
    """
    Produce facilitator feedback via the responder chain.
    """

    def respond(state: RuntimeState, _: RunnableConfig = None) -> RuntimeState:
        event_id = state.current_event
        event = logic_memory.get_event(event_id)
        persona_overview = [
            f"{persona.name} ({persona.role}) - cảm xúc: {persona.emotion}"
            for persona in state.active_personas.values()
        ]

        remaining_key = f"{event_id}_remaining_success_criteria"
        completed_key = f"{event_id}_completed_success_criteria"
        partial_key = f"{event_id}_partial"

        base_success = event.get("success_criteria", []) if event else []
        remaining_success = state.event_summary.get(remaining_key, base_success)
        completed_success = state.event_summary.get(completed_key, [])
        partial_success = state.event_summary.get(partial_key, [])

        ai_reply = responder_chain(
            {
                "event_title": event.get("title", event_id) if event else event_id,
                "scene_summary": state.scene_summary or "Chưa có dữ liệu.",
                "success_criteria": remaining_success,
                "completed_success_criteria": completed_success,
                "partial_success_criteria": partial_success,
                # Provide legacy key until downstream consumers migrate fully.
                "required_actions": remaining_success,
                "persona_overview": "; ".join(persona_overview) or "Không có.",
                "dialogue_history": state.dialogue_history,
                "policy_flags": state.policy_flags,
                "user_action": state.user_action or "Chưa ghi nhận.",
                "turn_count": state.turn_count,
                "max_turns": state.max_turns,
                "system_notice": state.system_notice,
            }
        )

        state.ai_reply = ai_reply
        if not state.system_notice:
            state.turn_count = state.turn_count + 1
        return state

    return respond
