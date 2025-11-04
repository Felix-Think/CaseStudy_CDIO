from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from casestudy.app.dependencies.cases import get_case_service
from casestudy.app.schemas.case import CaseCreatePayload, CaseCreateResponse, CaseListResponse
from casestudy.app.services.case_service import CaseService

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("/", response_model=CaseListResponse)
async def list_cases_endpoint(
    limit: int = Query(50, ge=1, le=200),
    service: CaseService = Depends(get_case_service),
) -> CaseListResponse:
    return service.list_cases(limit=limit)


@router.post(
    "/",
    response_model=CaseCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_case_endpoint(
    payload: CaseCreatePayload,
    service: CaseService = Depends(get_case_service),
) -> CaseCreateResponse:
    try:
        return service.create_case(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
