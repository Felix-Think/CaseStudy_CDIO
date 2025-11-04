from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, status

from api_casestudy.schemas import (
    SemanticBuildRequest,
    SemanticBuildResponse,
    SemanticQueryRequest,
    SemanticQueryResponse,
)
from api_casestudy.services import SemanticService

router = APIRouter(prefix="/semantic", tags=["semantic"])


@lru_cache
def get_semantic_service() -> SemanticService:
    return SemanticService()


@router.post(
    "/build",
    response_model=SemanticBuildResponse,
    status_code=status.HTTP_201_CREATED,
)
async def build_semantic_endpoint(
    payload: SemanticBuildRequest,
    service: SemanticService = Depends(get_semantic_service),
) -> SemanticBuildResponse:
    try:
        return service.build_semantic_store(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.post(
    "/query",
    response_model=SemanticQueryResponse,
)
async def query_semantic_endpoint(
    payload: SemanticQueryRequest,
    service: SemanticService = Depends(get_semantic_service),
) -> SemanticQueryResponse:
    try:
        return service.query(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
