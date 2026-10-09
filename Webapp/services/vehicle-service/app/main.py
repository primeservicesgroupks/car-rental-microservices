
"""
main.py

Project 5 — Vehicle Microservice

Entry point for the Car Rental Vehicle Service.

Responsibilities:
    1. Create the FastAPI application.
    2. Register the Vehicle API router.
    3. Provide an application health check.
    4. Provide a PostgreSQL connectivity health check.
    5. Expose API documentation through Swagger UI.

Architecture:

    Client / Swagger
          |
          v
    FastAPI Application
          |
          +---- /health
          |
          +---- /health/db
          |
          +---- /vehicles
          |        |
          |        v
          |    Vehicle Router
          |        |
          |        v
          |    SQLAlchemy
          |        |
          |        v
          |    PostgreSQL
          |
          +---- JWT Authentication
                   |
                   v
              RBAC / Ownership

The Vehicle Service runs independently of the User Service.

User Service:
    http://127.0.0.1:8001

Vehicle Service:
    http://127.0.0.1:8002
"""

# =========================================================
# IMPORTS
# =========================================================

# FastAPI:
#   Creates the web application.
#
# Depends:
#   Injects dependencies into route functions.
from fastapi import Depends, FastAPI

# SQLAlchemy text:
#   Allows execution of raw SQL statements such as SELECT 1.
from sqlalchemy import text

# SQLAlchemy Session:
#   Represents a database session.
from sqlalchemy.orm import Session

# Database dependency:
#   Creates and closes PostgreSQL sessions per request.
from app.db import get_db

# Vehicle API router:
#   Contains endpoints for vehicle creation, browsing,
#   updating, and managing availability.
from app.routers.vehicles import router as vehicles_router


# =========================================================
# CREATE FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="Car Rental Vehicle Service",

    description=(
        "Project 5 Vehicle Microservice. "
        "Provides vehicle listing management, "
        "PostgreSQL persistence, JWT authentication, "
        "and role-based authorization."
    ),

    version="1.0.0",
)


# =========================================================
# REGISTER VEHICLE ROUTER
# =========================================================

# The Vehicle router is defined in:
#
#     app/routers/vehicles.py
#
# That file should contain:
#
#     router = APIRouter(
#         prefix="/vehicles",
#         tags=["Vehicles"],
#     )
#
# Registering it exposes endpoints such as:
#
#     GET   /vehicles
#     POST  /vehicles
#     GET   /vehicles/mine
#     GET   /vehicles/{vehicle_id}
#     PUT   /vehicles/{vehicle_id}
#     PATCH /vehicles/{vehicle_id}/availability
#
# IMPORTANT:
# Register the router after creating the FastAPI app.
#
# Do not create another FastAPI instance afterward,
# because that would discard the registered routes.

app.include_router(vehicles_router)


# =========================================================
# APPLICATION HEALTH CHECK
# =========================================================

@app.get(
    "/health",
    tags=["Health"],
)
def health_check():
    """
    Check whether the Vehicle Service API is running.

    This is a liveness check.

    It verifies:
        - FastAPI is running.
        - The application can receive HTTP requests.
        - The application can return HTTP responses.

    It does NOT verify PostgreSQL connectivity.

    Endpoint:
        GET /health

    Expected HTTP status:
        200 OK
    """

    return {
        "status": "healthy",
        "service": "vehicle-service",
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
    Check whether PostgreSQL is reachable.

    This is a database connectivity check.

    FastAPI calls get_db() to obtain a SQLAlchemy session.

    The SELECT 1 query is intentionally lightweight.
    It does not read or modify application records.

    Endpoint:
        GET /health/db

    Expected HTTP status:
        200 OK when PostgreSQL is reachable.

    If PostgreSQL is unavailable, the query raises
    a database exception. The API will report a failure
    unless an appropriate exception handler is configured.
    """

    # Execute a simple SQL query against PostgreSQL.
    db.execute(
        text("SELECT 1")
    )

    # Return success only after the query completes.
    return {
        "status": "healthy",
        "database": "reachable",
    }
