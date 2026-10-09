
"""
dependencies.py

PROJECT 5 — VEHICLE MICROSERVICE

Purpose:
    Authenticate requests using JWT access tokens issued
    by the Project 4 User Service.

Responsibilities:
    1. Read JWT verification configuration.
    2. Extract Bearer tokens from HTTP requests.
    3. Verify JWT signature and expiration.
    4. Validate the authenticated user ID and role.
    5. Build a trusted CurrentIdentity object.
    6. Provide reusable role-based authorization.
    7. Enforce vehicle ownership permissions.

Authentication:
    Determines WHO is making the request.

Authorization:
    Determines WHAT the authenticated user may do.

Important:
    The Vehicle Service does not connect directly to
    the User Service database.

    It validates a signed JWT and uses the identity
    information contained in that token.
"""

# =========================================================
# 1. IMPORTS
# =========================================================

import logging
import os

from pathlib import Path
from typing import Annotated

import jwt

from dotenv import load_dotenv

from fastapi import (
    Depends,
    HTTPException,
    status,
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from pydantic import BaseModel


# =========================================================
# 2. LOGGING
# =========================================================

# Python's logging module allows us to record useful
# diagnostic information without exposing JWT tokens
# or signing secrets in API responses.

logger = logging.getLogger(__name__)


# =========================================================
# 3. LOAD VEHICLE SERVICE ENVIRONMENT
# =========================================================

# __file__ points to:
#
# vehicle-service/app/dependencies.py
#
# parents[0] = app/
# parents[1] = vehicle-service/
#
# Therefore the expected .env location is:
#
# vehicle-service/.env

SERVICE_ROOT = Path(__file__).resolve().parents[1]

ENV_FILE = SERVICE_ROOT / ".env"

# Load local configuration.
#
# override=False preserves environment variables already
# supplied by the operating system or deployment platform.
#
# In production, environment variables should normally
# come from a secret manager or deployment configuration.

load_dotenv(
    dotenv_path=ENV_FILE,
    override=False,
)


# =========================================================
# 4. JWT CONFIGURATION
# =========================================================

# The User Service signs tokens with JWT_SECRET_KEY.
#
# For this HS256 development lab, Vehicle Service must
# use the SAME secret to verify those signatures.
#
# The two services should still use different
# DATABASE_URL values.

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

JWT_ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256",
)

# Explicitly restrict the accepted signing algorithm.
#
# Do not trust an arbitrary algorithm supplied by
# the incoming JWT header.

SUPPORTED_ALGORITHM = "HS256"


# =========================================================
# 5. BEARER TOKEN SECURITY SCHEME
# =========================================================

# Reads requests containing:
#
# Authorization: Bearer eyJhbGciOi...
#
# auto_error=False allows our dependency to return
# a consistent HTTP 401 response when credentials
# are missing.
#
# FastAPI also uses this configuration to document
# authentication in Swagger UI.

bearer_scheme = HTTPBearer(
    auto_error=False,
)


# =========================================================
# 6. AUTHENTICATED IDENTITY MODEL
# =========================================================

class CurrentIdentity(BaseModel):
    """
    Trusted identity extracted from a verified JWT.

    id:
        User ID issued by the User Service.

    role:
        RENTER, OWNER, or ADMIN.

    This model must only be created from verified claims
    when used for authorization.
    """

    id: int
    role: str


# =========================================================
# 7. STANDARD UNAUTHORIZED RESPONSE
# =========================================================

def unauthorized() -> HTTPException:
    """
    Return HTTP 401 for missing or invalid credentials.

    Do not reveal whether the token had:
        - An invalid signature.
        - An expired timestamp.
        - An invalid subject.
        - A missing role.

    Those details belong in development logs,
    not in public API responses.
    """

    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )


# =========================================================
# 8. JWT AUTHENTICATION DEPENDENCY
# =========================================================

