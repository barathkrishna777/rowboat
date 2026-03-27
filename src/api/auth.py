"""Authentication API — email/password, Google OAuth sign-in, and username management."""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.database import get_session
from src.db.tables import UserTable
from src.models.user import User, UserAvailability, UserPreferences, UserProfile
from src.tools.google_calendar import (
    SCOPES,
    exchange_code_for_token,
    get_oauth_flow,
)

logger = logging.getLogger(__name__)
router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,30}$")


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
    prefs = UserPreferences(**json.loads(row.preferences)) if row.preferences else None
    token = json.loads(row.google_calendar_token) if row.google_calendar_token else None
    profile = UserProfile(**json.loads(row.profile)) if row.profile else None
    avail = UserAvailability(**json.loads(row.availability)) if row.availability else None
    return User(
        id=row.id, name=row.name, email=row.email,
        username=row.username, auth_provider=row.auth_provider,
        preferences=prefs, google_calendar_token=token,
        profile=profile, availability=avail,
    )


def _get_auth_redirect_uri() -> str:
    import os
    base = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")
    return f"{base}/api/auth/google/callback"


# ── Dependency: current user ───────────────────────────────────────────


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
    username: str | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


class SetUsernameRequest(BaseModel):
    username: str


# ── Email/password endpoints ──────────────────────────────────────────


@router.post("/register", response_model=LoginResponse)
async def register(req: RegisterRequest, session: AsyncSession = Depends(get_session)):
    """Create a new account with email/password and return a JWT."""
    existing = (await session.execute(
        select(UserTable).where(UserTable.email == req.email)
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    username = None
    if req.username:
        if not USERNAME_RE.match(req.username):
            raise HTTPException(status_code=400, detail="Username must be 3-30 characters (letters, numbers, underscores)")
        taken = (await session.execute(
            select(UserTable).where(UserTable.username == req.username)
        )).scalar_one_or_none()
        if taken:
            raise HTTPException(status_code=400, detail="Username already taken")
        username = req.username

    user_id = str(uuid.uuid4())
    row = UserTable(
        id=user_id, name=req.name, email=req.email,
        username=username, password_hash=_hash_password(req.password),
        auth_provider="email",
    )
    session.add(row)
    await session.commit()

    token = _create_token(user_id)
    return LoginResponse(access_token=token, user=_row_to_user(row))


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


# ── Google OAuth sign-in ──────────────────────────────────────────────

# Temporary store for PKCE code_verifiers keyed by OAuth state.
# In production, replace with Redis or a DB table with TTL.
_pending_oauth: dict[str, str] = {}


def _build_google_flow():
    from google_auth_oauthlib.flow import Flow
    redirect_uri = _get_auth_redirect_uri()
    client_config = {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }
    return Flow.from_client_config(client_config, scopes=SCOPES, redirect_uri=redirect_uri)


@router.get("/google/url")
async def google_auth_url():
    """Get the Google OAuth sign-in URL (covers sign-in + calendar access)."""
    flow = _build_google_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent",
    )
    # Store the PKCE code_verifier so the callback can use it
    if hasattr(flow, "code_verifier") and flow.code_verifier:
        _pending_oauth[state] = flow.code_verifier
    return {"auth_url": auth_url}


@router.get("/google/callback")
async def google_auth_callback(
    code: str,
    state: str = "",
    session: AsyncSession = Depends(get_session),
):
    """Handle Google OAuth callback — create/login user and store calendar token."""
    from googleapiclient.discovery import build as build_service

    flow = _build_google_flow()

    # Restore the PKCE code_verifier from the original auth request
    code_verifier = _pending_oauth.pop(state, None)
    if code_verifier:
        flow.code_verifier = code_verifier

    try:
        flow.fetch_token(code=code)
    except Exception as e:
        logger.error(f"[Auth] Google token exchange failed: {e}")
        raise HTTPException(status_code=400, detail=f"Google auth failed: {e}")

    credentials = flow.credentials
    token_data = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes) if credentials.scopes else list(SCOPES),
    }

    # Fetch Google profile info
    try:
        oauth2_service = build_service("oauth2", "v2", credentials=credentials)
        google_user = oauth2_service.userinfo().get().execute()
    except Exception as e:
        logger.error(f"[Auth] Failed to fetch Google profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Google profile")

    google_id = google_user.get("id", "")
    email = google_user.get("email", "")
    name = google_user.get("name", email.split("@")[0])

    # Find existing user by google_id or email
    row = None
    if google_id:
        result = await session.execute(select(UserTable).where(UserTable.google_id == google_id))
        row = result.scalar_one_or_none()
    if not row and email:
        result = await session.execute(select(UserTable).where(UserTable.email == email))
        row = result.scalar_one_or_none()

    if row:
        # Existing user — update their Google info and calendar token
        row.google_id = google_id
        row.google_calendar_token = json.dumps(token_data)
        if not row.auth_provider:
            row.auth_provider = "google"
        if row.name == "Unknown" or not row.name:
            row.name = name
    else:
        # New user
        row = UserTable(
            id=str(uuid.uuid4()), name=name, email=email,
            google_id=google_id, auth_provider="google",
            google_calendar_token=json.dumps(token_data),
        )
        session.add(row)

    await session.commit()
    await session.refresh(row)

    # Create JWT and redirect to the Streamlit UI with token in query params
    jwt_token = _create_token(row.id)

    import os
    ui_base = os.environ.get("UI_BASE_URL", "http://localhost:8501").rstrip("/")
    return RedirectResponse(f"{ui_base}?auth_token={jwt_token}&user_id={row.id}")


# ── Username management ───────────────────────────────────────────────


@router.post("/username", response_model=User)
async def set_username(
    req: SetUsernameRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Set or update the current user's username."""
    if not USERNAME_RE.match(req.username):
        raise HTTPException(
            status_code=400,
            detail="Username must be 3-30 characters (letters, numbers, underscores only)",
        )
    taken = (await session.execute(
        select(UserTable).where(UserTable.username == req.username, UserTable.id != current_user.id)
    )).scalar_one_or_none()
    if taken:
        raise HTTPException(status_code=400, detail="Username already taken")

    row = await session.get(UserTable, current_user.id)
    row.username = req.username
    await session.commit()
    return _row_to_user(row)


@router.get("/check-username/{username}")
async def check_username(username: str, session: AsyncSession = Depends(get_session)):
    """Check if a username is available."""
    if not USERNAME_RE.match(username):
        return {"available": False, "reason": "Invalid format"}
    existing = (await session.execute(
        select(UserTable).where(UserTable.username == username)
    )).scalar_one_or_none()
    return {"available": existing is None}


# ── Current user ──────────────────────────────────────────────────────


@router.get("/me", response_model=User)
async def me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return current_user
