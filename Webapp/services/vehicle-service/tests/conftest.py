"""Isolated tests: use an in-memory SQLite DB, never local PostgreSQL."""
import os
from datetime import datetime, timedelta, timezone
import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Configure environment before importing application modules.
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ["JWT_SECRET_KEY"] = "project5-only-test-signing-key-not-for-production"
os.environ["JWT_ALGORITHM"] = "HS256"
from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app import models  # noqa: F401,E402

@pytest.fixture
def client():
    """Fresh schema per test; override request-scoped SQLAlchemy dependency."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)  # Tests only; production uses Alembic.
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()

@pytest.fixture
def auth_header():
    """Produce signed test JWTs for role/ownership scenarios."""
    def make(user_id=10, role="OWNER", *, expired=False, secret=None):
        expiration = datetime.now(timezone.utc) + timedelta(
            minutes=-5 if expired else 30
        )
        token = jwt.encode(
            {"sub": str(user_id), "role": role, "exp": expiration},
            secret or os.environ["JWT_SECRET_KEY"],
            algorithm="HS256",
        )
        return {"Authorization": f"Bearer {token}"}
    return make

@pytest.fixture
def vehicle_payload():
    return {
        "make": "Toyota", "model": "Camry", "year": 2012,
        "color": "Silver", "daily_rate": "45.00",
        "city": "Olathe", "state": "KS",
    }
