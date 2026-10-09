
"""
vehicles.py

PROJECT 5 — VEHICLE MICROSERVICE

Purpose:
    Manage vehicle listings stored in the Vehicle Service's
    independent PostgreSQL database.

API Endpoints:
    GET   /vehicles
    POST  /vehicles
    GET   /vehicles/mine
    GET   /vehicles/{vehicle_id}
    PUT   /vehicles/{vehicle_id}
    PATCH /vehicles/{vehicle_id}/availability

Authentication:
    JWT Bearer tokens issued by the User Service.

Authorization:
    RENTER:
        Browse vehicle listings.
        Cannot create or modify vehicles.

    OWNER:
        Browse vehicles.
        Create vehicle listings.
        Manage only vehicles they own.

    ADMIN:
        Browse vehicles.
        Create vehicle listings.
        Manage any vehicle.

Security:
    - The client cannot assign vehicle ownership.
    - owner_id is obtained from the validated JWT.
    - A valid JWT does not automatically grant permission
      to modify another user's vehicle.

Database:
    SQLAlchemy ORM with PostgreSQL persistence.

Project 5 enhancement:
    GET /vehicles?available_only=true

    This filters out vehicles where is_available=False.
"""

# =========================================================
# 1. IMPORTS
# =========================================================

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

# Database session dependency.
from app.db import get_db

# SQLAlchemy ORM model.
from app.models import Vehicle

# Pydantic request and response schemas.
from app.schemas import (
    AvailabilityUpdate,
    VehicleCreate,
    VehicleResponse,
    VehicleUpdate,
)

# Authentication dependencies and validated JWT identity.
from app.dependencies import (
    CurrentIdentity,
    get_current_identity,
)


# =========================================================
# 2. ROUTER CONFIGURATION
# =========================================================

router = APIRouter(
    prefix="/vehicles",
    tags=["Vehicles"],
)


# =========================================================
# 3. REUSABLE AUTHORIZATION FUNCTIONS
# =========================================================

def require_vehicle_manager(
    current_user: CurrentIdentity,
) -> None:
    """
    Require OWNER or ADMIN privileges.

    This function performs role-based authorization.

    Authentication answers:
        Who is the user?

    Authorization answers:
        What is the user allowed to do?

    A RENTER may possess a valid JWT but still cannot
    create or modify vehicle listings.
    """

    if current_user.role not in {"OWNER", "ADMIN"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="OWNER or ADMIN role required",
        )


def require_vehicle_ownership(
    vehicle: Vehicle,
    current_user: CurrentIdentity,
) -> None:
    """
    Verify permission to modify a particular vehicle.

    ADMIN:
        Can modify any vehicle.

    OWNER:
        Can modify only vehicles where:

            vehicle.owner_id == current_user.id

    RENTER:
        Cannot modify any vehicle.
    """

    # First verify that the account has a management role.
    require_vehicle_manager(current_user)

    # ADMIN accounts may manage any vehicle.
    if current_user.role == "ADMIN":
        return

    # OWNER accounts must own the requested vehicle.
    if vehicle.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this vehicle",
        )


# =========================================================
# 4. GET ALL VEHICLES
# GET /vehicles
# =========================================================

