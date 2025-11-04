from __future__ import annotations

from typing import Any, Dict, List

from langchain_core.runnables import Runnable


def create_policy_lookup_chain(policy_index, *, top_k: int = 3) -> Runnable:
    """
    Lightweight retrieval-only chain for policy and safety guidance.
    Returns structured dictionaries to make downstream nodes deterministic.
    """

    def lookup(payload: Dict[str, Any]) -> List[Dict[str, str]]:
        user_action = (payload.get("user_action") or "").strip()
        if not user_action:
            return []

        results = policy_index.similarity_search(user_action, k=top_k)
        return [
            {
                "policy_id": doc.metadata.get("policy_id", f"policy_{idx}"),
                "policy_text": doc.page_content,
            }
            for idx, doc in enumerate(results, start=1)
        ]

    return lookup
