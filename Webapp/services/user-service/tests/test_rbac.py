"""
test_rbac.py

Automated Role-Based Access Control and ownership tests.

Security policy:

GET /users
    ADMIN only.

GET /users/{user_id}
    Own user or ADMIN.

PUT /users/{user_id}
    Own user or ADMIN.

Public users must not be able to promote themselves
to ADMIN through the profile update endpoint.
"""

from sqlalchemy import select

from app.db import SessionLocal
from app.models import User


# =========================================================
# HELPER
# =========================================================

def create_authenticated_user(
    client,
    email: str,
    role: str,
):
    """
    Create an authenticated test identity.

    RENTER and OWNER:
        Registered normally through /auth/register.

    ADMIN:
        Initially registered as RENTER because public
        ADMIN registration is intentionally blocked.

        The test then directly modifies the test user's
        database role to ADMIN.

    Returns:
        (user_id, access_token)
    """

    password = "LearningPassword123!"

    public_role = (
        role
        if role != "ADMIN"
        else "RENTER"
    )

    registration = client.post(
        "/auth/register",
        json={
            "first_name": "RBAC",
            "last_name": role.title(),
            "email": email,
            "password": password,
            "role": public_role,
        },
    )

    assert registration.status_code == 201

    user_id = registration.json()["id"]


    # -----------------------------------------------------
    # TEST ADMIN PROVISIONING
    # -----------------------------------------------------

    if role == "ADMIN":

        with SessionLocal() as db:

            user = db.scalar(
                select(User).where(
                    User.id == user_id
                )
            )

            assert user is not None

            user.role = "ADMIN"

            db.commit()


    # -----------------------------------------------------
    # LOGIN
    # -----------------------------------------------------

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return user_id, token


# =========================================================
# AUTH HEADER HELPER
# =========================================================

def bearer(token: str) -> dict[str, str]:
    """
    Build the HTTP Authorization header.
    """

    return {
        "Authorization": f"Bearer {token}"
    }


# =========================================================
# GET /users
# =========================================================

def test_renter_cannot_list_users(client):
    """
    RENTER must not list every user.
    """

    _, token = create_authenticated_user(
        client,
        "pytest-rbac-renter-list@example.com",
        "RENTER",
    )

    response = client.get(
        "/users",
        headers=bearer(token),
    )

    assert response.status_code == 403


def test_owner_cannot_list_users(client):
    """
    OWNER must not list every user.
    """

    _, token = create_authenticated_user(
        client,
        "pytest-rbac-owner-list@example.com",
        "OWNER",
    )

    response = client.get(
        "/users",
        headers=bearer(token),
    )

    assert response.status_code == 403


