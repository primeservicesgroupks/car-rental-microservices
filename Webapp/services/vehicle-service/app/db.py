"""Database engine, declarative metadata, and per-request sessions."""
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Resolve .env relative to the service, not the terminal's working directory.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing; configure vehicle-service/.env")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

class Base(DeclarativeBase):
    """All Vehicle Service tables inherit from this metadata registry."""

def get_db():
    """Yield one SQLAlchemy session and close it after the HTTP request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
