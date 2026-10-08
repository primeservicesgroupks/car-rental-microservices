"""
test_registration.py

Automated tests for POST /auth/register.

Tests:
    - RENTER registration
    - OWNER registration
    - ADMIN registration rejection
    - Duplicate email protection
    - Password hashing
    - Safe API responses
    - Email normalization
"""

from sqlalchemy import select

from app.models import User


# =========================================================
# RENTER REGISTRATION
# =========================================================

def test_register_renter_success(client):
    """
    Public RENTER registration should succeed.
    """

    email = "pytest-renter-registration@example.com"

    response = client.post(
        "/auth/register",
        json={
            "first_name": "Test",
            "last_name": "Renter",
            "email": email,
            "password": "LearningPassword123!",
            "role": "RENTER",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == email
    assert data["role"] == "RENTER"
    assert data["first_name"] == "Test"
    assert data["last_name"] == "Renter"
    assert "id" in data

    # Sensitive information must never be returned.
    assert "password" not in data
    assert "password_hash" not in data


# =========================================================
# OWNER REGISTRATION
# =========================================================

def test_register_owner_success(client):
    """
    Public OWNER registration should succeed.
    """

    email = "pytest-owner-registration@example.com"

    response = client.post(
        "/auth/register",
        json={
            "first_name": "Test",
            "last_name": "Owner",
            "email": email,
            "password": "LearningPassword123!",
            "role": "OWNER",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == email
    assert data["role"] == "OWNER"

    assert "password" not in data
    assert "password_hash" not in data


# =========================================================
# ADMIN REGISTRATION REJECTION
# =========================================================

def test_register_admin_rejected(client):
    """
    Public registration must not create ADMIN accounts.
    """

    response = client.post(
        "/auth/register",
        json={
            "first_name": "Test",
            "last_name": "Admin",
            "email": "pytest-admin-registration@example.com",
            "password": "LearningPassword123!",
            "role": "ADMIN",
        },
    )

    assert response.status_code == 403

    data = response.json()

    assert "detail" in data


# =========================================================
# DUPLICATE EMAIL
# =========================================================

def test_duplicate_email_rejected(register_user):
    """
    Email uniqueness should be case-insensitive because
    registration normalizes email addresses.
    """

    first_response = register_user(
        email="pytest-duplicate@example.com",
    )

    assert first_response.status_code == 201

    second_response = register_user(
        email="PYTEST-DUPLICATE@EXAMPLE.COM",
    )

    assert second_response.status_code == 409

    assert (
        second_response.json()["detail"]
        == "Email already exists"
    )


# =========================================================
# PASSWORD HASHING
# =========================================================

def test_password_is_hashed_in_database(
    client,
    db,
):
    """
    Verify that plaintext passwords are never stored.
    """

    email = "pytest-hash-test@example.com"
    plaintext_password = "LearningPassword123!"

    response = client.post(
        "/auth/register",
        json={
            "first_name": "Hash",
            "last_name": "Test",
            "email": email,
            "password": plaintext_password,
            "role": "RENTER",
        },
    )

    assert response.status_code == 201

    record = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    assert record is not None

    # Database must not contain plaintext password.
    assert record.password_hash != plaintext_password

    # pwdlib recommended hashing currently produces
    # Argon2 hashes.
    assert record.password_hash.startswith("$argon2")

    # Hash must never appear in the API response.
    data = response.json()

    assert "password" not in data
    assert "password_hash" not in data


# =========================================================
# EMAIL NORMALIZATION
# =========================================================

def test_registration_normalizes_email(client):
    """
    Registration should normalize email to lowercase.
    """

    response = client.post(
        "/auth/register",
        json={
            "first_name": "Email",
            "last_name": "Normalize",
            "email": "PYTEST-NORMALIZE@EXAMPLE.COM",
            "password": "LearningPassword123!",
            "role": "RENTER",
        },
    )

    assert response.status_code == 201

    assert (
        response.json()["email"]
        == "pytest-normalize@example.com"
    )