from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

from casestudy.agent import LogicMemory, RuntimeState
from casestudy.agent.const import DEFAULT_MODEL_NAME
from casestudy.agent.graph import CaseStudyGraphBuilder
from casestudy.utils import semantic_extract as semantic_utils

from api_casestudy.schemas import (
    AgentSessionCreateRequest,
    AgentSessionCreateResponse,
    AgentSessionHistoryResponse,
    AgentTurnLog,
    AgentTurnRequest,
    AgentTurnResponse,
)
from api_casestudy.services.tts_engine import TTSEngine, TTSPayload
from api_casestudy.services.voice_selector import VoiceSelector
from api_casestudy.services.state_repository import ConversationStateRepository


logger = logging.getLogger(__name__)


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


def _is_user_speaker(label: Optional[str]) -> bool:
    if not label:
        return False
    normalized = label.strip().lower()
    if not normalized:
        return False
    try:
        ascii_normalized = normalized.encode("ascii", "ignore").decode("ascii")
    except Exception:
        ascii_normalized = normalized
    markers = (
        "user",
        "nguoi hoc",
        "hoc vien",
        "learner",
        "ban",
        "hoc sinh",
    )
    for candidate in (normalized, ascii_normalized):
        if any(marker in candidate for marker in markers if marker):
            return True
    return False

@dataclass
class DialogueLine:
    speaker: str
    text: str
    persona_id: Optional[str] = None


def _render_dialogue_lines(entries: list[dict]) -> list[DialogueLine]:
    lines: list[DialogueLine] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        speaker = (
            entry.get("speaker")
            or entry.get("persona")
            or entry.get("role")
            or "Nhân vật"
        )
        if _is_user_speaker(speaker):
            continue
        content = (
            entry.get("content")
            or entry.get("text")
            or entry.get("message")
            or ""
        ).strip()
        if not content:
            continue
        persona_id = (
            entry.get("persona_id")
            or entry.get("personaId")
            or entry.get("id")
            or None
        )
        lines.append(DialogueLine(speaker=speaker, text=content, persona_id=persona_id))
    return lines


def _extract_dialogue_lines(state: RuntimeState) -> list[DialogueLine]:
    summary_dialogue = state.event_summary.get("_last_persona_dialogue") or []
    lines = _render_dialogue_lines(summary_dialogue)
    if lines:
        return lines

    history = state.dialogue_history or []
    if history:
        recent = history[-6:]
        lines = _render_dialogue_lines(recent)
        if lines:
            return lines

    return []


def _format_dialogue_text(lines: list[DialogueLine]) -> Optional[str]:
    if not lines:
        return None
    formatted = " ".join(f"{line.speaker}: {line.text}" for line in lines)
    return formatted or None


