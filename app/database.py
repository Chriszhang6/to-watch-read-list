import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# Handle Heroku PostgreSQL URL format
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)

    # Migration: Add local_date column if it doesn't exist
    with engine.connect() as conn:
        if DATABASE_URL.startswith("sqlite"):
            # Check if column exists in SQLite
            result = conn.execute(text("PRAGMA table_info(items)"))
            columns = [row[1] for row in result.fetchall()]
            if 'local_date' not in columns:
                conn.execute(text("ALTER TABLE items ADD COLUMN local_date VARCHAR"))
                conn.commit()
        else:
            # PostgreSQL
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'items' AND column_name = 'local_date'
            """))
            if not result.fetchone():
                conn.execute(text("ALTER TABLE items ADD COLUMN local_date VARCHAR"))
                conn.commit()
