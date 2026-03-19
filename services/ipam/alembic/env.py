import asyncio
from logging.config import fileConfig

from alembic import context
from ipam.infrastructure.models import IPAMBase
from sqlalchemy import MetaData, pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from shared.event.models import EventStoreBase

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Merge metadata from both IPAM read models and event store tables
combined_metadata = MetaData()
for metadata in (IPAMBase.metadata, EventStoreBase.metadata):
    for table in metadata.tables.values():
        table.tometadata(combined_metadata)

target_metadata = combined_metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
