"""Pydantic schemas: validate input and expose only approved output fields."""
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class VehicleFields(BaseModel):
    make: str = Field(min_length=1, max_length=50)
    model: str = Field(min_length=1, max_length=50)
    year: int = Field(ge=1980, le=2100)
    color: str | None = Field(default=None, max_length=30)
    daily_rate: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=2, max_length=2)

    @field_validator("state")
    @classmethod
    def normalize_state(cls, value: str) -> str:
        """Keep US state codes consistent in the database."""
        if not value.isalpha():
            raise ValueError("state must contain two letters")
        return value.upper()

class VehicleCreate(VehicleFields):
    """Clients cannot choose owner_id, which comes from their JWT."""
    model_config = ConfigDict(extra="forbid")

class VehicleUpdate(BaseModel):
    """All fields optional; explicitly null required columns are rejected in router."""
    model_config = ConfigDict(extra="forbid")
    make: str | None = Field(default=None, min_length=1, max_length=50)
    model: str | None = Field(default=None, min_length=1, max_length=50)
    year: int | None = Field(default=None, ge=1980, le=2100)
    color: str | None = Field(default=None, max_length=30)
    daily_rate: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    state: str | None = Field(default=None, min_length=2, max_length=2)

    @field_validator("state")
    @classmethod
    def normalize_state(cls, value: str | None) -> str | None:
        if value is not None:
            if not value.isalpha():
                raise ValueError("state must contain two letters")
            return value.upper()
        return value

class AvailabilityUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_available: bool

class VehicleResponse(VehicleFields):
    id: int
    owner_id: int
    is_available: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
