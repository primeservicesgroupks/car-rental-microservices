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