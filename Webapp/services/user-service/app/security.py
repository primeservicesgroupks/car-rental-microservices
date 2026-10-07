"""
security.py

Security utilities for the User Service.

Responsibilities:
    - Hash plaintext passwords.
    - Verify plaintext passwords against stored hashes.
    - Create signed JWT access tokens.

Passwords:
    Argon2 is used through pwdlib.

Authentication tokens:
    JWT access tokens are signed using the configured
    secret key and algorithm.
"""

import os

from datetime import datetime, timedelta, timezone

import jwt

from dotenv import load_dotenv
from pwdlib import PasswordHash


# =========================================================
# LOAD ENVIRONMENT CONFIGURATION
# =========================================================

load_dotenv()


# =========================================================
# PASSWORD HASHING CONFIGURATION
# =========================================================

password_hash = PasswordHash.recommended()


# =========================================================
# JWT CONFIGURATION
# =========================================================

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256",
)

ACCESS_TOKEN_EXPIRE_MINUTES_RAW = os.getenv(
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "30",
)


# =========================================================
# VALIDATE JWT CONFIGURATION
# =========================================================

if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY is missing"
    )


try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(
        ACCESS_TOKEN_EXPIRE_MINUTES_RAW
    )

except ValueError as exc:
    raise RuntimeError(
        "ACCESS_TOKEN_EXPIRE_MINUTES must be an integer"
    ) from exc


if ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
    raise RuntimeError(
        "ACCESS_TOKEN_EXPIRE_MINUTES must be greater than 0"
    )


# =========================================================
# HASH PASSWORD
# =========================================================

def hash_password(
    plain_password: str,
) -> str:
    """
    Convert a plaintext password into a secure
    password hash.

    The plaintext password must never be stored.
    """

    return password_hash.hash(
        plain_password
    )


# =========================================================
# VERIFY PASSWORD
# =========================================================

def verify_password(
    plain_password: str,
    stored_password_hash: str,
) -> bool:
    """
    Verify a plaintext password against the
    password hash stored in PostgreSQL.
    """

    return password_hash.verify(
        plain_password,
        stored_password_hash,
    )


# =========================================================
# CREATE ACCESS TOKEN
# =========================================================

def create_access_token(
    subject: str,
) -> str:
    """
    Create a signed JWT access token.

    subject:
        Identifies the authenticated user.

        We will store the user's database ID in the
        standard JWT 'sub' claim.

    Example payload:

        {
            "sub": "1",
            "iat": ...,
            "exp": ...
        }
    """

    now = datetime.now(
        timezone.utc
    )

    expires_at = now + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": subject,
        "iat": now,
        "exp": expires_at,
    }

    token = jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )

    return token

# =========================================================
# DECODE ACCESS TOKEN
# =========================================================

def decode_access_token(
    token: str,
) -> dict:
    """
    Decode and validate a JWT access token.

    PyJWT verifies:

        - the JWT signature
        - the expiration time
        - the configured signing algorithm

    If the token is invalid or expired, PyJWT raises
    an exception.

    The caller is responsible for translating those
    exceptions into the appropriate HTTP response.
    """

    payload = jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
    )

    return payload