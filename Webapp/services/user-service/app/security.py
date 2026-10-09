
"""
security.py

PROJECT 4 — USER SERVICE SECURITY UTILITIES

Purpose:
    Provide password hashing, password verification,
    JWT token creation, and JWT token validation.

Responsibilities:
    1. Hash plaintext passwords using Argon2.
    2. Verify passwords against stored password hashes.
    3. Create signed JWT access tokens.
    4. Include authenticated user ID and role in JWTs.
    5. Verify JWT signature, expiration, and claims.

PROJECT 5 INTEGRATION:
    The Vehicle Service requires JWT tokens containing:

        sub  = User database ID
        role = RENTER, OWNER, or ADMIN
        iat  = Token creation time
        exp  = Token expiration time

IMPORTANT:
    The role must come from the authenticated User
    database record, never from the login request.

    For this local development lab, the User Service
    and Vehicle Service share the same HS256 signing key.
"""

# =========================================================
# 1. IMPORTS
# =========================================================

import os

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from pathlib import Path

import jwt

from dotenv import load_dotenv
from pwdlib import PasswordHash


# =========================================================
# 2. LOAD ENVIRONMENT CONFIGURATION
# =========================================================

# __file__ points to:
#
# user-service/app/security.py
#
# parents[0] = app/
# parents[1] = user-service/
#
# This ensures that the correct .env file is loaded
# even if Python is started from another directory.

SERVICE_ROOT = Path(__file__).resolve().parents[1]

ENV_FILE = SERVICE_ROOT / ".env"

# Existing operating-system environment variables
# take precedence over values in the local .env file.

load_dotenv(
    dotenv_path=ENV_FILE,
    override=False,
)


# =========================================================
# 3. PASSWORD HASHING CONFIGURATION
# =========================================================

# PasswordHash.recommended() currently uses Argon2.
#
# Argon2 is a password-hashing algorithm designed
# to make password cracking computationally expensive.
#
# Each password hash includes a random salt.
#
# Therefore, two users with identical passwords
# should still have different stored hashes.

password_hash = PasswordHash.recommended()


# =========================================================
# 4. JWT CONFIGURATION
# =========================================================

# JWT_SECRET_KEY:
#     Secret used to sign and verify JWT tokens.
#
# JWT_ALGORITHM:
#     Signing algorithm used by the User Service.
#
# ACCESS_TOKEN_EXPIRE_MINUTES:
#     How long a newly issued access token is valid.

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY"
)

JWT_ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256",
)

ACCESS_TOKEN_EXPIRE_MINUTES_RAW = os.getenv(
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "30",
)


# =========================================================
# 5. VALIDATE JWT CONFIGURATION
# =========================================================

# A missing secret would prevent secure signing.
#
# Fail at startup rather than accidentally creating
# unsigned or improperly signed tokens.

if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY is missing. "
        "Configure it in user-service/.env."
    )


# This lab intentionally supports HS256 only.
#
# Restricting algorithms avoids accidentally accepting
# an unexpected signing algorithm.

if JWT_ALGORITHM != "HS256":
    raise RuntimeError(
        "Unsupported JWT_ALGORITHM. "
        "Project 4 and Project 5 currently use HS256."
    )


# Convert expiration configuration to an integer.

try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(
        ACCESS_TOKEN_EXPIRE_MINUTES_RAW
    )

except ValueError as exc:
    raise RuntimeError(
        "ACCESS_TOKEN_EXPIRE_MINUTES must be an integer"
    ) from exc


# Tokens must have a positive lifetime.

if ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
    raise RuntimeError(
        "ACCESS_TOKEN_EXPIRE_MINUTES must be greater than 0"
    )


# =========================================================
# 6. SUPPORTED USER ROLES
# =========================================================

# These values must match:
#
# app/schemas.py -> UserRole
#
# and:
#
# vehicle-service/app/dependencies.py
#
# Do not accept arbitrary role strings.

ALLOWED_ROLES = {
    "RENTER",
    "OWNER",
    "ADMIN",
}


# =========================================================
# 7. HASH PASSWORD
# =========================================================

def hash_password(
    plain_password: str,
) -> str:
    """
    Convert a plaintext password into an Argon2 hash.

    Example:
        Input:
            LearningPassword123!

        Output:
            $argon2id$v=19$...

    The returned hash is stored in PostgreSQL.

    Never store the original plaintext password.
    """

    return password_hash.hash(
        plain_password
    )


# =========================================================
# 8. VERIFY PASSWORD
# =========================================================

