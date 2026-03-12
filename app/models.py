from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("Item", back_populates="owner")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    title = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    source_type = Column(String, default="other")  # youtube, article, other
    captured_at = Column(DateTime, default=datetime.utcnow)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    owner = relationship("User", back_populates="items")
