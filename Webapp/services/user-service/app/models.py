"""
models.py

SQLAlchemy ORM models for the User Service.

An ORM model maps a Python class to a database table.

    Python class       PostgreSQL table
    ------------       ----------------
    User        <----> users

One User object represents one row in the users table.
"""

from sqlalchemy import String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


# =========================================================
# USER DATABASE MODEL
# =========================================================

class User(Base):
    """
    Represents the users table in PostgreSQL.

    Each instance of User represents one database row.
    """

    # PostgreSQL table name.
    __tablename__ = "users"

    # -----------------------------------------------------
    # PRIMARY KEY
    # -----------------------------------------------------

    # SQLAlchemy/PostgreSQL generates the integer ID.
    #
    # Example:
    #   1
    #   2
    #   3

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    # -----------------------------------------------------
    # FIRST NAME
    # -----------------------------------------------------

    first_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # -----------------------------------------------------
    # LAST NAME
    # -----------------------------------------------------

    last_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # -----------------------------------------------------
    # EMAIL
    # -----------------------------------------------------

    email: Mapped[str] = mapped_column(
        String(320),

        # Database must always have an email.
        nullable=False,

        # Prevent duplicate email values.
        unique=True,

        # Create an index because email will commonly
        # be searched during login/user lookup.
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
    String(255),
    nullable=False,
)

    # -----------------------------------------------------
    # PHONE
    # -----------------------------------------------------

    # Phone is optional.
    #
    # Store phone numbers as strings rather than integers
    # because phone numbers are identifiers, not values
    # we perform arithmetic on.

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    # -----------------------------------------------------
    # ROLE
    # -----------------------------------------------------

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,

        # Python/SQLAlchemy-side default.
        default="RENTER",

        # PostgreSQL-side default.
        server_default=text("'RENTER'"),
    )