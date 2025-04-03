import pytest
from app.services import auth, document
from app.schemas.auth import UserCreate
from app.schemas.document import DocumentCreate

@pytest.mark.asyncio
async def test_auth_service_create_user(db):
    user_data = UserCreate(
        email="serviceuser@example.com",
        password="ServicePass123!",
        password_confirm="ServicePass123!",
        full_name="Service User"
    )
    
    created_user = await auth.AuthService.create_user(db, user_data)
    assert created_user.email == "serviceuser@example.com"
    assert created_user.is_active is True

@pytest.mark.asyncio
async def test_document_service_create(db, test_user):
    doc_data = DocumentCreate(name="Service Test Doc")
    doc = await document.DocumentService.create_document(
        db, test_user.id, None, doc_data
    )
    assert doc.name == "Service Test Doc"
    assert doc.user_id == test_user.id

@pytest.mark.asyncio
async def test_vector_store_service(mocker):
    from app.services.vector_store import VectorStoreService
    import numpy as np
    
    mock_collection = mocker.MagicMock()
    mock_collection.insert_many.return_value.inserted_ids = [1, 2, 3]
    
    mocker.patch(
        "app.services.vector_store.get_mongo_collection",
        return_value=mock_collection
    )
    
    service = VectorStoreService()
    chunks = await service.create_and_store_embeddings(
        "doc1", "test text", {"meta": "data"}
    )
    assert chunks == 3