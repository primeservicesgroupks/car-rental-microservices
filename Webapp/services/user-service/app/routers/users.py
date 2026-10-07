"""
users.py

User-management routes for the Car Rental User Service.

Project 3:
    User data was moved from temporary in-memory storage
    to PostgreSQL using SQLAlchemy.

Project 4:
    Account creation has moved to:

        POST /auth/register

    because registration must securely hash the user's
    password before storing the account.

Current endpoints:

    GET /users
        Retrieve all users.

    GET /users/{user_id}
        Retrieve one user.

    PUT /users/{user_id}
        Update allowed profile information.

Future Project 4 work will protect these routes using
JWT authentication and role-based authorization.
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
from app.dependencies import get_current_user
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

# Project 3 previously contained:
#
#     POST /users
#
# That endpoint is intentionally removed in Project 4.
#
# New account creation must go through:
#
#     POST /auth/register
#
# because registration is responsible for:
#
#     1. validating registration data
#     2. validating the requested role
#     3. normalizing the email address
#     4. checking for duplicate email addresses
#     5. hashing the plaintext password
#     6. storing password_hash in PostgreSQL
#     7. returning a safe UserResponse
#
# We do NOT create users here without a password hash.


# =========================================================
# LIST USERS
# GET /users
# =========================================================

@router.get(
    "",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
)
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return all users ordered by ID.

    Project 4 note:
        This endpoint is currently public for learning
        purposes.

        Later in Project 4 it will be protected using
        JWT authentication and authorization.
    """

    statement = (
        select(User)
        .order_by(User.id)
    )

    records = db.scalars(
        statement
    ).all()

    return records


# =========================================================
# GET ONE USER
# GET /users/{user_id}
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

    Returns:
        200 - User found.

        404 - User does not exist.
    """

    record = db.get(
        User,
        user_id,
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return record


# =========================================================
# UPDATE USER
# PUT /users/{user_id}
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
    Update an existing user's profile.

    Only fields explicitly supplied in the request
    are considered for modification.

    Password changes are NOT handled here.

    Role changes are also blocked here during Project 4.
    They will eventually require appropriate authorization.
    """


    # =====================================================
    # FIND USER
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
    # GET ONLY FIELDS PROVIDED BY CLIENT
    # =====================================================

    # Example:
    #
    # Request:
    #
    # {
    #     "phone": "9135559999"
    # }
    #
    # produces:
    #
    # {
    #     "phone": "9135559999"
    # }
    #
    # Other fields remain unchanged.

    data = changes.model_dump(
        exclude_unset=True,
    )


    # =====================================================
    # PROTECT FIRST NAME
    # =====================================================

    # first_name is NOT NULL in PostgreSQL.
    #
    # Therefore:
    #
    # {
    #     "first_name": null
    # }
    #
    # must not be allowed.

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

        if data["email"] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="email cannot be null",
            )

        data["email"] = (
            str(data["email"])
            .strip()
            .lower()
        )


    # =====================================================
    # BLOCK ROLE CHANGES THROUGH PROFILE UPDATE
    # =====================================================

    # Project 3 allowed role changes because authentication
    # and authorization had not yet been implemented.
    #
    # In Project 4, allowing someone to submit:
    #
    # {
    #     "role": "ADMIN"
    # }
    #
    # through an ordinary profile update would be a
    # privilege-escalation vulnerability.
    #
    # Role management will eventually be handled through
    # an authorized administrative workflow.

    if "role" in data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Role cannot be changed through "
                "the user profile endpoint"
            ),
        )


    # =====================================================
    # APPLY CHANGES
    # =====================================================

    for key, value in data.items():
        setattr(
            record,
            key,
            value,
        )


    # =====================================================
    # SAVE CHANGES TO POSTGRESQL
    # =====================================================

    try:
        db.commit()

    except IntegrityError:

        # PostgreSQL rejected the update.
        #
        # The most likely reason in this endpoint is
        # attempting to change the email address to one
        # that already belongs to another user.

        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )


    # =====================================================
    # REFRESH ORM OBJECT
    # =====================================================

    # Reload the database row so our ORM object reflects
    # the final committed database state.

    db.refresh(record)


    # =====================================================
    # RETURN SAFE RESPONSE
    # =====================================================

    # response_model=UserResponse controls what FastAPI
    # exposes to the client.
    #
    # UserResponse must NOT contain:
    #
    #     password
    #     password_hash

    return record