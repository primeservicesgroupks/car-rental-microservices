"""
Alembic migration environment for the User Service.

This file tells Alembic:

1. How to connect to PostgreSQL.
2. Where DATABASE_URL comes from.
3. Which SQLAlchemy models exist.
4. Which metadata Alembic should inspect when
   generating migrations.
"""

import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from app.db import Base

# IMPORTANT:
# Import models so SQLAlchemy registers the User model
# with Base.metadata.
#
# We don't directly use "models" below, but importing it
# causes the User table definition to be registered.
from app import models  # noqa: F401


# =========================================================
# ALEMBIC CONFIGURATION
# =========================================================

config = context.config


# Configure logging using alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# =========================================================
# ENVIRONMENT VARIABLES
# =========================================================

# Load variables from .env during local development.
load_dotenv()


database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise RuntimeError(
        "DATABASE_URL environment variable is missing."
    )


# =========================================================
# DATABASE CONNECTION
# =========================================================

# Override the placeholder sqlalchemy.url in alembic.ini
# with DATABASE_URL from the environment.
#
# This prevents us from hard-coding database credentials
# into alembic.ini.

config.set_main_option(
    "sqlalchemy.url",
    database_url,
)


# =========================================================
# SQLALCHEMY METADATA
# =========================================================

# Base.metadata contains all tables registered by our
# SQLAlchemy ORM models.
#
# Alembic compares this metadata against the actual
# PostgreSQL schema when --autogenerate is used.

target_metadata = Base.metadata


# =========================================================
# OFFLINE MIGRATIONS
# =========================================================

def run_migrations_offline() -> None:
    """
    Run migrations without creating a live
    database connection.

    Primarily useful when generating SQL scripts.
    """

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# =========================================================
# ONLINE MIGRATIONS
# =========================================================

def run_migrations_online() -> None:
    """
    Run migrations using a live database connection.
    """

    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {}
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# =========================================================
# RUN CORRECT MIGRATION MODE
# =========================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()