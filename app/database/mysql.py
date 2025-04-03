from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings

# Connection pool configuration
async_engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=settings.DEBUG,
    poolclass=QueuePool,
    pool_size=settings.MYSQL_POOL_SIZE,
    max_overflow=settings.MYSQL_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_timeout=30,
    connect_args={
        "connect_timeout": 10,
        "ssl": False
    }
)

# Session factory
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

Base = declarative_base()

# Optional: Connection event listeners
@event.listens_for(async_engine.sync_engine, "connect")
def set_sql_mode(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("SET SESSION sql_mode='STRICT_TRANS_TABLES'")
    cursor.close()

async def test_connection():
    """Test database connection"""
    async with AsyncSessionLocal() as session:
        try:
            await session.execute("SELECT 1")
            return True
        except SQLAlchemyError:
            return False