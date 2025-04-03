import pytest
from fastapi import status
from app.schemas.document import DocumentCreate

@pytest.mark.asyncio
async def test_upload_document(client, auth_headers, tmp_path):
    test_file = tmp_path / "test.pdf"
    test_file.write_text("Test content")
    
    with open(test_file, "rb") as f:
        response = await client.post(
            "/documents/upload",
            files={"file": ("test.pdf", f, "application/pdf")},
            data={"name": "Test Document"},
            headers=auth_headers
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Test Document"
    assert data["file_type"] == "application/pdf"

@pytest.mark.asyncio
async def test_get_user_documents(client, auth_headers, test_document):
    response = await client.get("/documents", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Document"

@pytest.mark.asyncio
async def test_process_document(client, auth_headers, test_document, mocker):
    # Mock the vector store processing
    mocker.patch(
        "app.services.vector_store.VectorStoreService.create_and_store_embeddings",
        return_value=5
    )
    
    response = await client.post(
        f"/documents/{test_document.id}/process",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Document processed successfully"