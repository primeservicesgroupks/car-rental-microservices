"""Vehicle table: only vehicle-owned data belongs in this database."""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, func, text
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Cross-service identity reference; intentionally NOT a foreign key to users.
    owner_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    make: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    color: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # Decimal avoids binary floating-point errors for currency.
    daily_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
