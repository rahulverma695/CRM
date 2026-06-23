import asyncio
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
from app.config import settings
from app.core.models import Base
import app.core.models  # noqa: F401  ensures all models are imported
import app.crm.models   # noqa: F401  registers CRM models with Base.metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

import os as _os
MIGRATION_URL = (
    _os.environ.get("MIGRATION_DATABASE_URL")
    or settings.migration_database_url
    or settings.database_url
)


def run_migrations_offline() -> None:
    context.configure(
        url=MIGRATION_URL, target_metadata=target_metadata,
        literal_binds=True, dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = create_async_engine(MIGRATION_URL)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
