from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pymongo import ASCENDING
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from casestudy.agent import RuntimeState

from api_casestudy.core.config import get_settings
from api_casestudy.db.database import get_mongo_client


class ConversationStateRepository:
    """
    Lớp phụ trách lưu trữ RuntimeState và turn logs vào MongoDB.
    """

    def __init__(self) -> None:
        settings = get_settings()
        client = get_mongo_client()
        db = client[settings.state_db]

        self._state_collection: Collection = db["runtime_states"]
        self._turn_collection: Collection = db["turn_logs"]
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        try:
            self._state_collection.create_index(
                "session_id", unique=True, name="session_id_unique_idx"
            )
            self._turn_collection.create_index(
                [("session_id", ASCENDING), ("turn_index", ASCENDING)],
                name="session_turn_idx",
            )
        except PyMongoError:
            # Không chặn workflow nếu việc tạo index thất bại.
            pass

    def save_state(self, session_id: str, case_id: str, state: RuntimeState) -> None:
        payload = {
            "session_id": session_id,
            "case_id": case_id,
            "turn_count": state.turn_count,
            "updated_at": datetime.now(timezone.utc),
            "state": state.to_serializable(),
        }
        try:
            self._state_collection.replace_one(
                {"session_id": session_id},
                payload,
                upsert=True,
            )
        except PyMongoError as exc:
            raise RuntimeError("Không thể lưu runtime state vào MongoDB.") from exc

    def append_turn(
        self,
        *,
        session_id: str,
        case_id: str,
        user_action: Optional[str],
        state: RuntimeState,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        turn_document: Dict[str, Any] = {
            "session_id": session_id,
            "case_id": case_id,
            "turn_index": state.turn_count,
            "user_action": user_action or state.user_action,
            "ai_reply": state.ai_reply,
            "current_event": state.current_event,
            "scene_summary": state.scene_summary,
            "event_summary": state.event_summary,
            "state": state.to_serializable(),
        }
        if metadata:
            turn_document["metadata"] = metadata
        try:
            self._turn_collection.insert_one(turn_document)
        except PyMongoError as exc:
            raise RuntimeError("Không thể ghi turn log vào MongoDB.") from exc

    def load_state(self, session_id: str) -> Optional[RuntimeState]:
        try:
            document = self._state_collection.find_one({"session_id": session_id})
        except PyMongoError as exc:
            raise RuntimeError("Không thể đọc runtime state từ MongoDB.") from exc
        if not document:
            return None
        state_payload = document.get("state")
        if not state_payload:
            return None
        return RuntimeState.from_serialized(state_payload)

    def get_state_metadata(self, session_id: str) -> Optional[Dict[str, Any]]:
        try:
            document = self._state_collection.find_one({"session_id": session_id})
        except PyMongoError as exc:
            raise RuntimeError("Không thể đọc metadata runtime state.") from exc
        if not document:
            return None
        return {
            "session_id": document["session_id"],
            "case_id": document["case_id"],
            "turn_count": document.get("turn_count", 0),
            "updated_at": document.get("updated_at"),
        }

    def list_turns(self, session_id: str) -> List[Dict[str, Any]]:
        try:
            cursor = self._turn_collection.find({"session_id": session_id}).sort(
                "turn_index", ASCENDING
            )
        except PyMongoError as exc:
            raise RuntimeError("Không thể truy vấn turn logs từ MongoDB.") from exc

        turns: List[Dict[str, Any]] = []
        for doc in cursor:
            turns.append(
                {
                    "turn_index": doc.get("turn_index", 0),
                    "user_action": doc.get("user_action"),
                    "ai_reply": doc.get("ai_reply"),
                    "current_event": doc.get("current_event"),
                    "created_at": doc.get("created_at"),
                    "state": doc.get("state", {}),
                }
            )
        return turns
