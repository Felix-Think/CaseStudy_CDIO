from __future__ import annotations

from langchain_core.runnables import RunnableConfig
from ..state import RuntimeState
from typing import Any

def build_policy_node(policy_chain) -> Any:
    """
    Attach nearest policy guidance based on the latest user action.
    """

    def policy(state: RuntimeState, _: RunnableConfig = None) -> RuntimeState:
        state.policy_flags = policy_chain({"user_action": state.user_action})
        return state

    return policy
