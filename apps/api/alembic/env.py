"""
Alembic environment configuration.
"""

import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool, text, Enum as SQLAEnum
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel

from alembic import context

# Import all models to ensure they are registered with SQLModel metadata
from src.models import *  # noqa: F403, F401

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = SQLModel.metadata


def render_item(type_, obj, autogen_context):
    """Custom rendering for Enums to use values not names."""
    if type_ == "type" and isinstance(obj, SQLAEnum):
        # Get the Python enum class
        enum_class = obj.enum_class
        if enum_class:
            # Use enum VALUES not names  
            values = [e.value for e in enum_class]
            return f"sa.Enum({', '.join(repr(v) for v in values)}, name='{obj.name}')"
    return False

# Override database URL from environment variable if available
database_url = os.getenv("SQLALCHEMY_DATABASE_URL") or os.getenv("DATABASE_URL")
if database_url:
    # Convert to async URL if needed
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        render_as_batch=False,
        render_item=render_item,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with a database connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        render_as_batch=False,
        render_item=render_item,
    )

    with context.begin_transaction():
        # Create PostgreSQL extensions as specified in Story 1.2 Task 5
        connection.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        connection.execute(text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))

        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode."""
    configuration = config.get_section(config.config_ini_section, {})

    # Ensure we're using the async driver
    if "sqlalchemy.url" in configuration:
        url = configuration["sqlalchemy.url"]
        if not url.startswith("postgresql+asyncpg://"):
            if url.startswith("postgresql://"):
                configuration["sqlalchemy.url"] = url.replace(
                    "postgresql://", "postgresql+asyncpg://", 1
                )

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
