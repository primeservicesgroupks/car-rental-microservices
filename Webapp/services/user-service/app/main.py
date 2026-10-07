"""
main.py

Entry point for the Car Rental User Service.
"""

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.routers.users import router as users_router


# =========================================================
# CREATE FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="Car Rental User Service",
    description="Manages users for the car rental platform.",
    version="1.0.0",
)


# =========================================================
# REGISTER ROUTERS
# =========================================================

app.include_router(users_router)


# =========================================================
# API HEALTH CHECK
# =========================================================

@app.get(
    "/health",
    tags=["Health"],
)
def health_check():
    """
    Verify that the FastAPI process is responding.

    This does NOT prove PostgreSQL is available.
    """

    return {
        "status": "healthy",
        "service": "user-service",
    }


# =========================================================
# DATABASE HEALTH CHECK
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
    """

    db.execute(text("SELECT 1"))

    return {
        "status": "healthy",
        "database": "reachable",
    }