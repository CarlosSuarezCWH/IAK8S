import pytest
from fastapi import status
from app.schemas.auth import UserCreate

@pytest.mark.asyncio
async def test_create_user(client):
    user_data = {
        "email": "newuser@example.com",
        "password": "StrongPass123!",
        "password_confirm": "StrongPass123!",
        "full_name": "New User"
    }
    
    response = await client.post("/auth/register", json=user_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_success(client, test_user):
    response = await client.post("/auth/login", data={
        "username": test_user.email,
        "password": "testpass123"
    })
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_credentials(client, test_user):
    response = await client.post("/auth/login", data={
        "username": test_user.email,
        "password": "wrongpassword"
    })
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_get_current_user(client, auth_headers):
    response = await client.get("/auth/me", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "hashed_password" not in data