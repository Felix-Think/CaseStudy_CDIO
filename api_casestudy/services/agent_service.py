from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

from casestudy.agent import LogicMemory, RuntimeState
from casestudy.agent.graph import CaseStudyGraphBuilder
from casestudy.utils import semantic_extract as semantic_utils

from api_casestudy.schemas import (
    AgentSessionCreateRequest,
    AgentSessionCreateResponse,
    AgentTurnRequest,
    AgentTurnResponse,
)


def _normalize_runtime_state(result) -> RuntimeState:
    if isinstance(result, RuntimeState):
        return result
    if isinstance(result, dict):
        return RuntimeState.from_serialized(result)
    raise TypeError("Không thể chuyển đổi kết quả graph sang RuntimeState.")


class _InMemoryStateStore:
    """
    RuntimeStateStore tối giản lưu trữ trong bộ nhớ để tránh ghi file.
    """

    def __init__(self) -> None:
        self._state: Optional[RuntimeState] = None

    def load(self) -> Optional[RuntimeState]:
        return self._state

    def save(self, state: RuntimeState) -> None:
        self._state = state


def _configure_semantic_module(case_id: str) -> None:
    """
    Cập nhật module semantic_extract để load đúng namespace Pinecone cho case_id.
    """
    semantic_utils.configure_paths(case_id)


@dataclass
class AgentSession:
    session_id: str
    case_id: str
    graph: Any
    state: RuntimeState
    state_store: _InMemoryStateStore

    def to_response(self) -> AgentSessionCreateResponse:
        return AgentSessionCreateResponse(
            session_id=self.session_id,
            case_id=self.case_id,
            state=self.state.to_serializable(),
        )

    def run_turn(self, *, user_action: Optional[str] = None, config: Optional[Dict] = None) -> RuntimeState:
        if user_action is not None:
            cleaned = user_action.strip()
            self.state.user_action = cleaned
        invoke_config = config or {}
        result = self.graph.invoke(self.state, config=invoke_config)
        self.state = _normalize_runtime_state(result)
        self.state_store.save(self.state)
        return self.state


class AgentService:
    """
    Quản lý vòng đời agent sessions, wrap LangGraph runner.
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, AgentSession] = {}

    def create_session(self, payload: AgentSessionCreateRequest) -> AgentSessionCreateResponse:
        try:
            logic_memory = LogicMemory.load(payload.case_id)
        except FileNotFoundError as exc:
            raise ValueError(f"Không tìm thấy dữ liệu logic cho case_id '{payload.case_id}'.") from exc

        start_event = payload.start_event or logic_memory.first_event or "CE1"

        _configure_semantic_module(payload.case_id)

        state_store = _InMemoryStateStore()
        builder = CaseStudyGraphBuilder(
            case_id=payload.case_id,
            model_name=payload.model_name,
        )
        builder.state_store = state_store
        graph = builder.build().compile()

        initial_user_action = payload.user_action.strip() if payload.user_action else None

        state = RuntimeState.initialize(
            logic_memory=logic_memory,
            start_event=start_event,
            user_action=initial_user_action,
        )

        initial_config: Dict[str, Any] = {}
        if payload.reset_state:
            initial_config["reset_state"] = True
        if payload.start_event:
            initial_config["start_event"] = payload.start_event

        state_store.save(state)
        try:
            result_state = _normalize_runtime_state(
                graph.invoke(state, config=initial_config)
            )
        except Exception as exc:  # pragma: no cover - fallback
            raise RuntimeError("Không thể khởi tạo agent session.") from exc
        state_store.save(result_state)

        session_id = uuid.uuid4().hex
        session = AgentSession(
            session_id=session_id,
            case_id=payload.case_id,
            graph=graph,
            state=result_state,
            state_store=state_store,
        )
        self._sessions[session_id] = session
        return session.to_response()

    def send_turn(self, payload: AgentTurnRequest) -> AgentTurnResponse:
        session = self._sessions.get(payload.session_id)
        if not session:
            raise KeyError(f"Session '{payload.session_id}' không tồn tại.")

        if not payload.user_input or not payload.user_input.strip():
            raise ValueError("user_input không được để trống.")

        config = {"reset_state": True} if payload.reset_state else {}
        if payload.start_event:
            config["start_event"] = payload.start_event

        state = session.run_turn(user_action=payload.user_input, config=config)
        return AgentTurnResponse(
            session_id=session.session_id,
            case_id=session.case_id,
            state=state.to_serializable(),
        )

    def end_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
