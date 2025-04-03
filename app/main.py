from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from typing import Dict, Any

from app.config import settings, LOGGING_CONFIG
from app.database import init_db, close_db
from app.routers import auth, documents, shared, health
import logging.config

# Configuración inicial de logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting application with environment: %s", settings.ENVIRONMENT)
    
    try:
        await init_db()
        logger.info("Database connections initialized")
    except Exception as e:
        logger.critical("Database initialization failed: %s", str(e))
        raise
    
    yield  # Aquí la aplicación corre
    
    # Shutdown
    await close_db()
    logger.info("Application shutdown complete")

app = FastAPI(
    title="Document AI API",
    description="API for document processing and analysis",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None
)

# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(shared.router, prefix="/shared", tags=["Sharing"])

# Exception handlers could be added here