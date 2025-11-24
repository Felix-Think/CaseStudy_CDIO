from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class BackgroundImageRequest(BaseModel):
    case_id: str = Field(..., min_length=1)
    prompt: Optional[str] = None
    scene: Optional[Dict[str, Any]] = None
    index_event: Optional[Dict[str, Any]] = None
    seed: Optional[int] = Field(default=None, ge=0)
    file_name: Optional[str] = Field(default=None, min_length=1)
    use_local_context: bool = Field(
        default=True,
        description="Cho phep doc context.json khi khong co prompt/scene.",
    )


class BackgroundImageResponse(BaseModel):
    case_id: str
    prompt_used: str
    file_path: str
    file_name: str
    seed: int
    source: str
    image_base64: str
    message: str
