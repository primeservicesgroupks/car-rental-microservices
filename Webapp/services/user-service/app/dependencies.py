"""
dependencies.py

Reusable FastAPI dependencies for authentication.

Responsibilities:
    - Extract Bearer tokens from HTTP requests.
    - Decode and validate JWT access tokens.
    - Extract the authenticated user's identity.
    - Load the authenticated user from PostgreSQL.

Future Project 4 work will build role-based authorization
on top of these authentication dependencies.
"""

import jwt

from fastapi import (
    Depends,
    HTTPException,
    status,
)

from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.security import decode_access_token

from collections.abc import Callable


# =========================================================
# OAUTH2 BEARER TOKEN EXTRACTOR
# =========================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
)


# =========================================================
# STANDARD AUTHENTICATION ERROR
# =========================================================

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={
        "WWW-Authenticate": "Bearer",
    },
)


# =========================================================
# GET CURRENT AUTHENTICATED USER
# =========================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate the Bearer token and return the authenticated
    SQLAlchemy User object.

    Authentication flow:

        Authorization header
                ↓
        OAuth2PasswordBearer
                ↓
        raw JWT
                ↓
        decode_access_token()
                ↓
        extract "sub"
                ↓
        convert subject to user ID
                ↓
        PostgreSQL lookup
                ↓
        User object

    Any authentication failure results in HTTP 401.
    """

    # -----------------------------------------------------
    # DECODE AND VALIDATE JWT
    # -----------------------------------------------------

    try:
        payload = decode_access_token(
            token
        )

        # JWT "sub" is the standard subject claim.
        #
        # During login we stored:
        #
        #     subject=str(record.id)
        #
        # Therefore:
        #
        #     sub = "1"
        #
        # means the token belongs to user ID 1.

        subject = payload.get("sub")

        if subject is None:
            raise credentials_exception

        # Convert the JWT subject back to our integer
        # PostgreSQL primary key.

        user_id = int(subject)

    except (
        jwt.InvalidTokenError,
        ValueError,
        TypeError,
    ):
        raise credentials_exception


    # -----------------------------------------------------
    # FIND USER IN POSTGRESQL
    # -----------------------------------------------------

    record = db.get(
        User,
        user_id,
    )

    if record is None:
        raise credentials_exception


    # -----------------------------------------------------
    # RETURN AUTHENTICATED USER
    # -----------------------------------------------------

    return record

# =========================================================
# REQUIRE ROLE
# =========================================================

def require_role(
    *allowed_roles: str,
) -> Callable:
    """
    Create a reusable FastAPI authorization dependency.

    The returned dependency:

        1. authenticates the caller
        2. obtains the current User
        3. checks the user's role
        4. returns the User when authorized
        5. raises HTTP 403 when unauthorized

    Example:

        current_user: User = Depends(
            require_role("ADMIN")
        )

    Future example:

        current_user: User = Depends(
            require_role("OWNER", "ADMIN")
        )
    """

    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        """
        Check whether the authenticated user's role
        is one of the allowed roles.
        """

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return role_checker