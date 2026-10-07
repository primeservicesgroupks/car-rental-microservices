"""
schemas.py

Pydantic schemas for the Car Rental User Service.

Project 4 introduces authentication-related request and
response models while ensuring sensitive authentication
data is never exposed through normal API responses.

Security principles:
    - Plaintext passwords are accepted only where required
      for registration and login.
    - Passwords are never returned by the API.
    - Password hashes are never returned by the API.
    - Public registration may request normal user roles,
      but ADMIN registration is blocked in auth.py.
    - Normal profile updates cannot modify a user's role.
"""

from enum import Enum

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)


# =========================================================
# USER ROLES
# =========================================================

class UserRole(str, Enum):
    """
    Roles supported by the User Service.

    RENTER:
        Can rent vehicles.

    OWNER:
        Can eventually list/manage vehicles.

    ADMIN:
        Administrative role.

        Public ADMIN registration is blocked in auth.py.
        ADMIN accounts should eventually be provisioned
        through a trusted administrative workflow.
    """

    RENTER = "RENTER"
    OWNER = "OWNER"
    ADMIN = "ADMIN"


# =========================================================
# REGISTRATION REQUEST
# POST /auth/register
# =========================================================

class UserRegister(BaseModel):
    """
    Data accepted during public user registration.

    The plaintext password exists only long enough for the
    application to validate and hash it.

    auth.py is responsible for rejecting ADMIN registration.
    """

    first_name: str = Field(
        min_length=1,
        max_length=50,
    )

    last_name: str = Field(
        min_length=1,
        max_length=50,
    )

    email: EmailStr

    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    role: UserRole = UserRole.RENTER

    # Reject unexpected request fields rather than
    # silently ignoring them.
    model_config = ConfigDict(
        extra="forbid",
    )


# =========================================================
# LOGIN REQUEST
# POST /auth/login
# =========================================================

class LoginRequest(BaseModel):
    """
    Credentials supplied when a user logs in.

    The plaintext password is used only for verification
    against the stored password hash.
    """

    email: EmailStr

    password: str = Field(
        min_length=1,
        max_length=128,
    )

    model_config = ConfigDict(
        extra="forbid",
    )


# =========================================================
# TOKEN RESPONSE
# =========================================================

class TokenResponse(BaseModel):
    """
    Response returned after successful authentication.

    access_token:
        Signed JWT presented by the client on future
        authenticated requests.

    token_type:
        Identifies the authentication scheme.
    """

    access_token: str

    token_type: str = "bearer"


# =========================================================
# USER RESPONSE
# =========================================================

class UserResponse(BaseModel):
    """
    Safe representation of a user returned by the API.

    IMPORTANT:

    This model deliberately does NOT contain:

        password
        password_hash

    Therefore normal API responses cannot accidentally
    serialize those sensitive database fields.
    """

    id: int

    first_name: str

    last_name: str

    email: EmailStr

    phone: str | None = None

    role: UserRole

    # SQLAlchemy returns User ORM objects rather than
    # dictionaries.
    #
    # from_attributes=True allows Pydantic to read:
    #
    #     record.id
    #     record.first_name
    #     record.email
    #     etc.
    #
    # directly from the SQLAlchemy object.

    model_config = ConfigDict(
        from_attributes=True,
    )


# =========================================================
# USER PROFILE UPDATE
# PUT /users/{user_id}
# =========================================================

class UserUpdate(BaseModel):
    """
    Fields allowed during a normal profile update.

    Every field is optional because the client may update
    only one field at a time.

    Example:

        {
            "phone": "9135559999"
        }

    Notice that this schema intentionally does NOT contain:

        password
        password_hash
        role

    Password changes will require a dedicated secure flow.

    Role changes will require an authorized administrative
    workflow.
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

    # Reject fields that are not explicitly allowed.
    #
    # For example:
    #
    # {
    #     "role": "ADMIN"
    # }
    #
    # will fail Pydantic validation rather than being
    # silently ignored.

    model_config = ConfigDict(
        extra="forbid",
    )