@dataclass
class AgentSession:
    session_id: str
    case_id: str
    model_name: str
    graph: Any
    state: RuntimeState
    state_store: _InMemoryStateStore

    def to_response(
        self,
        *,
        tts_payload: Optional[TTSPayload] = None,
        tts_segments: Optional[list[dict]] = None,
        tts_text: Optional[str] = None,
    ) -> AgentSessionCreateResponse:
        return AgentSessionCreateResponse(
            session_id=self.session_id,
            case_id=self.case_id,
            state=self.state.to_serializable(),
            tts_audio=tts_payload.audio_b64 if tts_payload else None,
            tts_mime_type=tts_payload.mime_type if tts_payload else None,
            tts_model=tts_payload.model if tts_payload else None,
            tts_voice=tts_payload.voice if tts_payload else None,
            tts_text=tts_text or (tts_payload.text if tts_payload else None),
            tts_segments=tts_segments or [],
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

    def __init__(self, state_repo: Optional[ConversationStateRepository] = None) -> None:
        self._sessions: Dict[str, AgentSession] = {}
        self._tts_engine = TTSEngine.from_env()
        default_voice = self._tts_engine.voice if self._tts_engine else None
        self._voice_selector = VoiceSelector.from_env(default_voice=default_voice)
        try:
            self._state_repo: Optional[ConversationStateRepository] = (
                state_repo or ConversationStateRepository()
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Không thể khởi tạo ConversationStateRepository: %s", exc, exc_info=True)
            self._state_repo = None

    @staticmethod
    def _resolve_model_name(model_name: Optional[str]) -> str:
        return model_name or DEFAULT_MODEL_NAME

    def _compile_graph(
        self,
        *,
        case_id: str,
        model_name: str,
        state_store: _InMemoryStateStore,
    ):
        _configure_semantic_module(case_id)
        builder = CaseStudyGraphBuilder(case_id=case_id, model_name=model_name)
        builder.state_store = state_store
        return builder.build().compile()


    def _persist_state(
        self,
        *,
        session_id: str,
        case_id: str,
        state: RuntimeState,
        user_action: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not self._state_repo:
            return
        self._state_repo.save_state(session_id, case_id, state)
        if user_action is not None or metadata:
            self._state_repo.append_turn(
                session_id=session_id,
                case_id=case_id,
                user_action=user_action,
                state=state,
                metadata=metadata,
            )

    def _tts_enabled(self) -> bool:
        return bool(self._tts_engine and getattr(self._tts_engine, "enabled", False))

    def _build_tts_segments(
        self,
        lines: list[DialogueLine],
    ) -> tuple[Optional[TTSPayload], list[dict], Optional[str]]:
        text_fallback = _format_dialogue_text(lines)
        segments: list[dict] = []
        primary_payload: Optional[TTSPayload] = None
        if not lines:
            return None, segments, text_fallback

        enabled = self._tts_enabled()
        for line in lines:
            voice = self._voice_selector.pick(line.persona_id, line.speaker)
            payload: Optional[TTSPayload] = None
            if enabled and self._tts_engine:
                payload = self._tts_engine.synthesize(line.text, voice=voice)
            if payload and not primary_payload:
                primary_payload = payload
            segments.append(
                {
                    "speaker": line.speaker,
                    "persona_id": line.persona_id,
                    "text": line.text,
                    "voice": voice,
                    "audio": payload.audio_b64 if payload else None,
                    "mime_type": payload.mime_type if payload else None,
                    "model": payload.model if payload else None,
                }
            )
        return primary_payload, segments, text_fallback
        

    def create_session(self, payload: AgentSessionCreateRequest) -> AgentSessionCreateResponse:
        session_id = uuid.uuid4().hex
        model_name = self._resolve_model_name(payload.model_name)

        try:
            logic_memory = LogicMemory.load(payload.case_id)
        except FileNotFoundError as exc:
            raise ValueError(f"Không tìm thấy dữ liệu logic cho case_id '{payload.case_id}'.") from exc

        start_event = payload.start_event or logic_memory.first_event or "CE1"

        state_store = _InMemoryStateStore()
        graph = self._compile_graph(
            case_id=payload.case_id,
            model_name=model_name,
            state_store=state_store,
        )

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
        self._persist_state(
            session_id=session_id,
            case_id=payload.case_id,
            state=state,
        )
        try:
            result_state = _normalize_runtime_state(
                graph.invoke(state, config=initial_config)
            )
        except Exception as exc:  # pragma: no cover - fallback
            raise RuntimeError("Không thể khởi tạo agent session.") from exc
        state_store.save(result_state)
        self._persist_state(
            session_id=session_id,
            case_id=payload.case_id,
            state=result_state,
            user_action=initial_user_action,
            metadata={"phase": "initial_bootstrap"},
        )

        session = AgentSession(
            session_id=session_id,
            case_id=payload.case_id,
            model_name=model_name,
            graph=graph,
            state=result_state,
            state_store=state_store,
        )
        self._sessions[session_id] = session
        dialogue_lines = _extract_dialogue_lines(result_state)
        tts_payload, tts_segments, tts_text = self._build_tts_segments(dialogue_lines)
        final_text = tts_text or result_state.ai_reply
        return session.to_response(
            tts_payload=tts_payload,
            tts_segments=tts_segments,
            tts_text=final_text,
        )

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
        dialogue_lines = _extract_dialogue_lines(state)
        tts_payload, tts_segments, tts_text = self._build_tts_segments(dialogue_lines)
        final_text = tts_text or state.ai_reply
        self._persist_state(
            session_id=session.session_id,
            case_id=session.case_id,
            state=state,
            user_action=payload.user_input,
        )
        return AgentTurnResponse(
            session_id=session.session_id,
            case_id=session.case_id,
            state=state.to_serializable(),
            tts_audio=tts_payload.audio_b64 if tts_payload else None,
            tts_mime_type=tts_payload.mime_type if tts_payload else None,
            tts_model=tts_payload.model if tts_payload else None,
            tts_voice=tts_payload.voice if tts_payload else None,
            tts_text=final_text,
            tts_segments=tts_segments,
        )

    def end_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def load_state(self, session_id: str) -> RuntimeState:
        if not self._state_repo:
            raise RuntimeError("State repository không khả dụng.")
        state = self._state_repo.load_state(session_id)
        if state is None:
            raise KeyError(f"Session '{session_id}' không tồn tại trong state store.")
        return state

    def get_session_history(self, session_id: str) -> AgentSessionHistoryResponse:
        if not self._state_repo:
            raise RuntimeError("State repository không khả dụng.")
        metadata = self._state_repo.get_state_metadata(session_id)
        if metadata is None:
            raise KeyError(f"Session '{session_id}' không tồn tại.")
        turn_logs = self._state_repo.list_turns(session_id)
        return AgentSessionHistoryResponse(
            session_id=session_id,
            case_id=metadata["case_id"],
            turns=[AgentTurnLog(**turn) for turn in turn_logs],
        )
