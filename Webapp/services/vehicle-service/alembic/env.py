"""Alembic environment: read Vehicle Service URL and compare Vehicle metadata."""
import os
from logging.config import fileConfig
from pathlib import Path
from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from app.db import Base
from app import models  # noqa: F401; import registers Vehicle on Base.metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Explicit path makes CLI execution independent of current shell directory.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL is missing in vehicle-service/.env")
# ConfigParser uses percent for interpolation; escape percent signs in URLs.
config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Generate SQL without opening a live database connection."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Apply migrations using a live PostgreSQL connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
