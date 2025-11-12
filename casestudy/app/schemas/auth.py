from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, constr

BasicEmailStr = constr(strip_whitespace=True, min_length=3)

class RegisterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: BasicEmailStr
    password: constr(min_length=6)
    password_confirm: constr(min_length=6) = Field(alias="passwordConfirm")


class LoginRequest(BaseModel):
    email: BasicEmailStr
    password: constr(min_length=6)
    remember: bool = False


class AuthResponse(BaseModel):
    message: str
    redirect: str = "/nhap-case"
    user_id: str | None = None


class SessionOwnerRequest(BaseModel):
    session_id: constr(strip_whitespace=True, min_length=6)
