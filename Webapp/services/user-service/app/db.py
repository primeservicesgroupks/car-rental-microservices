"""
db.py

Database configuration for the User Service.

Responsibilities:
- Load DATABASE_URL from the local environment.
- Create the SQLAlchemy database engine.
- Create database sessions.
- Define the shared SQLAlchemy Base class.
- Provide one database session per FastAPI request.
"""

import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Session,
    sessionmaker,
)


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

# During local development, python-dotenv loads values
# from the .env file.
#
# Example:
#
# DATABASE_URL=postgresql+psycopg://...
#
# In a production environment, DATABASE_URL would normally
# come from the deployment environment or a secrets system.

load_dotenv()


# =========================================================
# DATABASE URL
# =========================================================

database_url = os.getenv("DATABASE_URL")

# Fail immediately during application startup if the
# database configuration is missing.
#
# This is better than allowing the application to start
# with an invalid database configuration.

if not database_url:
    raise RuntimeError(
        "DATABASE_URL environment variable is missing."
    )


# =========================================================
# SQLALCHEMY ENGINE
# =========================================================

# The engine manages connections between SQLAlchemy
# and PostgreSQL.
#
# pool_pre_ping=True:
# SQLAlchemy checks a pooled connection before using it.
# This helps detect stale/broken database connections.

engine = create_engine(
    database_url,
    pool_pre_ping=True,
)


# =========================================================
# SESSION FACTORY
# =========================================================

# SessionLocal is NOT an active database session.
#
# It is a factory used to CREATE database sessions.
#
# Each FastAPI request will receive its own Session.

SessionLocal = sessionmaker(
    bind=engine,

    # Keep ORM object attributes available after commit.
    expire_on_commit=False,
)


# =========================================================
# DECLARATIVE BASE
# =========================================================

# All SQLAlchemy ORM models will inherit from Base.
#
# Example:
#
# class User(Base):
#     __tablename__ = "users"

class Base(DeclarativeBase):
    pass


# =========================================================
# FASTAPI DATABASE DEPENDENCY
# =========================================================

def get_db() -> Generator[Session, None, None]:
    """
    Provide one SQLAlchemy Session per FastAPI request.

    FastAPI will:
        1. Create the session.
        2. Give it to the endpoint.
        3. Execute the endpoint.
        4. Return here afterward.
        5. Close the session.

    The finally block ensures that the connection is
    returned to SQLAlchemy's connection pool even when
    an endpoint raises an exception.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()