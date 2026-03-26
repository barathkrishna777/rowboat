"""Authentication API — register, login, and JWT-based session management."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.database import get_session
from src.db.tables import UserTable
from src.models.user import User, UserPreferences

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# ── Helpers ────────────────────────────────────────────────────────────


def _hash_password(password: str) -> str:
    return pwd_context.hash(password)


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode(
        {"sub": user_id, "exp": expire},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def _row_to_user(row: UserTable) -> User:
    import json
    prefs = UserPreferences(**json.loads(row.preferences)) if row.preferences else None
    token = json.loads(row.google_calendar_token) if row.google_calendar_token else None
    return User(id=row.id, name=row.name, email=row.email, preferences=prefs, google_calendar_token=token)


# ── Dependency: current user (optional — returns None if no token) ─────


async def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User | None:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub", "")
    except JWTError:
        return None
    row = await session.get(UserTable, user_id)
    return _row_to_user(row) if row else None


async def get_current_user(
    user: User | None = Depends(get_current_user_optional),
) -> User:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


# ── Request / Response models ──────────────────────────────────────────


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


class UserPublic(BaseModel):
    id: str
    name: str
    email: str


# ── Endpoints ──────────────────────────────────────────────────────────


@router.post("/register", response_model=LoginResponse)
async def register(req: RegisterRequest, session: AsyncSession = Depends(get_session)):
    """Create a new account and return a JWT."""
    existing = (await session.execute(
        select(UserTable).where(UserTable.email == req.email)
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    row = UserTable(
        id=user_id,
        name=req.name,
        email=req.email,
        password_hash=_hash_password(req.password),
    )
    session.add(row)
    await session.commit()

    token = _create_token(user_id)
    return LoginResponse(access_token=token, user=User(id=user_id, name=req.name, email=req.email))


@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    """Authenticate with email + password and receive a JWT."""
    result = await session.execute(
        select(UserTable).where(UserTable.email == form_data.username)
    )
    row = result.scalar_one_or_none()
    if not row or not row.password_hash or not _verify_password(form_data.password, row.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = _create_token(row.id)
    return LoginResponse(access_token=token, user=_row_to_user(row))


@router.get("/me", response_model=User)
async def me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return current_user
