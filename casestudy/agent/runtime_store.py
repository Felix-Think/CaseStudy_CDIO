from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .const import get_runtime_state_dir, get_runtime_state_path
from .state import RuntimeState


class RuntimeStateStore:
    """
    Simple JSON-backed persistence for runtime state.
    Keeping file I/O isolated makes nodes easier to test.
    """

    def __init__(self, case_id: str) -> None:
        self.case_id = case_id
        self.state_dir = get_runtime_state_dir(case_id)
        self.state_path = get_runtime_state_path(case_id)

    def load(self) -> Optional[RuntimeState]:
        if not self.state_path.exists():
            return None
        with self.state_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return RuntimeState.from_serialized(payload)

    def save(self, state: RuntimeState) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with self.state_path.open("w", encoding="utf-8") as handle:
            json.dump(state.to_serializable(), handle, ensure_ascii=False, indent=2)
