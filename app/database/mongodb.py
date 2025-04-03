from pymongo import MongoClient
from pymongo.errors import (
    PyMongoError,
    ConnectionFailure,
    OperationFailure,
    ServerSelectionTimeoutError
)
from contextlib import contextmanager
import logging
from typing import Iterator

from app.config import settings

logger = logging.getLogger(__name__)

class MongoDBConnectionError(Exception):
    """Custom exception for MongoDB connection issues"""
    pass

class MongoDBOperationError(Exception):
    """Custom exception for MongoDB operation failures"""
    pass

# Global MongoDB client
mongo_client: MongoClient = None

def initialize_mongo_client():
    """Initialize MongoDB client with connection pooling"""
    global mongo_client
    try:
        mongo_client = MongoClient(
            settings.MONGO_URI,
            maxPoolSize=settings.MONGO_MAX_POOL_SIZE,
            serverSelectionTimeoutMS=settings.MONGO_TIMEOUT_MS,
            socketTimeoutMS=settings.MONGO_TIMEOUT_MS,
            connectTimeoutMS=settings.MONGO_TIMEOUT_MS,
            retryWrites=True,
            retryReads=True
        )
        # Test the connection
        mongo_client.admin.command('ping')
        logger.info("MongoDB connection established successfully")
    except ServerSelectionTimeoutError as e:
        logger.error(f"MongoDB server selection timeout: {str(e)}")
        raise MongoDBConnectionError("Could not connect to MongoDB server")
    except ConnectionFailure as e:
        logger.error(f"MongoDB connection failed: {str(e)}")
        raise MongoDBConnectionError("MongoDB connection failed")
    except PyMongoError as e:
        logger.error(f"General MongoDB error: {str(e)}")
        raise MongoDBConnectionError("MongoDB initialization error")

@contextmanager
def get_mongo_collection(collection_name: str) -> Iterator:
    """Context manager for MongoDB collections with error handling"""
    if mongo_client is None:
        initialize_mongo_client()
    
    try:
        db = mongo_client[settings.MONGO_DB_NAME]
        collection = db[collection_name]
        yield collection
    except OperationFailure as e:
        logger.error(f"MongoDB operation failed: {str(e)}")
        raise MongoDBOperationError(f"Database operation failed: {str(e)}")
    except PyMongoError as e:
        logger.error(f"MongoDB error: {str(e)}")
        raise MongoDBOperationError(f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise

def close_mongo_connection():
    """Close MongoDB connection"""
    global mongo_client
    if mongo_client:
        try:
            mongo_client.close()
            logger.info("MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {str(e)}")
        finally:
            mongo_client = None

# Initialize on import
try:
    initialize_mongo_client()
except MongoDBConnectionError:
    # Will be retried on first operation if initial connection fails
    pass