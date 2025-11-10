from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from casestudy.app.dependencies.cases import (
    get_case_service,
    get_case_draft_service,
)
from casestudy.app.schemas.case import (
    CaseCreatePayload,
    CaseCreateResponse,
    CaseListResponse,
    CaseDraftRequest,
    CaseDraftResponse,
)
from casestudy.app.services.case_service import CaseService
from casestudy.app.services.case_draft_service import CaseDraftService

# Router setup
router = APIRouter(prefix="/cases", tags=["cases"])

# ==============================
# Endpoint: GET /cases
# ==============================
@router.get("/", response_model=CaseListResponse)
async def list_cases_endpoint(
    limit: int = Query(50, ge=1, le=200),
    service: CaseService = Depends(get_case_service),
) -> CaseListResponse:
    """
    Danh sách các case hiện có (giới hạn bởi 'limit').
    """
    return service.list_cases(limit=limit)

# ==============================
# Endpoint: POST /cases
# ==============================
@router.post(
    "/",
    response_model=CaseCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_case_endpoint(
    payload: CaseCreatePayload,
    service: CaseService = Depends(get_case_service),
) -> CaseCreateResponse:
    """
    Tạo mới một case từ dữ liệu payload.
    """
    try:
        return service.create_case(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

# ==============================
# Endpoint: POST /cases/draft
# ==============================
@router.post(
    "/draft",
    response_model=CaseDraftResponse,
    status_code=status.HTTP_200_OK,
)
async def draft_case_endpoint(
    payload: CaseDraftRequest,
    service: CaseDraftService = Depends(get_case_draft_service),
) -> CaseDraftResponse:
    """
    Sinh bản nháp (draft) cho case bằng Gemini hoặc AI service.
    """
    try:
        return service.draft_case(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
