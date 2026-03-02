import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_register_and_login():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register
        res = await client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "securepass123"
        })
        assert res.status_code == 201
        
        # Login
        res = await client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "securepass123"
        })
        assert res.status_code == 200
        assert "access_token" in res.json()