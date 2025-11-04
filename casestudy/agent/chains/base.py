from __future__ import annotations

from typing import Optional

from langchain_openai import ChatOpenAI

from ..const import DEFAULT_MODEL_NAME


def create_chat_model(
    model_name: Optional[str] = None,
    *,
    temperature: float = 0.2,
) -> ChatOpenAI:
    """
    Factory to keep a single place for ChatOpenAI configuration.

    Parameters
    ----------
    model_name:
        Override default OpenAI chat model if provided.
    temperature:
        Creativity level for downstream prompts.
    """
    resolved_model = model_name or DEFAULT_MODEL_NAME
    return ChatOpenAI(model=resolved_model, temperature=temperature)
