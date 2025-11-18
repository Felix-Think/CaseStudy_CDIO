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


class AgentSessionCreateResponse(BaseModel):
    session_id: str
    case_id: str
    state: Dict[str, Any]


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
