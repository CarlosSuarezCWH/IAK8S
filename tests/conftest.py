import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient
import asyncio

from app.main import app
from app.config import settings
from app.database.mysql import Base, get_db_session
from app.database.init_db import init_db
import os

# Configuración de logging para tests
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database de test
TEST_DATABASE_URL = f"{settings.SQLALCHEMY_DATABASE_URI}_test"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def engine():
    """Async engine fixture"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )
    yield engine
    await engine.dispose()

@pytest.fixture(scope="function")
async def db(engine):
    """Create fresh database for each test"""
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    
    async with async_session() as session:
        yield session
    
    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def client(db):
    """Test client fixture with override for db dependency"""
    async def override_get_db():
        try:
            yield db
        finally:
            await db.close()
    
    app.dependency_overrides[get_db_session] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

# Fixtures para datos de prueba
@pytest.fixture
async def test_user(db):
    from app.models.user import User
    from app.utils.security import SecurityUtils
    
    user = User(
        email="test@example.com",
        hashed_password=SecurityUtils.get_password_hash("testpass123"),
        full_name="Test User",
        is_active=True
    )
    db.add(user)
    await db.commit()
    return user

@pytest.fixture
async def test_document(db, test_user):
    from app.models.document import Document
    
    doc = Document(
        user_id=test_user.id,
        name="Test Document",
        file_path="/test/path.pdf",
        file_type="application/pdf",
        file_size=1024,
        status="uploaded"
    )
    db.add(doc)
    await db.commit()
    return doc

@pytest.fixture
async def auth_headers(client, test_user):
    # Login to get token
    response = await client.post("/auth/login", data={
        "username": test_user.email,
        "password": "testpass123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}