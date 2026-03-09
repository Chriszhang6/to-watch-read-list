import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from starlette.responses import RedirectResponse


SECRET_KEY = os.getenv("SECRET_KEY")
APP_PASSWORD = os.getenv("APP_PASSWORD")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required")
if not APP_PASSWORD:
    raise RuntimeError("APP_PASSWORD environment variable is required")

serializer = URLSafeTimedSerializer(SECRET_KEY, salt="auth")
security = HTTPBearer(auto_error=False)

SESSION_COOKIE_NAME = "session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 days


def create_session(password: str) -> Optional[str]:
    """Create a session token if password is correct."""
    if password == APP_PASSWORD:
        return serializer.dumps({"authenticated": True, "timestamp": datetime.utcnow().isoformat()})
    return None


def verify_session(token: str) -> bool:
    """Verify if a session token is valid."""
    try:
        data = serializer.loads(token, max_age=SESSION_MAX_AGE)
        return data.get("authenticated", False)
    except (BadSignature, SignatureExpired):
        return False


def get_current_user(request: Request) -> bool:
    """Dependency to check if user is authenticated."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token or not verify_session(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return True


def set_session_cookie(response, token: str):
    """Set session cookie on response."""
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=False  # Set to True in production with HTTPS
    )


def clear_session_cookie(response):
    """Clear session cookie."""
    response.delete_cookie(SESSION_COOKIE_NAME)
