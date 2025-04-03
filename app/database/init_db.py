import os
import logging
from sqlalchemy import create_engine, inspect
from alembic.config import Config
from alembic import command
from app.config import settings
from app.database.mysql import Base
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations():
    try:
        # Configurar conexión
        engine = create_engine(
            f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}/{settings.MYSQL_DB}",
            pool_pre_ping=True
        )
        
        # Configurar Alembic
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option(
            "sqlalchemy.url", 
            f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}/{settings.MYSQL_DB}"
        )

        # Verificar conexión a la base de datos
        with engine.connect() as connection:
            inspector = inspect(engine)
            
            # Verificar si las tablas principales existen
            if not inspector.has_table("users"):
                logger.info("Creando tablas base desde modelos SQLAlchemy...")
                Base.metadata.create_all(bind=engine)
                command.stamp(alembic_cfg, "head")
                logger.info("Migración inicial completada")
            else:
                logger.info("Aplicando migraciones con Alembic...")
                command.upgrade(alembic_cfg, "head")
                logger.info("Migraciones aplicadas correctamente")
                
    except SQLAlchemyError as e:
        logger.error(f"Error de conexión a la base de datos: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado durante las migraciones: {str(e)}")
        raise
