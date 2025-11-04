from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


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
