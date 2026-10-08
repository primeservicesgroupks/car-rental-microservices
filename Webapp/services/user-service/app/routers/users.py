"""
users.py

User-management routes for the Car Rental User Service.

Project 3:
    - User data moved from in-memory storage to PostgreSQL.
    - SQLAlchemy became the persistence layer.

Project 4:
    - Account creation moved to POST /auth/register.
    - JWT authentication protects user-management endpoints.
    - Role-based access control protects administrative operations.
    - Ownership authorization prevents users from accessing or
      modifying another user's profile.

Authorization policy:

    GET /users
        ADMIN only.

    GET /users/{user_id}
        The user may retrieve their own profile.
        ADMIN may retrieve any user's profile.

    PUT /users/{user_id}
        The user may update their own profile.
        ADMIN may update any user's allowed profile fields.

Important:
    Password changes are NOT handled by this router.

    Role changes are NOT handled by this router.

    UserUpdate intentionally excludes password, password_hash,
    and role.
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import (
    get_current_user,
    require_role,
)
from app.models import User
from app.schemas import (
    UserResponse,
    UserUpdate,
)


# =========================================================
# ROUTER CONFIGURATION
# =========================================================

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


# =========================================================
# IMPORTANT PROJECT 4 DESIGN CHANGE
# =========================================================

# Project 3 previously allowed:
#
#     POST /users
#
# That endpoint has intentionally been removed.
#
# Account creation now happens through:
#
#     POST /auth/register
#
# The registration workflow is responsible for:
#
#     - validating registration data
#     - validating the requested role
#     - blocking public ADMIN registration
#     - normalizing the email address
#     - checking duplicate email addresses
#     - hashing the plaintext password
#     - storing password_hash
#     - returning a safe UserResponse
#
# This gives the application one controlled account-
# creation workflow.


# =========================================================
# LIST ALL USERS
# GET /users
# ADMIN ONLY
# =========================================================

@router.get(
    "",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
)
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("ADMIN")
    ),
):
    """
    Return all users ordered by ID.

    Authorization:
        ADMIN only.

    RENTER:
        403 Forbidden

    OWNER:
        403 Forbidden

    ADMIN:
        200 OK

    Authentication and ADMIN-role validation are performed
    by require_role("ADMIN").
    """

    # -----------------------------------------------------
    # QUERY USERS
    # -----------------------------------------------------

    statement = (
        select(User)
        .order_by(User.id)
    )

    records = db.scalars(
        statement
    ).all()

    # UserResponse controls serialization and prevents
    # sensitive fields such as password_hash from being
    # exposed.

    return records


# =========================================================
# GET ONE USER
# GET /users/{user_id}
# OWN PROFILE OR ADMIN
# =========================================================

@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve one user by primary-key ID.

    Authorization:

        Normal users:
            May retrieve only their own profile.

        ADMIN:
            May retrieve any user's profile.

    Authentication:
        A valid Bearer JWT is required.
    """


    # =====================================================
    # AUTHORIZATION
    # =====================================================

    # Allow the request when:
    #
    #     current_user.id == user_id
    #
    # OR:
    #
    #     current_user.role == "ADMIN"
    #
    # Deny when BOTH are false.

    if (
        current_user.id != user_id
        and current_user.role != "ADMIN"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission "
                "to access this user"
            ),
        )


    # =====================================================
    # FIND TARGET USER
    # =====================================================

    record = db.get(
        User,
        user_id,
    )


    # =====================================================
    # USER DOES NOT EXIST
    # =====================================================

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


    # =====================================================
    # RETURN SAFE USER RESPONSE
    # =====================================================

    return record


# =========================================================
# UPDATE USER
# PUT /users/{user_id}
# OWN PROFILE OR ADMIN
# =========================================================

@router.put(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def update_user(
    user_id: int,
    changes: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing user's allowed profile fields.

    Authorization:

        Normal users:
            May update only their own profile.

        ADMIN:
            May update any user's allowed profile fields.

    The following fields are intentionally NOT handled
    through this endpoint:

        password
        password_hash
        role

    Password and role management require separate,
    controlled workflows.
    """


    # =====================================================
    # AUTHORIZATION
    # =====================================================

    # A normal authenticated user may update only the
    # database record matching their authenticated ID.
    #
    # ADMIN users may update another user's normal
    # profile information.

    if (
        current_user.id != user_id
        and current_user.role != "ADMIN"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission "
                "to modify this user"
            ),
        )


    # =====================================================
    # FIND TARGET USER
    # =====================================================

    record = db.get(
        User,
        user_id,
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


    # =====================================================
    # GET REQUESTED CHANGES
    # =====================================================

    # exclude_unset=True is important.
    #
    # Suppose the request contains:
    #
    # {
    #     "phone": "9135559999"
    # }
    #
    # Then data becomes:
    #
    # {
    #     "phone": "9135559999"
    # }
    #
    # Fields not included by the client remain unchanged.

    data = changes.model_dump(
        exclude_unset=True,
    )


    # =====================================================
    # PROTECT FIRST NAME
    # =====================================================

    # first_name is NOT NULL in PostgreSQL.
    #
    # Therefore an explicit:
    #
    # {
    #     "first_name": null
    # }
    #
    # must be rejected.

    if (
        "first_name" in data
        and data["first_name"] is None
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="first_name cannot be null",
        )


    # =====================================================
    # PROTECT LAST NAME
    # =====================================================

    if (
        "last_name" in data
        and data["last_name"] is None
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="last_name cannot be null",
        )


    # =====================================================
    # NORMALIZE EMAIL
    # =====================================================

    if "email" in data:

        # Email is NOT NULL in PostgreSQL.

        if data["email"] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="email cannot be null",
            )

        # Normalize email addresses before storing them.
        #
        # Example:
        #
        #     Ade@Example.com
        #
        # becomes:
        #
        #     ade@example.com

        data["email"] = (
            str(data["email"])
            .strip()
            .lower()
        )


    # =====================================================
    # APPLY ALLOWED CHANGES
    # =====================================================

    # UserUpdate determines which fields may reach this
    # point.
    #
    # Because UserUpdate does NOT contain:
    #
    #     role
    #     password
    #     password_hash
    #
    # those security-sensitive fields cannot be changed
    # through this profile endpoint.

    for key, value in data.items():
        setattr(
            record,
            key,
            value,
        )


    # =====================================================
    # SAVE CHANGES
    # =====================================================

    try:
        db.commit()

    except IntegrityError:

        # PostgreSQL rejected the transaction.
        #
        # The most likely reason here is an attempt to
        # change the user's email to an address already
        # assigned to another user.

        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )


    # =====================================================
    # REFRESH ORM OBJECT
    # =====================================================

    # Reload database-generated/final values after commit.

    db.refresh(record)


    # =====================================================
    # RETURN SAFE RESPONSE
    # =====================================================

    # response_model=UserResponse ensures fields such as
    # password_hash are never serialized into the response.

    return record