def verify_password(
    plain_password: str,
    stored_password_hash: str,
) -> bool:
    """
    Verify a plaintext password against a stored hash.

    Returns:
        True:
            Password matches.

        False:
            Password does not match.

    The password is not decrypted.

    Argon2 verifies the supplied password against
    the salt and hash parameters stored in PostgreSQL.
    """

    return password_hash.verify(
        plain_password,
        stored_password_hash,
    )


# =========================================================
# 9. CREATE JWT ACCESS TOKEN
# =========================================================

def create_access_token(
    subject: str,
    role: str,
) -> str:
    """
    Create a signed JWT access token.

    Parameters:
        subject:
            Authenticated user's database ID.

            Example:
                "267"

        role:
            Authenticated user's database role.

            Example:
                "OWNER"

    Example JWT payload:

        {
            "sub": "267",
            "role": "OWNER",
            "iat": 1790000000,
            "exp": 1790001800
        }

    The timestamps above are illustrative.

    IMPORTANT:
        This function receives role from auth.py,
        after the user has been authenticated.

        Never trust a role supplied by the client.
    """

    # -----------------------------------------------------
    # STEP 1 — VALIDATE USER ID
    # -----------------------------------------------------

    # The standard JWT sub claim must be a string.
    #
    # Our application stores integer database IDs,
    # so we convert them to strings.

    subject = str(subject)

    if (
        not subject.isdecimal()
        or int(subject) <= 0
    ):
        raise ValueError(
            "JWT subject must be a positive user ID"
        )

    # -----------------------------------------------------
    # STEP 2 — VALIDATE ROLE
    # -----------------------------------------------------

    if role not in ALLOWED_ROLES:
        raise ValueError(
            "Invalid JWT user role"
        )

    # -----------------------------------------------------
    # STEP 3 — GET CURRENT UTC TIME
    # -----------------------------------------------------

    now = datetime.now(
        timezone.utc
    )

    # -----------------------------------------------------
    # STEP 4 — CALCULATE EXPIRATION
    # -----------------------------------------------------

    expires_at = now + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    # -----------------------------------------------------
    # STEP 5 — BUILD JWT PAYLOAD
    # -----------------------------------------------------

    payload = {
        # Authenticated user's database ID.
        "sub": subject,

        # Authenticated user's database role.
        #
        # CRITICAL FOR PROJECT 5 RBAC.
        "role": role,

        # Time when the token was issued.
        "iat": now,

        # Time when the token expires.
        "exp": expires_at,
    }

    # -----------------------------------------------------
    # STEP 6 — SIGN JWT
    # -----------------------------------------------------

    # jwt.encode() signs the token using the secret.
    #
    # The secret itself is not included in the JWT.

    token = jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )

    return token


# =========================================================
# 10. DECODE AND VALIDATE ACCESS TOKEN
# =========================================================

def decode_access_token(
    token: str,
) -> dict:
    """
    Decode and validate a signed JWT access token.

    Validations:
        1. JWT signature is valid.
        2. Signing algorithm is allowed.
        3. Token has not expired.
        4. Required claims are present.
        5. User ID is valid.
        6. Role is supported.

    Returns:
        Dictionary containing verified JWT claims.

    Raises:
        jwt.PyJWTError:
            Invalid signature, expired token, missing
            claims, or other JWT validation error.

    The FastAPI authentication dependency translates
    these exceptions into HTTP 401 responses.
    """

    # -----------------------------------------------------
    # STEP 1 — VERIFY SIGNATURE AND EXPIRATION
    # -----------------------------------------------------

    payload = jwt.decode(
        token,
        JWT_SECRET_KEY,

        # Accept only the configured algorithm.
        algorithms=[JWT_ALGORITHM],

        # Require essential identity claims.
        options={
            "require": [
                "sub",
                "role",
                "iat",
                "exp",
            ],
            "verify_signature": True,
            "verify_exp": True,
            "verify_iat": True,
        },
    )

    # -----------------------------------------------------
    # STEP 2 — VALIDATE SUBJECT
    # -----------------------------------------------------

    subject = payload.get("sub")

    if (
        not isinstance(subject, str)
        or not subject.isdecimal()
        or int(subject) <= 0
    ):
        raise jwt.InvalidTokenError(
            "Invalid JWT subject"
        )

    # -----------------------------------------------------
    # STEP 3 — VALIDATE ROLE
    # -----------------------------------------------------

    role = payload.get("role")

    if role not in ALLOWED_ROLES:
        raise jwt.InvalidTokenError(
            "Invalid JWT role"
        )

    # -----------------------------------------------------
    # STEP 4 — RETURN VERIFIED CLAIMS
    # -----------------------------------------------------

    return payload
