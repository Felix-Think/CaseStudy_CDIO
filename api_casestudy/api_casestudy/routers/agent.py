from __future__ import annotations

import asyncio
import json
import logging
import time
from functools import lru_cache
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from api_casestudy.schemas import (
    AgentSessionCreateRequest,
    AgentSessionCreateResponse,
    AgentSessionHistoryResponse,
    AgentTurnRequest,
    AgentTurnResponse,
)
from api_casestudy.services import AgentService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent", tags=["agent"])

# Track in-progress and completed sessions to prevent duplicates
_pending_sessions: dict[str, asyncio.Future] = {}
_completed_sessions: dict[str, tuple[float, AgentSessionCreateResponse]] = {}


@lru_cache
def get_agent_service() -> AgentService:
    return AgentService()


def _get_cached_session(case_id: str, client_ip: str) -> Optional[AgentSessionCreateResponse]:
    """Check if we have a recently completed session for this case+client."""
    cache_key = f"{case_id}:{client_ip}"
    if cache_key in _completed_sessions:
        created_at, response = _completed_sessions[cache_key]
        # Return cached session if it's less than 30 seconds old
        if time.time() - created_at < 30:
            logger.info(f"[CACHE HIT] Returning cached session for case_id={case_id}")
            return response
        else:
            # Clean up stale entry
            del _completed_sessions[cache_key]
    return None


def _cache_session(case_id: str, client_ip: str, response: AgentSessionCreateResponse) -> None:
    """Cache a completed session."""
    cache_key = f"{case_id}:{client_ip}"
    _completed_sessions[cache_key] = (time.time(), response)
    
    # Clean up old entries
    now = time.time()
    stale_keys = [k for k, (t, _) in _completed_sessions.items() if now - t > 60]
    for k in stale_keys:
        del _completed_sessions[k]


@router.post(
    "/sessions",
    response_model=AgentSessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session_endpoint(
    request: Request,
    payload: AgentSessionCreateRequest,
    service: AgentService = Depends(get_agent_service),
) -> AgentSessionCreateResponse:
    client_ip = request.client.host if request.client else "unknown"
    request_key = f"{payload.case_id}:{client_ip}"
    
    logger.info(
        "create_session request client=%s method=%s path=%s payload=%s",
        client_ip,
        request.method,
        request.url.path,
        payload.model_dump(),
    )
    
    # Check if there's already a request in progress for this case+client
    if request_key in _pending_sessions:
        logger.info(f"[WAITING] Request already in progress for case_id={payload.case_id}, waiting...")
        try:
            # Wait for the existing request to complete (max 30 seconds)
            result = await asyncio.wait_for(_pending_sessions[request_key], timeout=30.0)
            logger.info(f"[REUSED] Returning result from parallel request for case_id={payload.case_id}")
            return result
        except asyncio.TimeoutError:
            logger.warning(f"[TIMEOUT] Waiting for parallel request timed out for case_id={payload.case_id}")
            # Continue to create a new session
        except Exception as e:
            logger.warning(f"[ERROR] Parallel request failed for case_id={payload.case_id}: {e}")
            # Continue to create a new session
    
    # Create a future to track this request
    loop = asyncio.get_event_loop()
    future: asyncio.Future = loop.create_future()
    _pending_sessions[request_key] = future
    
    logger.info(f"[NEW REQUEST] case_id={payload.case_id}, client={client_ip}")
    
    try:
        # Run the blocking service call in a thread pool
        result = await asyncio.get_event_loop().run_in_executor(
            None, service.create_session, payload
        )
        
        # Resolve the future so waiting requests can use this result
        if not future.done():
            future.set_result(result)
        
        return result
    except ValueError as exc:
        if not future.done():
            future.set_exception(exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        if not future.done():
            future.set_exception(exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        if not future.done():
            future.set_exception(exc)
        raise
    finally:
        # Clean up the pending request
        if request_key in _pending_sessions:
            del _pending_sessions[request_key]


async def _stream_session_creation(
    payload: AgentSessionCreateRequest,
    service: AgentService,
    client_ip: str,
) -> AsyncGenerator[str, None]:
    """Stream session creation progress via Server-Sent Events."""
    request_key = f"{payload.case_id}:{client_ip}"
    
    def send_event(event_type: str, data: dict) -> str:
        return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
    
    # Send initial status
    yield send_event("status", {"message": "Đang khởi tạo tình huống...", "progress": 10})
    
    try:
        yield send_event("status", {"message": "Đang tải dữ liệu case...", "progress": 20})
        
        # Run the blocking service call in a thread pool
        loop = asyncio.get_event_loop()
        
        # Create session with progress updates
        yield send_event("status", {"message": "Đang phân tích ngữ cảnh...", "progress": 40})
        
        result = await loop.run_in_executor(
            None, service.create_session, payload
        )
        
        yield send_event("status", {"message": "Đang tạo phản hồi AI...", "progress": 70})
        yield send_event("status", {"message": "Hoàn tất!", "progress": 100})
        
        # Send the complete session data
        yield send_event("complete", result.model_dump())
        
    except ValueError as exc:
        yield send_event("error", {"message": str(exc), "code": 400})
    except RuntimeError as exc:
        yield send_event("error", {"message": str(exc), "code": 503})
    except Exception as exc:
        logger.exception(f"Streaming error for case_id={payload.case_id}")
        yield send_event("error", {"message": "Lỗi không xác định khi tạo session", "code": 500})


@router.post("/sessions/stream")
async def create_session_stream_endpoint(
    request: Request,
    payload: AgentSessionCreateRequest,
    service: AgentService = Depends(get_agent_service),
) -> StreamingResponse:
    """Create a new session with streaming progress updates via SSE."""
    client_ip = request.client.host if request.client else "unknown"
    
    return StreamingResponse(
        _stream_session_creation(payload, service, client_ip),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.post(
    "/sessions/{session_id}/turn",
    response_model=AgentTurnResponse,
)
async def send_turn_endpoint(
    request: Request,
    session_id: str,
    payload: AgentTurnRequest,
    service: AgentService = Depends(get_agent_service),
) -> AgentTurnResponse:
    logger.info(
        "send_turn request client=%s session_id=%s payload=%s",
        request.client.host if request.client else "unknown",
        session_id,
        payload.model_dump(),
    )
    
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


@router.get(
    "/sessions/{session_id}/history",
    response_model=AgentSessionHistoryResponse,
)
async def get_session_history_endpoint(
    session_id: str,
    service: AgentService = Depends(get_agent_service),
) -> AgentSessionHistoryResponse:
    try:
        return service.get_session_history(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
