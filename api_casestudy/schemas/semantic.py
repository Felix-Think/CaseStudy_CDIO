from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class SemanticBuildRequest(BaseModel):
    case_id: str = Field(..., description="Case ID cần đồng bộ semantic store.")
    force_rebuild: bool = Field(
        default=False,
        description="True để bỏ qua cache và xây dựng mới hoàn toàn.",
    )


class SemanticBuildResponse(BaseModel):
    case_id: str
    documents_indexed: int
    vector_store_path: str
    embedding_model: str


class SemanticQueryRequest(BaseModel):
    case_id: str = Field(..., description="Case ID dùng để truy vấn semantic store.")
    question: str = Field(..., description="Câu hỏi đầu vào.")
    top_k: int = Field(default=5, ge=1, le=20, description="Số vector tương tự cần lấy.")


class SemanticResultChunk(BaseModel):
    text: str
    score: float
    metadata: Optional[dict] = None


class SemanticQueryResponse(BaseModel):
    case_id: str
    question: str
    top_k: int
    results: List[SemanticResultChunk]
