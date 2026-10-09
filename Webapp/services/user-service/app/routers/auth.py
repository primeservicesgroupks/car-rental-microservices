
"""
auth.py

PROJECT 4 — USER SERVICE AUTHENTICATION

Purpose:
    Handle user registration, login, and authenticated
    identity retrieval.

Endpoints:
    POST /auth/register
        Register a RENTER or OWNER account.

    POST /auth/login
        Verify credentials and issue a signed JWT.

    GET /auth/me
        Return the authenticated user's information.

Project 5 integration:
    JWT tokens must contain:
        sub  = authenticated user's database ID
        role = authenticated user's database role
        exp  = token expiration timestamp

Security:
    - Public ADMIN registration is prohibited.
    - Passwords are hashed using Argon2.
    - Password hashes are never returned by the API.
    - Login returns the same error for unknown emails
      and incorrect passwords.
    - The JWT role comes from PostgreSQL, never from
      client-supplied login data.
"""

# =========================================================
# 1. IMPORTS
# =========================================================

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
    LoginRequest,
    TokenResponse,
    UserRegister,
    UserResponse,
    UserRole,
)

from app.security import (
    create_access_token,
    hash_password,
    verify_password,
)


# =========================================================
# 2. ROUTER CONFIGURATION
# =========================================================

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# =========================================================
# 3. REGISTER USER
# POST /auth/register
# =========================================================

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    registration: UserRegister,
    db: Session = Depends(get_db),
):
    """
    Register a new RENTER or OWNER.

    Workflow:
        1. Validate requested role.
        2. Normalize email.
        3. Check duplicate email.
        4. Hash password.
        5. Insert user into PostgreSQL.
        6. Return safe user information.

    Public users cannot register as ADMIN.
    """

    # -----------------------------------------------------
    # STEP 1 — BLOCK PUBLIC ADMIN REGISTRATION
    # -----------------------------------------------------

    if registration.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "ADMIN accounts cannot be created "
                "through public registration"
            ),
        )

    # -----------------------------------------------------
    # STEP 2 — NORMALIZE EMAIL
    # -----------------------------------------------------

    # Example:
    #   Owner@Example.com -> owner@example.com

    email = str(registration.email).strip().lower()

    # -----------------------------------------------------
    # STEP 3 — CHECK DUPLICATE EMAIL
    # -----------------------------------------------------

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )

    # -----------------------------------------------------
    # STEP 4 — HASH PASSWORD
    # -----------------------------------------------------

    # Never store registration.password directly.
    # Argon2 generates a salted password hash.

    hashed_password = hash_password(
        registration.password
    )

    # -----------------------------------------------------
    # STEP 5 — CREATE DATABASE RECORD
    # -----------------------------------------------------

    record = User(
        first_name=registration.first_name,
        last_name=registration.last_name,
        email=email,
        phone=registration.phone,
        role=registration.role.value,
        password_hash=hashed_password,
    )

    db.add(record)

    # -----------------------------------------------------
    # STEP 6 — COMMIT TRANSACTION
    # -----------------------------------------------------

    try:
        db.commit()

    except IntegrityError as exc:
        db.rollback()

        # The database UNIQUE constraint protects
        # against concurrent duplicate registrations.
        #
        # This response assumes the only expected
        # integrity conflict here is duplicate email.

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        ) from exc

    # -----------------------------------------------------
    # STEP 7 — REFRESH DATABASE VALUES
    # -----------------------------------------------------

    db.refresh(record)

    # -----------------------------------------------------
    # STEP 8 — RETURN SAFE RESPONSE
    # -----------------------------------------------------

    # UserResponse excludes password_hash.

    return record


# =========================================================
# 4. LOGIN
# POST /auth/login
# =========================================================

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate a user and issue a JWT.

    Workflow:
        1. Normalize email.
        2. Find user in PostgreSQL.
        3. Verify password.
        4. Read the user's trusted database role.
        5. Generate a signed JWT.
        6. Return access token.

    IMPORTANT:
        The role must come from the authenticated
        User database record.

        Never allow the login request to choose
        or override the user's role.
    """

    # -----------------------------------------------------
    # STEP 1 — NORMALIZE EMAIL
    # -----------------------------------------------------

    email = str(credentials.email).strip().lower()

    # -----------------------------------------------------
    # STEP 2 — FIND USER
    # -----------------------------------------------------

    record = db.scalar(
        select(User).where(User.email == email)
    )

    # -----------------------------------------------------
    # STEP 3 — VALIDATE CREDENTIALS
    # -----------------------------------------------------

    # Use the same public error for unknown users
    # and incorrect passwords.

    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    if record is None:
        raise invalid_credentials

    if not verify_password(
        credentials.password,
        record.password_hash,
    ):
        raise invalid_credentials

    # -----------------------------------------------------
    # STEP 4 — READ TRUSTED USER ROLE
    # -----------------------------------------------------

    # The SQLAlchemy User model stores the role as:
    #
    #   RENTER
    #   OWNER
    #   ADMIN
    #
    # The Vehicle Service uses this claim for RBAC.

    role = record.role

    if role not in {
        UserRole.RENTER.value,
        UserRole.OWNER.value,
        UserRole.ADMIN.value,
    }:
        # An unexpected database role is a server-side
        # identity configuration problem.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User role configuration is invalid",
        )

    # -----------------------------------------------------
    # STEP 5 — GENERATE JWT
    # -----------------------------------------------------

    # CRITICAL PROJECT 5 INTEGRATION UPDATE:
    #
    # Previously:
    #
    # create_access_token(subject=str(record.id))
    #
    # Now include the role from PostgreSQL.
    #
    # security.py must support the role argument
    # and place it in the signed JWT payload.

    access_token = create_access_token(
        subject=str(record.id),
        role=role,
    )

    # -----------------------------------------------------
    # STEP 6 — RETURN TOKEN
    # -----------------------------------------------------

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )


# =========================================================
# 5. AUTHENTICATED USER
# GET /auth/me
# =========================================================

@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def get_authenticated_user(
    current_user: User = Depends(get_current_user),
):
    """
    Return the authenticated user's information.

    Requires:
        Authorization: Bearer <access_token>

    get_current_user():
        - Validates JWT signature.
        - Validates token expiration.
        - Extracts the user ID.
        - Loads the user from PostgreSQL.

    UserResponse prevents password hashes
    from being returned.
    """

    return current_user