@router.get(
    "",
    response_model=list[VehicleResponse],
    status_code=status.HTTP_200_OK,
)
def list_vehicles(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of vehicles to return",
    ),

    offset: int = Query(
        default=0,
        ge=0,
        description="Number of matching vehicles to skip",
    ),

    available_only: bool = Query(
        default=False,
        description="Return only vehicles marked available",
    ),

    db: Session = Depends(get_db),
):
    """
    Return vehicle listings.

    This endpoint is PUBLIC.
    No JWT is required.

    Query parameters:

        limit:
            Maximum number of matching records returned.
            Default = 20
            Maximum = 100

        offset:
            Number of matching records skipped.
            Default = 0

        available_only:
            False:
                Return all vehicles.

            True:
                Return only vehicles where
                is_available=True.

    Examples:

        GET /vehicles

        GET /vehicles?available_only=true

        GET /vehicles?available_only=false

        GET /vehicles?limit=10&offset=0

        GET /vehicles?available_only=true&limit=5
    """

    # -----------------------------------------------------
    # START SQL QUERY
    # -----------------------------------------------------

    # SQL equivalent:
    #
    # SELECT *
    # FROM vehicles;

    statement = select(Vehicle)

    # -----------------------------------------------------
    # OPTIONAL AVAILABILITY FILTER
    # -----------------------------------------------------

    # Apply the WHERE condition only when requested.
    #
    # SQL equivalent:
    #
    # SELECT *
    # FROM vehicles
    # WHERE is_available = TRUE;

    if available_only:
        statement = statement.where(
            Vehicle.is_available.is_(True)
        )

    # -----------------------------------------------------
    # ORDERING AND PAGINATION
    # -----------------------------------------------------

    # Sorting by ID makes pagination deterministic.
    #
    # Filtering occurs before OFFSET and LIMIT.
    #
    # SQL equivalent:
    #
    # ORDER BY id
    # LIMIT 20 OFFSET 0;

    statement = (
        statement
        .order_by(Vehicle.id)
        .offset(offset)
        .limit(limit)
    )

    # -----------------------------------------------------
    # EXECUTE QUERY
    # -----------------------------------------------------

    # scalars() extracts Vehicle ORM objects.
    #
    # FastAPI uses VehicleResponse to serialize each
    # record into JSON.

    return db.scalars(statement).all()


# =========================================================
# 5. CREATE VEHICLE
# POST /vehicles
# =========================================================

