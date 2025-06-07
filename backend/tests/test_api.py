import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_create_analysis_task():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/analysis/",
            json={"youtube_url": "https://youtube.com/watch?v=test", "options": {}},
        )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_get_analysis_task():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        create_response = await ac.post(
            "/api/v1/analysis/",
            json={"youtube_url": "https://youtube.com/watch?v=test", "options": {}},
        )
        task_id = create_response.json()["id"]

        response = await ac.get(f"/api/v1/analysis/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert "youtube_url" in data


@pytest.mark.asyncio
async def test_list_analysis_tasks():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/analysis/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_nonexistent_task():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/analysis/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_invalid_youtube_url():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/analysis/", json={"youtube_url": "invalid-url", "options": {}}
        )
    assert response.status_code == 422
