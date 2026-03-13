import os
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .database import get_db
from .models import User

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required")

serializer = URLSafeTimedSerializer(SECRET_KEY, salt="auth")
security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SESSION_COOKIE_NAME = "session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 days


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_session(user_id: int) -> str:
    """Create a session token for a user."""
    return serializer.dumps({
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat()
    })


def verify_session(token: str) -> Optional[dict]:
    """Verify if a session token is valid. Returns user_id if valid."""
    try:
        data = serializer.loads(token, max_age=SESSION_MAX_AGE)
        return {"user_id": data.get("user_id")}
    except (BadSignature, SignatureExpired):
        return None


def get_current_user_id(request: Request) -> int:
    """Dependency to get current user ID. Raises if not authenticated."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    session_data = verify_session(token)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )

    return session_data["user_id"]


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency to get current user object. Raises if not authenticated."""
    user_id = get_current_user_id(request)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email."""
    return db.query(User).filter(User.email == email.lower()).first()


def create_user(db: Session, email: str, password: str) -> User:
    """Create a new user with hashed password."""
    hashed_password = hash_password(password)
    user = User(
        email=email.lower(),
        hashed_password=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password."""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


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
