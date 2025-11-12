from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class CaseSummary(BaseModel):
    case_id: str
    topic: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[str] = None
    time: Optional[str] = None
    who_first_on_scene: Optional[str] = None


class CaseListResponse(BaseModel):
    cases: List[CaseSummary]
    source: str


class CaseDetailResponse(BaseModel):
    case_id: str
    context: Optional[Dict[str, Any]] = None
    skeleton: Optional[Dict[str, Any]] = None
    personas: Optional[Dict[str, Any]] = None
    source: str


class CaseCreatePayload(BaseModel):
    """
    Payload nhận từ frontend để tạo/cập nhật case.
    """

    case_id: Optional[str] = None
    context: Dict[str, Any]
    personas: Union[List[Dict[str, Any]], Dict[str, Any]]
    skeleton: Dict[str, Any]


class CaseCreateResponse(BaseModel):
    case_id: str
    personas_count: int
    message: str
    local_path: Optional[str] = None


class CaseDraftRequest(BaseModel):
    """
    Payload gửi tới endpoint /cases/draft để sinh dữ liệu gợi ý.
    """

    prompt: Optional[str] = None
    topic: Optional[str] = None
    location: Optional[str] = None
    persona_count: Optional[int] = None
    min_personas: Optional[int] = None
    ensure_minimum_personas: bool = True
    personas: Optional[List[Dict[str, Any]]] = None

    class Config:
        extra = "allow"


class CaseDraftPersonasPayload(BaseModel):
    case_id: str
    personas: List[Dict[str, Any]]


class CaseDraftResponse(BaseModel):
    case_id: str
    topic: str
    prompt: Optional[str] = None
    skeleton: Dict[str, Any]
    context: Dict[str, Any]
    personas: CaseDraftPersonasPayload
    warnings: List[str] = Field(default_factory=list)
