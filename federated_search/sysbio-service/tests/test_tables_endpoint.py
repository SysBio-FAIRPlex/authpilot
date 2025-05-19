from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_tables_endpoint_returns_table_list():
    response = client.get("/tables")
    assert response.status_code == 200
    json = response.json()
    assert "tables" in json
    assert any(t["name"] == "person" for t in json["tables"])
