from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, HttpUrl


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


class LoginRequest(BaseModel):
    password: str


class MessageResponse(BaseModel):
    message: str
