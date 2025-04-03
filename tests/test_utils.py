import pytest
from app.utils import security, file_processing
from fastapi import UploadFile
from io import BytesIO

def test_password_hashing():
    password = "testpass123"
    hashed = security.SecurityUtils.get_password_hash(password)
    assert security.SecurityUtils.verify_password(password, hashed)
    assert not security.SecurityUtils.verify_password("wrongpass", hashed)

@pytest.mark.asyncio
async def test_file_processing(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test content")
    
    processor = file_processing.FileProcessor()
    saved_path = await processor.save_upload_file(str(tmp_path), UploadFile(
        filename="test.txt",
        file=BytesIO(b"Test content")
    ))
    
    assert saved_path == str(tmp_path / "test.txt")
    content = await processor.extract_text(saved_path)
    assert content == "Test content"