def get_current_identity(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> CurrentIdentity:
    """
    Validate an incoming JWT and return its identity.

    Workflow:

        1. Read Authorization header.
        2. Require Bearer authentication.
        3. Verify JWT configuration.
        4. Verify signature.
        5. Verify expiration.
        6. Extract sub and role claims.
        7. Validate both claims.
        8. Return CurrentIdentity.

    Example verified JWT payload:

        {
            "sub": "267",
            "role": "OWNER",
            "exp": 1790000000
        }
    """

    # -----------------------------------------------------
    # STEP 1 — REQUIRE BEARER TOKEN
    # -----------------------------------------------------

    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
    ):
        logger.debug(
            "Authentication failed: Bearer token missing"
        )

        raise unauthorized()

    # -----------------------------------------------------
    # STEP 2 — VERIFY JWT CONFIGURATION
    # -----------------------------------------------------

    if (
        not JWT_SECRET_KEY
        or JWT_ALGORITHM != SUPPORTED_ALGORITHM
    ):
        logger.error(
            "JWT verification configuration is missing "
            "or unsupported"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT verification not configured",
        )

    # -----------------------------------------------------
    # STEP 3 — DECODE AND VERIFY JWT
    # -----------------------------------------------------

    try:
        claims = jwt.decode(
            credentials.credentials,

            # Verify using the configured local secret.
            JWT_SECRET_KEY,

            # Accept HS256 only.
            algorithms=[SUPPORTED_ALGORITHM],

            # Require these claims to exist.
            #
            # PyJWT verifies expiration automatically
            # when an exp claim is present.
            options={
                "require": [
                    "sub",
                    "exp",
                ],
                "verify_signature": True,
                "verify_exp": True,
            },
        )

    # -----------------------------------------------------
    # STEP 4 — HANDLE EXPIRED TOKEN
    # -----------------------------------------------------

    except jwt.ExpiredSignatureError as exc:
        logger.warning(
            "JWT rejected: access token expired"
        )

        raise unauthorized() from exc

    # -----------------------------------------------------
    # STEP 5 — HANDLE INVALID SIGNATURE
    # -----------------------------------------------------

    except jwt.InvalidSignatureError as exc:
        logger.warning(
            "JWT rejected: invalid signature"
        )

        raise unauthorized() from exc

    # -----------------------------------------------------
    # STEP 6 — HANDLE OTHER JWT ERRORS
    # -----------------------------------------------------

    except jwt.PyJWTError as exc:
        logger.warning(
            "JWT rejected: %s",
            type(exc).__name__,
        )

        raise unauthorized() from exc

    # -----------------------------------------------------
    # STEP 7 — VALIDATE SUBJECT CLAIM
    # -----------------------------------------------------

    # JWT sub should contain a string representing
    # the User Service's integer user ID.
    #
    # Example:
    #
    # "sub": "267"

    raw_id = claims.get("sub")

    if (
        not isinstance(raw_id, str)
        or not raw_id.isdecimal()
    ):
        logger.warning(
            "JWT rejected: invalid subject format"
        )

        raise unauthorized()

    user_id = int(raw_id)

    if user_id <= 0:
        logger.warning(
            "JWT rejected: invalid user ID"
        )

        raise unauthorized()

    # -----------------------------------------------------
    # STEP 8 — VALIDATE ROLE CLAIM
    # -----------------------------------------------------

    role = claims.get("role")

    allowed_roles = {
        "RENTER",
        "OWNER",
        "ADMIN",
    }

    if role not in allowed_roles:
        logger.warning(
            "JWT rejected: missing or unsupported role"
        )

        raise unauthorized()

    # -----------------------------------------------------
    # STEP 9 — RETURN TRUSTED IDENTITY
    # -----------------------------------------------------

    return CurrentIdentity(
        id=user_id,
        role=role,
    )


# =========================================================
# 9. REUSABLE ROLE-BASED AUTHORIZATION
# =========================================================

def require_role(*allowed_roles: str):
    """
    Create a FastAPI dependency that requires one
    or more specified roles.

    Example:

        Depends(
            require_role("OWNER", "ADMIN")
        )

    Behavior:
        - Invalid JWT -> 401
        - Valid JWT, wrong role -> 403
        - Valid JWT, allowed role -> success
    """

    def check(
        identity: Annotated[
            CurrentIdentity,
            Depends(get_current_identity),
        ],
    ) -> CurrentIdentity:

        if identity.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return identity

    return check


# =========================================================
# 10. VEHICLE OWNERSHIP AUTHORIZATION
# =========================================================

def require_vehicle_access(
    owner_id: int,
    identity: CurrentIdentity,
) -> None:
    """
    Verify permission to modify a vehicle.

    ADMIN:
        May modify any vehicle.

    OWNER:
        May modify only their own vehicle.

    RENTER:
        Cannot modify vehicles.

    This function is intended to be called after
    loading the Vehicle ORM record from PostgreSQL.
    """

    # ADMIN can manage any vehicle.
    if identity.role == "ADMIN":
        return

    # OWNER can manage only their own vehicles.
    if (
        identity.role == "OWNER"
        and identity.id == owner_id
    ):
        return

    # Reject all other cases.
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to modify this vehicle",
    )
