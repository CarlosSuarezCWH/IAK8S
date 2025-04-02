from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Añade el directorio app al path
sys.path.append(os.getcwd())

from app.config import settings
from app.database.mysql import Base
from app.models.user import User
from app.models.document import Document
from app.models.shared import SharedDocument

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_online():
    connectable = engine_from_config(
        {"sqlalchemy.url": f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}/{settings.MYSQL_DB}"},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            compare_type=True
        )
        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
