from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, status

from api_casestudy.schemas import (
    AgentSessionCreateRequest,
    AgentSessionCreateResponse,
    AgentTurnRequest,
    AgentTurnResponse,
)
from api_casestudy.services import AgentService

router = APIRouter(prefix="/agent", tags=["agent"])


@lru_cache
def get_agent_service() -> AgentService:
    return AgentService()


@router.post(
    "/sessions",
    response_model=AgentSessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session_endpoint(
    payload: AgentSessionCreateRequest,
    service: AgentService = Depends(get_agent_service),
) -> AgentSessionCreateResponse:
    try:
        return service.create_session(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.post(
    "/sessions/{session_id}/turn",
    response_model=AgentTurnResponse,
)
async def send_turn_endpoint(
    session_id: str,
    payload: AgentTurnRequest,
    service: AgentService = Depends(get_agent_service),
) -> AgentTurnResponse:
    if payload.session_id and payload.session_id != session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id trong payload không trùng với đường dẫn.",
        )
    payload.session_id = session_id
    try:
        return service.send_turn(payload)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def end_session_endpoint(
    session_id: str,
    service: AgentService = Depends(get_agent_service),
) -> None:
    service.end_session(session_id)
