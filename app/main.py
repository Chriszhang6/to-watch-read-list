import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from .database import get_db, init_db, engine, Base
from .models import Item, User, PasswordReset
from .schemas import (
    ItemCreate, ItemUpdate, ItemResponse, ItemListResponse,
    LoginRequest, RegisterRequest, MessageResponse,
    ForgotPasswordRequest, ResetPasswordRequest
)
from .auth import (
    create_session, verify_session, get_current_user, get_current_user_id,
    set_session_cookie, clear_session_cookie, SESSION_COOKIE_NAME,
    authenticate_user, create_user, get_user_by_email, hash_password
)
import secrets
import uuid
from datetime import datetime, timedelta

from .services.scraper import scrape_url
from .services.email import send_password_reset_email

app = FastAPI(title="Watchlist", version="2.0.0")

# CORS configuration - more restrictive for security
# In production, set allowed origins to your actual domain
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
def on_startup():
    init_db()


# Page Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main page."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token or not verify_session(token):
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render the login page."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token and verify_session(token):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """Render the forgot password page."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token and verify_session(token):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("forgot_password.html", {"request": request})


@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request):
    """Render the reset password page."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token and verify_session(token):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("reset_password.html", {"request": request})


# Auth API Routes
@app.post("/api/register", response_model=MessageResponse)
async def register(
    register_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """Handle registration request."""
    # Check if email already exists
    existing_user = get_user_by_email(db, register_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    user = create_user(db, register_data.email, register_data.password)

    return {"message": "Registration successful"}


@app.post("/api/login")
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Handle login request."""
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_session(user.id)
    response = JSONResponse(content={"message": "Login successful"})
    set_session_cookie(response, token)
    return response


@app.post("/api/logout")
async def logout():
    """Handle logout request."""
    response = JSONResponse(content={"message": "Logged out"})
    clear_session_cookie(response)
    return response


# Items API Routes
@app.post("/api/items", response_model=ItemResponse)
async def create_item(
    item_data: ItemCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Create a new item from a URL."""
    # Scrape metadata
    try:
        metadata = await scrape_url(item_data.url)
    except Exception:
        metadata = {"title": None, "description": None, "source_type": "other"}

    # Create item
    item = Item(
        url=item_data.url,
        title=metadata["title"] or "Untitled",
        summary=metadata["description"],
        source_type=metadata["source_type"],
        user_id=user_id
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


@app.get("/api/items", response_model=ItemListResponse)
async def list_items(
    status_filter: str = Query("all", alias="status", regex="^(all|pending|completed)$"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    date: Optional[str] = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """List all items with optional filters."""
    query = db.query(Item).filter(Item.user_id == user_id)

    # Apply status filter
    if status_filter == "pending":
        query = query.filter(Item.completed == False)
    elif status_filter == "completed":
        query = query.filter(Item.completed == True)

    # Apply single date filter (for calendar view)
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
            next_day = target_date + timedelta(days=1)
            query = query.filter(Item.captured_at >= target_date, Item.captured_at < next_day)
        except ValueError:
            pass
    else:
        # Apply date range filters
        if date_from:
            try:
                from_date = datetime.strptime(date_from, "%Y-%m-%d")
                query = query.filter(Item.captured_at >= from_date)
            except ValueError:
                pass

        if date_to:
            try:
                to_date = datetime.strptime(date_to, "%Y-%m-%d")
                query = query.filter(Item.captured_at <= to_date)
            except ValueError:
                pass

    # Order by captured_at descending
    query = query.order_by(Item.captured_at.desc())

    items = query.all()
    total = len(items)

    return {"items": items, "total": total}


@app.get("/api/items/dates")
async def get_item_dates(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get all dates that have items (for calendar view)."""
    items = db.query(Item).filter(Item.user_id == user_id).all()

    dates = set()
    for item in items:
        date_str = item.captured_at.strftime("%Y-%m-%d")
        dates.add(date_str)

    return {"dates": sorted(list(dates), reverse=True)}


@app.get("/api/items/stats")
async def get_item_stats(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get item counts by status."""
    query = db.query(Item).filter(Item.user_id == user_id)
    total = query.count()
    pending = query.filter(Item.completed == False).count()
    completed = query.filter(Item.completed == True).count()

    return {"total": total, "pending": pending, "completed": completed}


@app.patch("/api/items/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    update_data: ItemUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Update an item (toggle completion)."""
    item = db.query(Item).filter(Item.id == item_id, Item.user_id == user_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if update_data.completed is not None:
        item.completed = update_data.completed
        item.completed_at = datetime.utcnow() if update_data.completed else None

    db.commit()
    db.refresh(item)

    return item


@app.delete("/api/items/{item_id}")
async def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Delete an item."""
    item = db.query(Item).filter(Item.id == item_id, Item.user_id == user_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()

    return {"message": "Item deleted"}


# Forgot Password API Routes
@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """Render the forgot password page."""
    return templates.TemplateResponse("forgot_password.html", {"request": request})


@app.post("/api/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """Handle forgot password request."""
    user = get_user_by_email(db, request.email)
    if not user:
        # Don't reveal if email exists (for security)
        return {"message": "If that email exists, a reset link has been sent."}

    # Invalidate any existing reset tokens for this user
    db.query(PasswordReset).filter(PasswordReset.user_id == user.id).delete()

    # Create reset token
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)

    password_reset = PasswordReset(
        token=reset_token,
        user_id=user.id,
        expires_at=expires_at
    )
    db.add(password_reset)
    db.commit()

    # Send email
    reset_url = f"{request.url}/reset-password"
    send_password_reset_email(user.email, reset_token, reset_url)

    return {"message": "If that email exists, a reset link has been sent"}


@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request):
    """Render the reset password page."""
    return templates.TemplateResponse("reset_password.html", {"request": request})


@app.post("/api/reset-password", response_model=MessageResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Handle reset password request."""
    # Verify token
    password_reset = db.query(PasswordReset).filter(
        PasswordReset.token == request.token,
        PasswordReset.used == False
    ).first()

    if not password_reset or password_reset.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Update password
    user.hashed_password = hash_password(request.password)
    password_reset.used = True

    db.commit()

    return {"message": "Password reset successful"}
