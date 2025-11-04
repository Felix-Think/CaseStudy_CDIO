from __future__ import annotations

from langchain_core.runnables import RunnableConfig

from ..runtime_store import RuntimeStateStore
from ..state import RuntimeState
from typing import Any

def build_egress_node(state_store: RuntimeStateStore) -> Any:
    """
    Persist runtime state and expose it for downstream tools (e.g., UI, logging).
    """

    def egress(state: RuntimeState, _: RunnableConfig = None) -> RuntimeState:
        state_store.save(state)
        return state

    return egress
