"""
schemas.py

Pydantic schemas for the User Service.

These schemas define the API data contracts.

They control:
- What data clients may send.
- How incoming data is validated.
- What data the API returns.

Important:
Pydantic schemas are NOT database tables.
Database tables are defined in models.py.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# =========================================================
# USER ROLES
# =========================================================

class UserRole(str, Enum):
    """
    Roles currently supported by the User Service.
    """

    RENTER = "RENTER"
    OWNER = "OWNER"
    ADMIN = "ADMIN"


# =========================================================
# CREATE USER SCHEMA
# =========================================================

class UserCreate(BaseModel):
    """
    Data accepted when a client creates a new user.

    Example:
        POST /users
    """

    first_name: str = Field(
        min_length=1,
        max_length=50,
    )

    last_name: str = Field(
        min_length=1,
        max_length=50,
    )

    # EmailStr validates that the value looks like
    # a properly formatted email address.
    email: EmailStr

    # Phone number is optional.
    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    # New users default to RENTER.
    role: UserRole = UserRole.RENTER


# =========================================================
# USER RESPONSE SCHEMA
# =========================================================

class UserResponse(UserCreate):
    """
    Data returned by the API for a user.

    UserResponse inherits the fields from UserCreate:

        first_name
        last_name
        email
        phone
        role

    and adds the database-generated user ID.
    """

    id: int

    # Allows Pydantic to create this response from
    # SQLAlchemy ORM objects.
    #
    # Example:
    #
    # SQLAlchemy:
    #     user.id
    #     user.first_name
    #     user.email
    #
    # Pydantic can read those attributes and serialize
    # them into the API response.

    model_config = ConfigDict(
        from_attributes=True,
    )


# =========================================================
# UPDATE USER SCHEMA
# =========================================================

class UserUpdate(BaseModel):
    """
    Data accepted when updating an existing user.

    All fields are optional because the client may want
    to update only one or two fields.
    """

    first_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    last_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    email: EmailStr | None = None

    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    role: UserRole | None = None