# pytest test_app.py
# Automated Tests
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_search():
    response = client.post("/search", json={"sql": "SELECT * FROM harmonized_metadata"})
    assert response.status_code == 200
    data = response.json()
    assert data == {}
