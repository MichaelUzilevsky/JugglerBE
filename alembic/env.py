from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import AsyncEngine
from alembic import context
import asyncio

from app import config
from app.db.sqlalchemy.base import Base
from app.db.sqlalchemy.models import *

# Alembic Config object
configuration = context.config

# Logging setup
if configuration.config_file_name is not None:
    fileConfig(configuration.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


postgresql_config = config.get_value("postgresql")
url = (
    f"postgresql+asyncpg://"
    f"{postgresql_config['user']}:{postgresql_config['password']}@"
    f"{postgresql_config['host']}:{postgresql_config['port']}/"
    f"{postgresql_config['database']}"
)

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no DB connection)."""

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Run migrations given a DB connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' (async) mode."""
    connectable = engine_from_config(
        configuration.get_section(configuration.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    if isinstance(connectable, AsyncEngine):
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
    else:
        with connectable.connect() as connection:
            do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
