from typing import Literal

from pydantic import BaseModel, EmailStr, Field

Role = Literal["admin", "facilitator", "viewer"]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)


class AuthUser(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: Role
    permissions: list[str]


class SessionResponse(BaseModel):
    user: AuthUser


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=12, max_length=200)
    role: Role
