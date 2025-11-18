from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response, status
from pymongo.errors import PyMongoError

from casestudy.app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    SessionOwnerRequest,
)
from casestudy.app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register_member(payload: RegisterRequest) -> AuthResponse:
    service = AuthService()
    try:
        email = service.register_member(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PyMongoError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể kết nối tới MongoDB. Vui lòng thử lại sau.",
        ) from exc

    message = f"Đăng ký thành công cho tài khoản {email}. Vui lòng đăng nhập để tiếp tục."
    return AuthResponse(message=message, redirect="/login")


@router.post("/login", response_model=AuthResponse)
async def login_member(payload: LoginRequest, response: Response) -> AuthResponse:
    service = AuthService()
    try:
        user_document = service.authenticate_member(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PyMongoError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể kết nối tới MongoDB. Vui lòng thử lại sau.",
        ) from exc

    user_id = str(user_document.get("_id"))
    response.set_cookie(
        key="user_id",
        value=user_id,
        httponly=True,
        max_age=60 * 60 * 12,
        samesite="lax",
    )
    return AuthResponse(
        message="Đăng nhập thành công. Đang chuyển tới Workspace.",
        redirect="/user",
        user_id=user_id,
    )


@router.post("/session-owner")
async def session_owner(
    payload: SessionOwnerRequest,
    request: Request,
) -> dict[str, str]:
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    service = AuthService()
    try:
        updated = service.append_session_owner(user_id, payload.session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PyMongoError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể kết nối tới MongoDB. Vui lòng thử lại sau.",
        ) from exc

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User không tồn tại.")

    return {"status": "ok"}
