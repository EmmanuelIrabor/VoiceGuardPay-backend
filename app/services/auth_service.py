"""
Auth business logic. Kept free of FastAPI imports so it can be tested
or reused independently of the HTTP layer.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest


class AuthError(Exception):
    """Raised for any auth failure the route layer should turn into an HTTP error."""
    pass


async def register_user(db: AsyncSession, payload: RegisterRequest) -> User:
    if payload.password != payload.confirm_password:
        raise AuthError("Passwords do not match.")

    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise AuthError("An account with this email already exists.")

    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, payload: LoginRequest) -> User:
    user = await db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.hashed_password):
        raise AuthError("Invalid email or password.")
    return user


def issue_token(user: User) -> str:
    return create_access_token({"sub": str(user.id)})
