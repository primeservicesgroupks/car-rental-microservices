"""
auth.py

Authentication routes for the Car Rental User Service.

Project 4 introduces authentication and authorization.

Current endpoint:
    POST /auth/register
        Register a new RENTER or OWNER account.

Coming next:
    POST /auth/login
        Authenticate a user and issue a JWT access token.

    GET /auth/me
        Return information about the currently
        authenticated user.

Security rules:
    - Passwords are never stored as plaintext.
    - Passwords are hashed before database storage.
    - Password hashes are never returned by the API.
    - ADMIN accounts cannot be created through
      public registration.
"""

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
# ROUTER CONFIGURATION
# =========================================================

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# =========================================================
# REGISTER USER
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
    Register a new user.

    Registration flow:

        HTTP request
            ↓
        Pydantic validation
            ↓
        Validate requested role
            ↓
        Normalize email
            ↓
        Check duplicate email
            ↓
        Hash plaintext password
            ↓
        Create SQLAlchemy User
            ↓
        Save to PostgreSQL
            ↓
        Return safe UserResponse

    The plaintext password is never stored.

    The password hash is stored in PostgreSQL but
    is never included in UserResponse.
    """


    # =====================================================
    # SECURITY CHECK: BLOCK PUBLIC ADMIN REGISTRATION
    # =====================================================

    # A public user must never be able to create their
    # own ADMIN account simply by submitting:
    #
    #     "role": "ADMIN"
    #
    # Administrative accounts should eventually be
    # provisioned through a trusted administrative process.

    if registration.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "ADMIN accounts cannot be created "
                "through public registration"
            ),
        )


    # =====================================================
    # NORMALIZE EMAIL ADDRESS
    # =====================================================

    # Convert the validated EmailStr into a regular string.
    #
    # strip()
    #     Removes accidental leading/trailing whitespace.
    #
    # lower()
    #     Makes our email comparison case-insensitive.
    #
    # Example:
    #
    #     Ade.Project4@Example.com
    #
    # becomes:
    #
    #     ade.project4@example.com

    email = str(
        registration.email
    ).strip().lower()


    # =====================================================
    # CHECK FOR DUPLICATE EMAIL
    # =====================================================

    # Query PostgreSQL for an existing account using
    # the normalized email address.

    existing_user = db.scalar(
        select(User).where(
            User.email == email
        )
    )


    # If the email already exists, registration should
    # stop before hashing or attempting an INSERT.

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )


    # =====================================================
    # HASH THE PASSWORD
    # =====================================================

    # registration.password contains the plaintext password.
    #
    # We NEVER put that value directly into PostgreSQL.
    #
    # security.py converts it into an Argon2 password hash.

    hashed_password = hash_password(
        registration.password
    )


    # =====================================================
    # CREATE SQLALCHEMY USER OBJECT
    # =====================================================

    # Build the ORM object that will eventually become
    # a row in the PostgreSQL users table.
    #
    # Notice:
    #
    #     password_hash=hashed_password
    #
    # NOT:
    #
    #     password=registration.password

    record = User(
        first_name=registration.first_name,
        last_name=registration.last_name,
        email=email,
        phone=registration.phone,
        role=registration.role.value,
        password_hash=hashed_password,
    )


    # =====================================================
    # ADD USER TO SQLALCHEMY SESSION
    # =====================================================

    # add() stages the new object for insertion.
    #
    # It does NOT permanently save the record until
    # db.commit() succeeds.

    db.add(record)


    # =====================================================
    # COMMIT USER TO POSTGRESQL
    # =====================================================

    try:
        db.commit()

    except IntegrityError:

        # -------------------------------------------------
        # ROLLBACK FAILED TRANSACTION
        # -------------------------------------------------

        # If PostgreSQL rejects the INSERT, the SQLAlchemy
        # session must be rolled back before it can safely
        # be used again.

        db.rollback()


        # -------------------------------------------------
        # DATABASE-LEVEL DUPLICATE PROTECTION
        # -------------------------------------------------

        # We already checked for duplicate email above.
        #
        # However, two requests could theoretically arrive
        # at almost exactly the same time:
        #
        # Request A:
        #     SELECT email -> not found
        #
        # Request B:
        #     SELECT email -> not found
        #
        # Both then attempt INSERT.
        #
        # PostgreSQL's UNIQUE constraint is therefore our
        # final protection against duplicate emails.

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )


    # =====================================================
    # REFRESH DATABASE-GENERATED VALUES
    # =====================================================

    # PostgreSQL generates values such as the primary-key ID.
    #
    # refresh() reloads the record from PostgreSQL so our
    # Python object contains those database-generated values.

    db.refresh(record)


    # =====================================================
    # RETURN SAFE USER RESPONSE
    # =====================================================

    # FastAPI converts this SQLAlchemy object using:
    #
    #     response_model=UserResponse
    #
    # UserResponse deliberately excludes:
    #
    #     password
    #     password_hash
    #
    # Therefore neither value is exposed to the client.

    return record

# =========================================================
# LOGIN
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
    Authenticate a user and return a JWT access token.

    Authentication flow:

        validate request
            ↓
        normalize email
            ↓
        find user
            ↓
        verify password
            ↓
        create JWT
            ↓
        return access token
    """

    # -----------------------------------------------------
    # NORMALIZE EMAIL
    # -----------------------------------------------------

    email = str(
        credentials.email
    ).strip().lower()


    # -----------------------------------------------------
    # FIND USER
    # -----------------------------------------------------

    record = db.scalar(
        select(User).where(
            User.email == email
        )
    )


    # -----------------------------------------------------
    # INVALID EMAIL
    # -----------------------------------------------------

    # We deliberately use the same error message for:
    #
    #     unknown email
    #     wrong password
    #
    # This avoids unnecessarily revealing whether a
    # particular email address has an account.

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )


    # -----------------------------------------------------
    # VERIFY PASSWORD
    # -----------------------------------------------------

    if not verify_password(
        credentials.password,
        record.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )


    # -----------------------------------------------------
    # CREATE JWT
    # -----------------------------------------------------

    access_token = create_access_token(
        subject=str(record.id)
    )


    # -----------------------------------------------------
    # RETURN TOKEN
    # -----------------------------------------------------

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )

# =========================================================
# CURRENT AUTHENTICATED USER
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
    Return the currently authenticated user.

    The client must provide:

        Authorization: Bearer <access_token>

    get_current_user() validates the JWT and loads
    the corresponding User from PostgreSQL.

    UserResponse ensures sensitive fields such as
    password_hash are never returned.
    """

    return current_user