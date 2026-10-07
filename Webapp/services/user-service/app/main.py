"""
main.py

Entry point for the Car Rental User Service.

Responsibilities:
    - Create the FastAPI application.
    - Register the User router.
    - Register the Authentication router.
    - Provide an API health check.
    - Provide a PostgreSQL connectivity health check.

Project 4 adds authentication while preserving the
functionality built during Projects 1–3.
"""

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router


# =========================================================
# CREATE FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="Car Rental User Service",
    description=(
        "User management and authentication service "
        "for the Car Rental Microservices platform."
    ),
    version="1.0.0",
)


# =========================================================
# REGISTER USER ROUTER
# =========================================================

# users_router comes from:
#
#     app/routers/users.py
#
# That file should contain:
#
#     router = APIRouter(
#         prefix="/users",
#         tags=["Users"],
#     )
#
# Example endpoints:
#
#     GET /users
#     GET /users/{user_id}
#     PUT /users/{user_id}

app.include_router(users_router)


# =========================================================
# REGISTER AUTHENTICATION ROUTER
# =========================================================

# auth_router comes from:
#
#     app/routers/auth.py
#
# That file should contain:
#
#     router = APIRouter(
#         prefix="/auth",
#         tags=["Authentication"],
#     )
#
# Current Project 4 endpoint:
#
#     POST /auth/register
#
# Coming later:
#
#     POST /auth/login
#     GET  /auth/me

app.include_router(auth_router)


# =========================================================
# API HEALTH CHECK
# GET /health
# =========================================================

@app.get(
    "/health",
    tags=["Health"],
)
def health_check():
    """
    Verify that the FastAPI application is responding.

    This confirms that the API process is alive.

    It does NOT verify PostgreSQL connectivity.
    """

    return {
        "status": "healthy",
        "service": "user-service",
    }


# =========================================================
# DATABASE HEALTH CHECK
# GET /health/db
# =========================================================

@app.get(
    "/health/db",
    tags=["Health"],
)
def database_health_check(
    db: Session = Depends(get_db),
):
    """
    Verify that the application can communicate
    with PostgreSQL.

    SELECT 1 is a lightweight database query used
    only to verify connectivity.

    It does not read or modify application data.
    """

    db.execute(
        text("SELECT 1")
    )

    return {
        "status": "healthy",
        "database": "reachable",
    }