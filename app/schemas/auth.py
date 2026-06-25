"""
Request/response shapes for the auth endpoints.
These map directly onto the Register and Login forms.
"""

import uuid

from pydantic import BaseModel, EmailStr, Field


# ── Register ─────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8)
    confirm_password: str = Field(min_length=8)


# ── Login ────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ── Shared response shapes ──────────────────────────────────────────
class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
