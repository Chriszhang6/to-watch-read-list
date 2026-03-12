from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator


class ItemCreate(BaseModel):
    url: str


class ItemUpdate(BaseModel):
    completed: Optional[bool] = None


class ItemResponse(BaseModel):
    id: int
    url: str
    title: Optional[str]
    summary: Optional[str]
    source_type: str
    captured_at: datetime
    completed: bool
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ItemListResponse(BaseModel):
    items: List[ItemResponse]
    total: int


class RegisterRequest(BaseModel):
    email: str
    password: str

    @field_validator('email')
    @classmethod
    def email_must_be_valid(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email address')
        return v.lower()

    @field_validator('password')
    @classmethod
    def password_must_be_strong(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator('email')
    @classmethod
    def email_to_lower(cls, v):
        return v.lower()


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    message: str
