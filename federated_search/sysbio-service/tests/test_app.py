import pytest
import httpx
import respx
from httpx import AsyncClient, ASGITransport

from main import app
from app.database import Base
from app.dependencies import get_db

DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.mark.asyncio
@respx.mock
async def test_successful_query():
    respx.post("http://amp-pd:8080/search").mock(
        return_value=httpx.Response(200, json={"data": [{"person_id": 101}]})
    )
    respx.post("http://amp-ad:8080/search").mock(
        return_value=httpx.Response(200, json={"data": [{"person_id": 2001}]})
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/search", json={
            "query": "SELECT * FROM person WHERE person_id > :min_id",
            "parameters": {"min_id": 0}
        })

    assert response.status_code == 200
    body = response.json()
    assert body["sources"]["pd"] == 1
    assert body["sources"]["ad"] == 1

@pytest.mark.asyncio
async def test_invalid_sql():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/search", json={"query": "SELEC WRONG SYNTAX", "parameters": {}})
    assert res.status_code == 400
    assert "Invalid SQL" in res.json()["errors"][0]["detail"]