def test_admin_can_list_users(client):
    """
    ADMIN may list users.
    """

    _, token = create_authenticated_user(
        client,
        "pytest-rbac-admin-list@example.com",
        "ADMIN",
    )

    response = client.get(
        "/users",
        headers=bearer(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    # Password hashes must never leak through ADMIN APIs.
    for user in data:
        assert "password" not in user
        assert "password_hash" not in user


# =========================================================
# OWN PROFILE ACCESS
# =========================================================

def test_renter_can_read_own_profile(client):
    """
    RENTER may retrieve their own profile.
    """

    user_id, token = create_authenticated_user(
        client,
        "pytest-rbac-own-renter@example.com",
        "RENTER",
    )

    response = client.get(
        f"/users/{user_id}",
        headers=bearer(token),
    )

    assert response.status_code == 200

    assert response.json()["id"] == user_id


def test_owner_can_read_own_profile(client):
    """
    OWNER may retrieve their own profile.
    """

    user_id, token = create_authenticated_user(
        client,
        "pytest-rbac-own-owner@example.com",
        "OWNER",
    )

    response = client.get(
        f"/users/{user_id}",
        headers=bearer(token),
    )

    assert response.status_code == 200

    assert response.json()["id"] == user_id


# =========================================================
# SAME ROLE DOES NOT MEAN SAME IDENTITY
# =========================================================

def test_renter_cannot_read_other_renter(client):
    """
    RENTER #1 must not retrieve RENTER #2.

    This proves authorization checks identity, not merely
    the user's role.
    """

    first_id, first_token = create_authenticated_user(
        client,
        "pytest-rbac-renter-one@example.com",
        "RENTER",
    )

    second_id, _ = create_authenticated_user(
        client,
        "pytest-rbac-renter-two@example.com",
        "RENTER",
    )

    assert first_id != second_id

    response = client.get(
        f"/users/{second_id}",
        headers=bearer(first_token),
    )

    assert response.status_code == 403


# =========================================================
# CROSS-ROLE ACCESS
# =========================================================

def test_renter_cannot_read_owner(client):
    """
    RENTER must not retrieve another OWNER's profile.
    """

    _, renter_token = create_authenticated_user(
        client,
        "pytest-rbac-reader-renter@example.com",
        "RENTER",
    )

    owner_id, _ = create_authenticated_user(
        client,
        "pytest-rbac-target-owner@example.com",
        "OWNER",
    )

    response = client.get(
        f"/users/{owner_id}",
        headers=bearer(renter_token),
    )

    assert response.status_code == 403


def test_owner_cannot_read_renter(client):
    """
    OWNER must not retrieve another RENTER's profile.
    """

    _, owner_token = create_authenticated_user(
        client,
        "pytest-rbac-reader-owner@example.com",
        "OWNER",
    )

    renter_id, _ = create_authenticated_user(
        client,
        "pytest-rbac-target-renter@example.com",
        "RENTER",
    )

    response = client.get(
        f"/users/{renter_id}",
        headers=bearer(owner_token),
    )

    assert response.status_code == 403


# =========================================================
# ADMIN READ OVERRIDE
# =========================================================

def test_admin_can_read_other_user(client):
    """
    ADMIN may retrieve another user's profile.
    """

    renter_id, _ = create_authenticated_user(
        client,
        "pytest-rbac-admin-target@example.com",
        "RENTER",
    )

    _, admin_token = create_authenticated_user(
        client,
        "pytest-rbac-admin-reader@example.com",
        "ADMIN",
    )

    response = client.get(
        f"/users/{renter_id}",
        headers=bearer(admin_token),
    )

    assert response.status_code == 200

    assert response.json()["id"] == renter_id


# =========================================================
# OWN PROFILE UPDATE
# =========================================================

def test_renter_can_update_own_profile(client):
    """
    RENTER may update allowed fields on their own profile.
    """

    user_id, token = create_authenticated_user(
        client,
        "pytest-rbac-update-own@example.com",
        "RENTER",
    )

    response = client.put(
        f"/users/{user_id}",
        headers=bearer(token),
        json={
            "phone": "9135551111"
        },
    )

    assert response.status_code == 200

    assert (
        response.json()["phone"]
        == "9135551111"
    )


def test_owner_can_update_own_profile(client):
    """
    OWNER may update allowed fields on their own profile.
    """

    user_id, token = create_authenticated_user(
        client,
        "pytest-rbac-owner-update-own@example.com",
        "OWNER",
    )

    response = client.put(
        f"/users/{user_id}",
        headers=bearer(token),
        json={
            "phone": "9135552222"
        },
    )

    assert response.status_code == 200

    assert (
        response.json()["phone"]
        == "9135552222"
    )


# =========================================================
# CROSS-USER UPDATE DENIAL
# =========================================================

def test_renter_cannot_update_other_user(client):
    """
    RENTER must not modify another user.
    """

    _, attacker_token = create_authenticated_user(
        client,
        "pytest-rbac-update-attacker@example.com",
        "RENTER",
    )

    target_id, _ = create_authenticated_user(
        client,
        "pytest-rbac-update-target@example.com",
        "RENTER",
    )

    response = client.put(
        f"/users/{target_id}",
        headers=bearer(attacker_token),
        json={
            "phone": "9135559999"
        },
    )

    assert response.status_code == 403


def test_owner_cannot_update_other_user(client):
    """
    OWNER must not modify another user's profile.
    """

    _, owner_token = create_authenticated_user(
        client,
        "pytest-rbac-owner-attacker@example.com",
        "OWNER",
    )

    target_id, _ = create_authenticated_user(
        client,
        "pytest-rbac-owner-target@example.com",
        "RENTER",
    )

    response = client.put(
        f"/users/{target_id}",
        headers=bearer(owner_token),
        json={
            "phone": "9135558888"
        },
    )

    assert response.status_code == 403


# =========================================================
# ADMIN UPDATE OVERRIDE
# =========================================================

def test_admin_can_update_other_user(client):
    """
    ADMIN may update another user's allowed profile fields.
    """

    target_id, _ = create_authenticated_user(
        client,
        "pytest-rbac-admin-update-target@example.com",
        "RENTER",
    )

    _, admin_token = create_authenticated_user(
        client,
        "pytest-rbac-admin-update@example.com",
        "ADMIN",
    )

    response = client.put(
        f"/users/{target_id}",
        headers=bearer(admin_token),
        json={
            "phone": "9135557777"
        },
    )

    assert response.status_code == 200

    assert (
        response.json()["phone"]
        == "9135557777"
    )


# =========================================================
# ROLE ESCALATION
# =========================================================

def test_user_cannot_promote_self_to_admin(client):
    """
    Normal profile updates must not allow role changes.

    UserUpdate should reject unknown role input.
    """

    user_id, token = create_authenticated_user(
        client,
        "pytest-rbac-role-escalation@example.com",
        "RENTER",
    )

    response = client.put(
        f"/users/{user_id}",
        headers=bearer(token),
        json={
            "role": "ADMIN"
        },
    )

    assert response.status_code == 422


# =========================================================
# MISSING AUTHENTICATION
# =========================================================

def test_users_endpoint_requires_authentication(client):
    """
    GET /users requires authentication before RBAC.
    """

    response = client.get("/users")

    assert response.status_code == 401