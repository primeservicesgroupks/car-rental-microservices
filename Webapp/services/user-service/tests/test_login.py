"""
test_login.py

Automated tests for POST /auth/login.

Tests:
    - Successful login
    - Wrong password
    - Unknown user
    - Case-insensitive email login
    - Safe token response
"""

# =========================================================
# SUCCESSFUL LOGIN
# =========================================================

def test_login_success(
    register_user,
    login_user,
):
    """
    Correct credentials should return a JWT.
    """

    email = "pytest-login-success@example.com"
    password = "LearningPassword123!"

    registration = register_user(
        email=email,
        password=password,
    )

    assert registration.status_code == 201

    response = login_user(
        email=email,
        password=password,
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["access_token"]
    assert data["token_type"] == "bearer"

    # Login must never return password information.
    assert "password" not in data
    assert "password_hash" not in data


# =========================================================
# WRONG PASSWORD
# =========================================================

def test_login_wrong_password(
    register_user,
    login_user,
):
    """
    Correct email with wrong password should fail.
    """

    email = "pytest-wrong-password@example.com"

    registration = register_user(
        email=email,
        password="CorrectPassword123!",
    )

    assert registration.status_code == 201

    response = login_user(
        email=email,
        password="WrongPassword123!",
    )

    assert response.status_code == 401


# =========================================================
# UNKNOWN USER
# =========================================================

def test_login_unknown_email(
    login_user,
):
    """
    Login for a nonexistent account should fail.
    """

    response = login_user(
        email="pytest-missing-user@example.com",
        password="LearningPassword123!",
    )

    assert response.status_code == 401


# =========================================================
# EMAIL NORMALIZATION DURING LOGIN
# =========================================================

def test_login_email_is_case_insensitive(
    register_user,
    login_user,
):
    """
    Login should normalize the submitted email.
    """

    email = "pytest-case-login@example.com"
    password = "LearningPassword123!"

    registration = register_user(
        email=email,
        password=password,
    )

    assert registration.status_code == 201

    response = login_user(
        email="PYTEST-CASE-LOGIN@EXAMPLE.COM",
        password=password,
    )

    assert response.status_code == 200

    assert "access_token" in response.json()