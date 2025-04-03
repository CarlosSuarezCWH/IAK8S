import pytest
from datetime import datetime
from app.models.user import User, UserRole, UserPermission
from app.models.document import Document, DocumentStatus

@pytest.mark.asyncio
async def test_user_model(db):
    user = User(
        email="modeluser@example.com",
        hashed_password="hashedpass",
        full_name="Model User",
        role=UserRole.ADMIN,
        permissions=[UserPermission.DOCUMENTS_WRITE]
    )
    
    db.add(user)
    await db.commit()
    
    assert user.email == "modeluser@example.com"
    assert user.role == UserRole.ADMIN
    assert user.has_permission(UserPermission.DOCUMENTS_WRITE)

@pytest.mark.asyncio
async def test_document_model(db, test_user):
    doc = Document(
        user_id=test_user.id,
        name="Model Test Doc",
        file_path="/test/path.pdf",
        file_type="application/pdf",
        file_size=2048,
        status=DocumentStatus.PROCESSED
    )
    
    db.add(doc)
    await db.commit()
    
    assert doc.name == "Model Test Doc"
    assert doc.status == DocumentStatus.PROCESSED
    assert doc.get_metadata()["name"] == "Model Test Doc"