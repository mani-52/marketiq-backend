"""
auth.py — Complete JWT authentication for MarketIQ.

Supports:
  1. Email + Password  (POST /auth/register  |  POST /auth/login)
  2. Google ID Token   (POST /auth/google)
  3. Current user      (GET  /auth/me)

Google flow:
  - Frontend: @react-oauth/google  →  credentialResponse.credential  (id_token)
  - Body sent to backend:  { "id_token": "<Google-signed JWT>" }
  - Backend verifies with:  google.oauth2.id_token.verify_oauth2_token(...)
  - NO external API calls. Verification is LOCAL using Google's public certs.

Dependencies (pip install):
  google-auth  requests  pyjwt
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt as pyjwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])
_bearer = HTTPBearer(auto_error=False)

# ---------------------------------------------------------------------------
# In-memory user store  (swap for SQLAlchemy + PostgreSQL in production)
# ---------------------------------------------------------------------------
_USERS: list[dict] = []


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _hash_password(password: str) -> str:
    """HMAC-SHA256 password hash keyed on JWT_SECRET."""
    return hmac.new(
        settings.jwt_secret.encode("utf-8"),
        password.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _find_by_email(email: str) -> Optional[dict]:
    return next(
        (u for u in _USERS if u["email"].lower() == email.lower()), None
    )


def _make_jwt(user_id: str, email: str, name: str) -> str:
    """Create a signed JWT valid for jwt_expire_minutes minutes."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_expire_minutes)).timestamp()),
    }
    return pyjwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _verify_jwt(token: str) -> dict:
    """Decode and verify our own JWT. Raises 401 on any failure."""
    try:
        return pyjwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired — please sign in again")
    except pyjwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}")


# ---------------------------------------------------------------------------
# Dependency — inject authenticated user into protected routes
# ---------------------------------------------------------------------------

async def require_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict:
    if not creds:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    return _verify_jwt(creds.credentials)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class RegisterBody(BaseModel):
    name:     str
    email:    str
    password: str

class LoginBody(BaseModel):
    email:    str
    password: str

class GoogleBody(BaseModel):
    """
    id_token = credentialResponse.credential from @react-oauth/google.
    This is a Google-signed JWT (RS256).  DO NOT confuse with access_token.
    """
    id_token: str

class AuthResponse(BaseModel):
    token: str
    user:  dict


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/register", response_model=AuthResponse)
async def register(body: RegisterBody):
    """Create a new account with email + password."""
    body.email = body.email.lower().strip()

    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Name is required")
    if not body.email:
        raise HTTPException(status_code=400, detail="Email is required")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    if _find_by_email(body.email):
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    user = {
        "id":           str(int(time.time() * 1000)),
        "name":         body.name.strip(),
        "email":        body.email,
        "passwordHash": _hash_password(body.password),
        "picture":      "",
        "provider":     "credentials",
        "createdAt":    datetime.now(timezone.utc).isoformat(),
    }
    _USERS.append(user)
    logger.info("Registered new user: %s", user["email"])

    token = _make_jwt(user["id"], user["email"], user["name"])
    return AuthResponse(
        token=token,
        user={"id": user["id"], "name": user["name"], "email": user["email"], "picture": ""},
    )


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginBody):
    """Sign in with email + password."""
    body.email = body.email.lower().strip()
    user = _find_by_email(body.email)

    if not user or user.get("passwordHash") != _hash_password(body.password):
        # Same message for both cases — don't leak whether email exists
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = _make_jwt(user["id"], user["email"], user["name"])
    logger.info("User logged in: %s", user["email"])
    return AuthResponse(
        token=token,
        user={"id": user["id"], "name": user["name"], "email": user["email"], "picture": user.get("picture", "")},
    )


@router.post("/google", response_model=AuthResponse)
async def google_login(body: GoogleBody):
    """
    Verify a Google ID Token and return a MarketIQ JWT.

    id_token  =  credentialResponse.credential  from @react-oauth/google
               =  a Google-signed RS256 JWT (NOT an access_token)

    Verification is LOCAL — google-auth fetches Google's public certs once
    and caches them.  No ongoing calls to Google APIs.
    """
    if not settings.google_client_id:
        raise HTTPException(
            status_code=503,
            detail=(
                "Google OAuth is not configured on this server. "
                "Add GOOGLE_CLIENT_ID to the backend .env file."
            ),
        )

    # ── Verify the ID token locally ──────────────────────────────────────────
    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests
    except ImportError:
        logger.error("google-auth not installed — run: pip install google-auth requests")
        raise HTTPException(
            status_code=500,
            detail="Server missing dependency: pip install google-auth requests",
        )

    try:
        id_info: dict = google_id_token.verify_oauth2_token(
            id_token=body.id_token,
            request=google_requests.Request(),
            audience=settings.google_client_id,
        )
    except ValueError as exc:
        # Catches: expired token, wrong audience, bad signature, malformed JWT
        logger.warning("Google id_token rejected: %s", exc)
        raise HTTPException(
            status_code=401,
            detail=f"Google token verification failed: {exc}",
        )
    except Exception as exc:
        logger.error("Unexpected error verifying Google token: %s", exc)
        raise HTTPException(status_code=401, detail="Could not verify Google token")

    # ── Extract user info from the verified payload ───────────────────────────
    email   = id_info.get("email", "").lower().strip()
    name    = id_info.get("name") or id_info.get("given_name") or email.split("@")[0]
    picture = id_info.get("picture", "")
    g_sub   = id_info.get("sub", "")          # Google's stable user ID

    if not email:
        raise HTTPException(status_code=400, detail="Google account has no email address")

    if not id_info.get("email_verified", False):
        raise HTTPException(status_code=400, detail="Google email address is not verified")

    # ── Upsert user ───────────────────────────────────────────────────────────
    user = _find_by_email(email)
    if user is None:
        user = {
            "id":           str(int(time.time() * 1000)),
            "name":         name,
            "email":        email,
            "passwordHash": "",          # Google users don't have a password
            "picture":      picture,
            "provider":     "google",
            "googleSub":    g_sub,
            "createdAt":    datetime.now(timezone.utc).isoformat(),
        }
        _USERS.append(user)
        logger.info("Google OAuth — new user created: %s", email)
    else:
        # Refresh name and avatar in case the user updated their Google profile
        user["name"]    = name
        user["picture"] = picture
        logger.info("Google OAuth — existing user signed in: %s", email)

    token = _make_jwt(user["id"], user["email"], user["name"])
    return AuthResponse(
        token=token,
        user={"id": user["id"], "name": user["name"], "email": user["email"], "picture": picture},
    )


@router.get("/me")
async def me(current_user: dict = Depends(require_user)):
    """Return the currently authenticated user's claims."""
    return current_user


# ── Backwards-compatibility aliases ──────────────────────────────────────────
# Other modules (notifications.py, analysis.py) may import these names.
get_current_user = require_user   # alias: notifications.py uses get_current_user
decode_token     = _verify_jwt    # alias: analysis.py uses decode_token