@router.post(
    "",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_vehicle(
    vehicle: VehicleCreate,

    db: Session = Depends(get_db),

    current_user: CurrentIdentity = Depends(
        get_current_identity
    ),
):
    """
    Create a vehicle listing.

    Authentication:
        Valid JWT required.

    Authorization:
        OWNER or ADMIN.

    Important:
        The client does not choose owner_id.

        owner_id comes from the authenticated identity.
    """

    # Reject users without OWNER or ADMIN privileges.
    require_vehicle_manager(current_user)

    # Convert the validated Pydantic schema into a dict.
    #
    # Example:
    #
    # {
    #     "make": "Toyota",
    #     "model": "Camry",
    #     "year": 2012,
    #     "daily_rate": Decimal("45.00"),
    #     ...
    # }

    vehicle_data = vehicle.model_dump()

    # Defense in depth:
    # Do not accept ownership from request data.
    vehicle_data.pop("owner_id", None)

    # Build the SQLAlchemy ORM record.
    record = Vehicle(
        **vehicle_data,
        owner_id=current_user.id,
    )

    # Stage the new vehicle for insertion.
    db.add(record)

    try:
        # Persist the vehicle in PostgreSQL.
        db.commit()

    except Exception:
        # A failed database transaction must be rolled
        # back before the session can be reused.
        db.rollback()
        raise

    # Reload database-generated fields:
    #
    # id
    # created_at
    # database defaults
    db.refresh(record)

    return record


# =========================================================
# 6. LIST MY VEHICLES
# GET /vehicles/mine
# =========================================================

# IMPORTANT:
# This fixed path must be registered before
# /vehicles/{vehicle_id}.
#
# Otherwise, "mine" may be interpreted as a vehicle ID.

@router.get(
    "/mine",
    response_model=list[VehicleResponse],
    status_code=status.HTTP_200_OK,
)
def list_my_vehicles(
    db: Session = Depends(get_db),

    current_user: CurrentIdentity = Depends(
        get_current_identity
    ),
):
    """
    Return listings owned by the authenticated user.

    OWNER:
        Sees their own vehicles.

    ADMIN:
        Sees vehicles owned by the ADMIN account itself.

    RENTER:
        Receives HTTP 403.

    Note:
        ADMIN's ability to modify any vehicle does not
        mean /mine returns every vehicle in the system.
    """

    require_vehicle_manager(current_user)

    # SQL equivalent:
    #
    # SELECT *
    # FROM vehicles
    # WHERE owner_id = <authenticated_user_id>
    # ORDER BY id;

    statement = (
        select(Vehicle)
        .where(
            Vehicle.owner_id == current_user.id
        )
        .order_by(Vehicle.id)
    )

    return db.scalars(statement).all()


# =========================================================
# 7. GET ONE VEHICLE
# GET /vehicles/{vehicle_id}
# =========================================================

@router.get(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    status_code=status.HTTP_200_OK,
)
def get_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve one vehicle by primary key.

    Public endpoint:
        JWT is not required.

    Possible responses:
        200: Vehicle found.
        404: Vehicle not found.
    """

    # db.get() looks up the vehicle by its primary key.
    record = db.get(
        Vehicle,
        vehicle_id,
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    return record


# =========================================================
# 8. UPDATE VEHICLE
# PUT /vehicles/{vehicle_id}
# =========================================================

@router.put(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    status_code=status.HTTP_200_OK,
)
def update_vehicle(
    vehicle_id: int,
    changes: VehicleUpdate,

    db: Session = Depends(get_db),

    current_user: CurrentIdentity = Depends(
        get_current_identity
    ),
):
    """
    Update an existing vehicle.

    OWNER:
        Can update only their own vehicles.

    ADMIN:
        Can update any vehicle.

    RENTER:
        Cannot update vehicles.

    This endpoint performs partial field updates
    even though the HTTP method is PUT.

    A future API refinement could use PATCH for
    partial updates and reserve PUT for replacement.
    """

    # -----------------------------------------------------
    # FIND EXISTING VEHICLE
    # -----------------------------------------------------

    record = db.get(
        Vehicle,
        vehicle_id,
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    # -----------------------------------------------------
    # VERIFY PERMISSION
    # -----------------------------------------------------

    require_vehicle_ownership(
        record,
        current_user,
    )

    # -----------------------------------------------------
    # EXTRACT REQUESTED CHANGES
    # -----------------------------------------------------

    # exclude_unset=True includes only fields explicitly
    # provided by the client.
    #
    # Example:
    #
    # {
    #     "daily_rate": "55.00"
    # }
    #
    # Other vehicle fields remain unchanged.

    data = changes.model_dump(
        exclude_unset=True,
    )

    # -----------------------------------------------------
    # PREVENT INVALID NULL VALUES
    # -----------------------------------------------------

    # These fields are required by the database.
    required_fields = {
        "make",
        "model",
        "year",
        "daily_rate",
        "city",
        "state",
    }

    for field in required_fields:
        if field in data and data[field] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field} cannot be null",
            )

    # -----------------------------------------------------
    # PROTECT VEHICLE OWNERSHIP
    # -----------------------------------------------------

    # Ownership cannot be transferred through this API.
    #
    # Even if owner_id is accidentally introduced into
    # VehicleUpdate later, remove it before applying data.

    data.pop("owner_id", None)

    # -----------------------------------------------------
    # APPLY ALLOWED CHANGES
    # -----------------------------------------------------

    for field, value in data.items():
        setattr(
            record,
            field,
            value,
        )

    # -----------------------------------------------------
    # SAVE CHANGES
    # -----------------------------------------------------

    try:
        db.commit()

    except Exception:
        db.rollback()
        raise

    db.refresh(record)

    return record


# =========================================================
# 9. UPDATE VEHICLE AVAILABILITY
# PATCH /vehicles/{vehicle_id}/availability
# =========================================================

@router.patch(
    "/{vehicle_id}/availability",
    response_model=VehicleResponse,
    status_code=status.HTTP_200_OK,
)
def update_vehicle_availability(
    vehicle_id: int,
    changes: AvailabilityUpdate,

    db: Session = Depends(get_db),

    current_user: CurrentIdentity = Depends(
        get_current_identity
    ),
):
    """
    Update the listing availability flag.

    Example request:

        PATCH /vehicles/1/availability

        {
            "is_available": false
        }

    OWNER:
        May update their own vehicle.

    ADMIN:
        May update any vehicle.

    RENTER:
        Cannot update availability.

    Important:
        This is a listing-level availability flag.

        Project 7 will introduce date-based booking
        availability and overlapping-booking protection.
    """

    # -----------------------------------------------------
    # FIND VEHICLE
    # -----------------------------------------------------

    record = db.get(
        Vehicle,
        vehicle_id,
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    # -----------------------------------------------------
    # VERIFY OWNERSHIP / ROLE
    # -----------------------------------------------------

    require_vehicle_ownership(
        record,
        current_user,
    )

    # -----------------------------------------------------
    # UPDATE AVAILABILITY
    # -----------------------------------------------------

    record.is_available = changes.is_available

    # -----------------------------------------------------
    # SAVE TO DATABASE
    # -----------------------------------------------------

    try:
        db.commit()

    except Exception:
        db.rollback()
        raise

    db.refresh(record)

    return record
