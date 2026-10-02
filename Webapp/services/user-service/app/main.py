"""
main.py

Entry point for the Car Rental User Service.

This file:
- Creates the FastAPI application
- Registers the User router
- Provides a health-check endpoint

Run the service from the user-service directory with:

    uvicorn app.main:app --reload --port 8001
"""

from fastapi import FastAPI

from app.routers.users import router as users_router


# =========================================================
# CREATE FASTAPI APPLICATION
# =========================================================

# FastAPI() creates the web application.
#
# The information below is automatically displayed
# in the Swagger/OpenAPI documentation.

app = FastAPI(
    title="Car Rental User Service",
    description="Manages users for the car rental platform.",
    version="1.0.0",
)


# =========================================================
# REGISTER ROUTERS
# =========================================================

# Import and register the User router.
#
# users_router already has:
#
#     prefix="/users"
#
# Therefore its endpoints become:
#
#     POST /users
#     GET  /users
#     GET  /users/{user_id}
#     PUT  /users/{user_id}

app.include_router(users_router)


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get(
    "/health",
    tags=["Health"],
)
def health_check():
    """
    Verify that the User Service is running.

    A successful request returns HTTP 200 automatically.
    """

    return {
        "status": "healthy",
        "service": "user-service",
    }