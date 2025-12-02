from __future__ import annotations

from langchain_core.runnables import RunnableConfig
from ..state import RuntimeState
from typing import Any

def build_policy_node(policy_chain) -> Any:
    """
    Attach nearest policy guidance based on the latest user action.
    """

    def policy(state: RuntimeState, _: RunnableConfig = None) -> RuntimeState:
        raw_flags = policy_chain({"user_action": state.user_action}) or []
        seen = set()
        deduped = []
        for flag in raw_flags:
            if not isinstance(flag, dict):
                continue
            key = (flag.get("policy_id"), flag.get("policy_text"))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(flag)
        state.policy_flags = deduped
        return state

    return policy
