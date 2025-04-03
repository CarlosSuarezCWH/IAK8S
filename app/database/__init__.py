from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.config import settings
from .mysql import async_engine, AsyncSessionLocal
from .mongodb import mongo_client, get_mongo_db

async def init_db():
    """Initialize database connections"""
    # MySQL connection is lazy, no need to explicitly connect
    # MongoDB connection test
    try:
        await get_mongo_db().command('ping')
    except PyMongoError as e:
        raise RuntimeError(f"MongoDB connection failed: {str(e)}")

async def close_db():
    """Close all database connections"""
    # Close MySQL connections
    if async_engine:
        await async_engine.dispose()
    
    # Close MongoDB connection
    if mongo_client:
        mongo_client.close()

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async DB session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# MongoDB dependency
def get_mongo_db():
    return mongo_client[settings.MONGO_DB_NAME]