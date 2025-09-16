import pytest
import httpx
import respx
from httpx import AsyncClient, ASGITransport
import json
from jose import jwt
import os

from main import app


@pytest.mark.asyncio
@respx.mock
async def test_successful_public_query():
    pd_route = respx.post("http://amp-pd:8080/search").mock(
        return_value=httpx.Response(200, json={"data": [{"person_id": 101}]})
    )
    ad_route = respx.post("http://amp-ad:8080/search").mock(
        return_value=httpx.Response(200, json={"data": [{"person_id": 2001}]})
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/search", json={
            "query": "SELECT * FROM person",
            "parameters": {
                "pd_access_tier": "public",
                "ad_access_tier": "public"
            }
        })

    assert response.status_code == 200
    body = response.json()
    
    # Check that downstream services were called correctly
    pd_request_body = json.loads(pd_route.calls.last.request.content)
    assert pd_request_body["parameters"]["access_tier"] == "public"
    assert "Authorization" not in pd_route.calls.last.request.headers

    ad_request_body = json.loads(ad_route.calls.last.request.content)
    assert ad_request_body["parameters"]["access_tier"] == "public"
    assert "Authorization" not in ad_route.calls.last.request.headers

@pytest.mark.asyncio
@respx.mock
async def test_successful_registered_query():
    pd_route = respx.post("http://amp-pd:8080/search").mock(
        return_value=httpx.Response(200, json={"data": [{"person_id": 101}]})
    )
    ad_route = respx.post("http://amp-ad:8080/search").mock(
        return_value=httpx.Response(200, json={"data": [{"person_id": 2001}]})
    )

    # Create a mock JWT
    token = jwt.encode({"sub": "user"}, os.getenv("JWT_SECRET", "secret"), "HS256")
    headers = {"Authorization": f"Bearer {token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/search", json={
            "query": "SELECT * FROM person",
            "parameters": {
                "pd_access_tier": "registered",
                "ad_access_tier": "controlled"
            }
        }, headers=headers)

    assert response.status_code == 200
    
    # Check that downstream services were called with correct tiers and auth header
    pd_request_body = json.loads(pd_route.calls.last.request.content)
    assert pd_request_body["parameters"]["access_tier"] == "registered"
    assert pd_route.calls.last.request.headers["Authorization"] == f"Bearer {token}"

    ad_request_body = json.loads(ad_route.calls.last.request.content)
    assert ad_request_body["parameters"]["access_tier"] == "controlled"
    assert ad_route.calls.last.request.headers["Authorization"] == f"Bearer {token}"


@pytest.mark.asyncio
async def test_invalid_sql():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/search", json={"query": "SELEC WRONG SYNTAX", "parameters": {}})
    assert res.status_code == 400
    assert "Invalid SQL" in res.json()["errors"][0]["detail"]
