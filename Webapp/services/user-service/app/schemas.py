"""
schemas.py

Pydantic schemas for the User Service.

Schemas define the data contracts for our API:
- What data a client can send
- What fields are required
- What validation rules apply
- What data the API returns
"""

from enum import Enum

from pydantic import BaseModel, EmailStr, Field


# =========================================================
# USER ROLE
# =========================================================

class UserRole(str, Enum):
    """
    Restrict user roles to values understood
    by the application.
    """

    RENTER = "RENTER"
    OWNER = "OWNER"
    ADMIN = "ADMIN"


# =========================================================
# CREATE USER
# =========================================================

class UserCreate(BaseModel):
    """
    Data accepted when creating a new user.

    Required:
        first_name
        last_name
        email

    Optional:
        phone

    Default:
        role = RENTER
    """

    first_name: str = Field(
        min_length=1,
        max_length=50,
    )

    last_name: str = Field(
        min_length=1,
        max_length=50,
    )

    # EmailStr validates basic email format.
    email: EmailStr

    # Phone is optional.
    phone: str | None = None

    # New users default to RENTER.
    role: UserRole = UserRole.RENTER


# =========================================================
# USER RESPONSE
# =========================================================

class UserResponse(UserCreate):
    """
    Data returned by the API.

    Inherits:
        first_name
        last_name
        email
        phone
        role

    Adds:
        id
    """

    id: int


# =========================================================
# UPDATE USER
# =========================================================

class UserUpdate(BaseModel):
    """
    Data accepted when updating an existing user.

    Every field is optional because a client may want
    to change only one or two fields.

    Example:

        {
            "phone": "9135559999"
        }
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

    phone: str | None = None

    role: UserRole | None = None