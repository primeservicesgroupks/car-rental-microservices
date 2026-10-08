"""
test_jwt.py

Automated tests for JWT validation and authenticated
identity.

Tests:
    - Valid JWT
    - GET /auth/me
    - Missing JWT
    - Invalid JWT
    - Expired JWT
    - JWT without subject
    - JWT referencing nonexistent user
"""

from datetime import (
    datetime,
    timedelta,
    timezone,
)

import jwt

from app.security import (
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
)


# =========================================================
# HELPER
# =========================================================

def get_valid_token(
    register_user,
    login_user,
    email="pytest-jwt-valid@example.com",
):
    """
    Register a test user, log in, and return its JWT.
    """

    password = "LearningPassword123!"

    registration = register_user(
        email=email,
        password=password,
    )

    assert registration.status_code == 201

    login_response = login_user(
        email=email,
        password=password,
    )

    assert login_response.status_code == 200

    return login_response.json()["access_token"]


# =========================================================
# VALID JWT / AUTHENTICATED IDENTITY
# =========================================================

def test_auth_me_with_valid_token(
    client,
    register_user,
    login_user,
):
    """
    A valid JWT should resolve the current user.
    """

    email = "pytest-jwt-me@example.com"

    token = get_valid_token(
        register_user,
        login_user,
        email=email,
    )

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == email
    assert data["role"] == "RENTER"

    assert "password" not in data
    assert "password_hash" not in data


# =========================================================
# MISSING TOKEN
# =========================================================

def test_auth_me_without_token(client):
    """
    A protected endpoint requires authentication.
    """

    response = client.get("/auth/me")

    assert response.status_code == 401


# =========================================================
# INVALID TOKEN
# =========================================================

def test_auth_me_with_invalid_token(client):
    """
    A malformed token should return 401.
    """

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": (
                "Bearer this-is-not-a-valid-jwt"
            )
        },
    )

    assert response.status_code == 401


# =========================================================
# EXPIRED TOKEN
# =========================================================

def test_expired_token_rejected(client):
    """
    A correctly signed but expired JWT must be rejected.
    """

    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub": "999999",
            "iat": now - timedelta(minutes=10),
            "exp": now - timedelta(minutes=5),
        },
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 401


# =========================================================
# MISSING SUBJECT
# =========================================================

def test_token_without_subject_rejected(client):
    """
    A signed token without the sub claim does not
    identify an authenticated user.
    """

    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 401


# =========================================================
# NONEXISTENT USER
# =========================================================

def test_token_for_nonexistent_user_rejected(client):
    """
    Even a correctly signed token must fail when its
    subject references a user that does not exist.
    """

    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub": "999999999",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 401