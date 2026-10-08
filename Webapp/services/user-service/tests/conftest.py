"""
conftest.py

Shared pytest fixtures for the Car Rental User Service.

Project 4 automated tests use these fixtures to provide:

    - FastAPI TestClient
    - PostgreSQL database access
    - automatic cleanup of pytest-created users
    - reusable registration helper
    - reusable login helper

IMPORTANT:
    These tests currently use the local development PostgreSQL
    database.

    To protect normal development users, every automated test
    account MUST use an email address beginning with:

        pytest-

    Example:

        pytest-renter@example.com

    The cleanup fixture removes only users whose email begins
    with "pytest-".
"""

import pytest

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db import SessionLocal
from app.main import app
from app.models import User


# =========================================================
# TEST EMAIL CONVENTION
# =========================================================

# All automated test accounts MUST begin with:
#
#     pytest-
#
# Examples:
#
#     pytest-renter@example.com
#     pytest-owner@example.com
#     pytest-login@example.com
#
# This gives us a predictable and safe way to identify
# automated test accounts.

TEST_EMAIL_PREFIX = "pytest-"


# =========================================================
# FASTAPI TEST CLIENT
# =========================================================

@pytest.fixture
def client():
    """
    Provide a FastAPI TestClient.

    TestClient allows pytest to call FastAPI endpoints
    directly without manually starting Uvicorn.

    Example:

        response = client.get("/health")
    """

    with TestClient(app) as test_client:
        yield test_client


# =========================================================
# DATABASE SESSION
# =========================================================

@pytest.fixture
def db():
    """
    Provide direct PostgreSQL access for tests that need
    to inspect database state.

    Example uses:

        - Verify password_hash was stored.
        - Verify plaintext passwords were not stored.
        - Inspect user roles.
    """

    session = SessionLocal()

    try:
        yield session

    finally:
        session.close()


# =========================================================
# AUTOMATIC TEST USER CLEANUP
# =========================================================

@pytest.fixture(autouse=True)
def cleanup_test_users():
    """
    Remove pytest-created users before AND after each test.

    Only users whose email begins with:

        pytest-

    are deleted.

    Normal development accounts such as:

        ade.project4@example.com
        owner.project4@example.com
        local-admin@example.com

    are not affected.

    Running cleanup before each test prevents a previous
    failed test from causing duplicate-email conflicts.

    Running cleanup after each test keeps the local
    development database clean.
    """

    def cleanup():
        with SessionLocal() as session:

            statement = delete(User).where(
                User.email.like(
                    f"{TEST_EMAIL_PREFIX}%"
                )
            )

            session.execute(statement)

            session.commit()

    # -----------------------------------------------------
    # CLEAN BEFORE TEST
    # -----------------------------------------------------

    cleanup()

    # Run the actual pytest test.
    yield

    # -----------------------------------------------------
    # CLEAN AFTER TEST
    # -----------------------------------------------------

    cleanup()


# =========================================================
# REGISTRATION HELPER
# =========================================================

@pytest.fixture
def register_user(client):
    """
    Return a reusable function for registering test users.

    Example:

        response = register_user(
            email="pytest-renter@example.com"
        )

    The default role is RENTER.

    ADMIN registration should still be rejected by the
    public registration endpoint.
    """

    def _register_user(
        email: str,
        password: str = "LearningPassword123!",
        role: str = "RENTER",
        first_name: str = "Pytest",
        last_name: str = "User",
        phone: str | None = None,
    ):

        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": password,
            "role": role,
        }

        # Only include phone when one was supplied.
        if phone is not None:
            payload["phone"] = phone

        return client.post(
            "/auth/register",
            json=payload,
        )

    return _register_user


# =========================================================
# LOGIN HELPER
# =========================================================

@pytest.fixture
def login_user(client):
    """
    Return a reusable function for authenticating users.

    Example:

        response = login_user(
            email="pytest-renter@example.com",
            password="LearningPassword123!",
        )
    """

    def _login_user(
        email: str,
        password: str,
    ):

        return client.post(
            "/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

    return _login_user