from __future__ import annotations

from typing import Any, Dict, Optional

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
    ensure_semantic: bool = Field(
        default=True,
        description="Tự động đảm bảo semantic index tồn tại trước khi khởi chạy.",
    )
    rebuild_semantic: bool = Field(
        default=False,
        description="Force rebuild semantic index trước khi chạy.",
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
