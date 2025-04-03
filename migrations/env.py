import logging
import os
import sys
from logging.config import fileConfig
from typing import TYPE_CHECKING

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

# Añadir el directorio app al path
sys.path.append(os.getcwd())

# Cargar configuración desde el módulo app
from app.config import settings
from app.database.mysql import Base
from app.models.user import User, UserRole, UserPermission
from app.models.document import Document, DocumentStatus
from app.models.shared import SharedDocument, SharePermission

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('alembic.env')

# Esto es usado por Alembic para acceder a la metadata
target_metadata = Base.metadata

def include_object(object, name, type_, reflected, compare_to):
    """Filtro para incluir/excluir objetos en las migraciones"""
    if type_ == "table" and name.startswith("tmp_"):
        return False
    return True

def run_migrations_offline() -> None:
    """Ejecuta migraciones en modo offline."""
    context.configure(
        url=settings.SQLALCHEMY_DATABASE_URI,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,  # Soporte para SQLite
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Ejecuta migraciones en modo online usando AsyncEngine."""
    connectable = AsyncEngine(
        engine_from_config(
            {"sqlalchemy.url": settings.SQLALCHEMY_DATABASE_URI},
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True
        )
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def do_run_migrations(connection: Connection) -> None:
    """Ejecuta las migraciones sincrónicamente."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    logger.info("Running migrations in offline mode")
    run_migrations_offline()
else:
    logger.info("Running migrations in online mode")
    import asyncio
    asyncio.run(run_migrations_online())