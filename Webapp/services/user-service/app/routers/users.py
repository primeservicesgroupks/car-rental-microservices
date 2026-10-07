"""
users.py

API routes for the User Service.

Project 3:
    User data is stored persistently in PostgreSQL
    using SQLAlchemy.

Endpoints:
    POST /users
    GET  /users
    GET  /users/{user_id}
    PUT  /users/{user_id}
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, UserUpdate


# =========================================================
# ROUTER CONFIGURATION
# =========================================================

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


# =========================================================
# CREATE USER
# POST /users
# =========================================================

@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new user in PostgreSQL.
    """

    # Normalize email before storing it.
    #
    # Example:
    #   John@Example.com
    #
    # becomes:
    #   john@example.com

    email = str(user.email).strip().lower()


    # -----------------------------------------------------
    # FRIENDLY DUPLICATE CHECK
    # -----------------------------------------------------

    # SQL equivalent:
    #
    # SELECT *
    # FROM users
    # WHERE email = 'john@example.com';

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )


    # -----------------------------------------------------
    # BUILD ORM OBJECT
    # -----------------------------------------------------

    # model_dump() converts the Pydantic object to a dict.
    #
    # We exclude email because we want to use our
    # normalized lowercase version.
    #
    # We exclude role because Pydantic uses UserRole,
    # while PostgreSQL stores the role as text.

    record = User(
        **user.model_dump(
            exclude={"email", "role"}
        ),
        email=email,
        role=user.role.value,
    )


    # Add the new object to the SQLAlchemy Session.

    db.add(record)


    # -----------------------------------------------------
    # SAVE TO POSTGRESQL
    # -----------------------------------------------------

    try:
        db.commit()

    except IntegrityError:

        # A failed transaction must be rolled back
        # before this Session can continue being used.

        db.rollback()

        # PostgreSQL's UNIQUE email protection handles
        # cases such as two concurrent requests attempting
        # to create the same email.

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )


    # Reload database-generated values such as ID.

    db.refresh(record)

    return record


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
):
    """
    Return all users ordered by ID.
    """

    statement = select(User).order_by(User.id)

    return db.scalars(statement).all()


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
):
    """
    Retrieve one user using the primary key.
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
):
    """
    Update an existing user.

    Only fields explicitly supplied by the client
    will be modified.
    """

    # -----------------------------------------------------
    # FIND EXISTING USER
    # -----------------------------------------------------

    record = db.get(
        User,
        user_id,
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


    # -----------------------------------------------------
    # GET REQUESTED CHANGES
    # -----------------------------------------------------

    # exclude_unset=True means only fields explicitly
    # included in the request are returned.

    data = changes.model_dump(
        exclude_unset=True,
    )


    # -----------------------------------------------------
    # PROTECT REQUIRED FIELDS
    # -----------------------------------------------------

    # These database columns are NOT NULL.
    #
    # Therefore a client should not be able to explicitly
    # update them to None.

    if (
        "first_name" in data
        and data["first_name"] is None
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="first_name cannot be null",
        )


    if (
        "last_name" in data
        and data["last_name"] is None
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="last_name cannot be null",
        )


    # -----------------------------------------------------
    # NORMALIZE EMAIL
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # CONVERT ROLE ENUM TO DATABASE STRING
    # -----------------------------------------------------

    if "role" in data:

        if data["role"] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="role cannot be null",
            )

        data["role"] = data["role"].value


    # -----------------------------------------------------
    # APPLY CHANGES TO ORM OBJECT
    # -----------------------------------------------------

    for key, value in data.items():
        setattr(
            record,
            key,
            value,
        )


    # -----------------------------------------------------
    # SAVE CHANGES
    # -----------------------------------------------------

    try:
        db.commit()

    except IntegrityError:

        db.rollback()

        # Most likely the update attempted to use an
        # email address that already belongs to another
        # user.

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )


    # Reload the updated database row.

    db.refresh(record)

    return record