from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentSessionCreateRequest(BaseModel):
    case_id: str = Field(..., description="Case ID cần khởi tạo agent.")
    start_event: Optional[str] = Field(
        default=None,
        description="Canon event bắt đầu (mặc định: event đầu tiên trong skeleton).",
    )
    user_action: Optional[str] = Field(
        default=None,
        description="Hành động ban đầu của người dùng (tùy chọn).",
    )
    model_name: Optional[str] = Field(
        default=None,
        description="Tên model LLM (nếu bỏ trống dùng mặc định trong agent).",
    )
    reset_state: bool = Field(
        default=True,
        description="Có reset trạng thái runtime trước khi chạy lượt đầu hay không.",
    )

class TTSSegment(BaseModel):
    speaker: Optional[str] = Field(default=None, description="Tên nhân vật đang nói.")
    persona_id: Optional[str] = Field(default=None, description="Định danh persona nếu có.")
    text: str = Field(..., description="Nội dung thoại đã dùng để tổng hợp giọng.")
    voice: Optional[str] = Field(default=None, description="Voice preset được chọn cho đoạn thoại.")
    audio: Optional[str] = Field(default=None, description="Chuỗi base64 audio cho đoạn thoại (nếu có).")
    mime_type: Optional[str] = Field(default=None, description="MIME type cho audio của đoạn thoại.")
    model: Optional[str] = Field(default=None, description="Model đã dùng để tạo đoạn thoại.")


class AgentSessionCreateResponse(BaseModel):
    session_id: str
    case_id: str
    state: Dict[str, Any]
    tts_audio: Optional[str] = Field(
        default=None, description="Base64-encoded facilitator reply synthesized via TTS."
    )
    tts_mime_type: Optional[str] = Field(
        default=None, description="MIME type for the tts_audio payload (e.g., audio/wav)."
    )
    tts_model: Optional[str] = Field(
        default=None, description="OpenAI model used to synthesize the reply."
    )
    tts_voice: Optional[str] = Field(
        default=None, description="Voice preset used for the synthesized reply."
    )
    tts_text: Optional[str] = Field(
        default=None, description="Plain text that was passed to the TTS engine."
    )
    tts_segments: List[TTSSegment] = Field(
        default_factory=list,
        description="Danh sách các đoạn thoại đã tổng hợp (mỗi nhân vật một giọng).",
    )


class AgentTurnRequest(BaseModel):
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID (có thể bỏ nếu đã truyền qua path).",
    )
    user_input: str = Field(..., description="Thông điệp/hành động mới của người dùng.")
    reset_state: bool = Field(
        default=False,
        description="Nếu True, agent sẽ reset state trước khi xử lý lượt này.",
    )
    start_event: Optional[str] = Field(
        default=None,
        description="Tùy chọn chuyển sang event khác trước khi xử lý lượt.",
    )


class AgentTurnResponse(BaseModel):
    session_id: str
    case_id: str
    state: Dict[str, Any]
    tts_audio: Optional[str] = Field(
        default=None, description="Base64-encoded facilitator reply synthesized via TTS."
    )
    tts_mime_type: Optional[str] = Field(
        default=None, description="MIME type for the tts_audio payload (e.g., audio/wav)."
    )
    tts_model: Optional[str] = Field(
        default=None, description="OpenAI model used to synthesize the reply."
    )
    tts_voice: Optional[str] = Field(
        default=None, description="Voice preset used for the synthesized reply."
    )
    tts_text: Optional[str] = Field(
        default=None, description="Plain text that was passed to the TTS engine."
    )
    tts_segments: List[TTSSegment] = Field(
        default_factory=list,
        description="Danh sách các đoạn thoại đã tổng hợp (mỗi nhân vật một giọng).",
    )

class AgentTurnLog(BaseModel):
    turn_index: int = Field(..., description="Thứ tự lượt trong session.")
    user_action: Optional[str] = Field(
        default=None, description="Hành động người dùng ở lượt này."
    )
    ai_reply: Optional[str] = Field(
        default=None, description="Phản hồi agent sau khi xử lý lượt."
    )
    current_event: Optional[str] = Field(
        default=None, description="Sự kiện đang active khi kết thúc lượt."
    )
    created_at: datetime = Field(
        ..., description="Thời điểm ghi nhận lượt (UTC)."
    )
    state: Dict[str, Any] = Field(
        ..., description="Snapshot đầy đủ của RuntimeState sau lượt."
    )


class AgentSessionHistoryResponse(BaseModel):
    session_id: str
    case_id: str
    turns: List[AgentTurnLog] = Field(
        default_factory=list, description="Danh sách log từng lượt."
    )
