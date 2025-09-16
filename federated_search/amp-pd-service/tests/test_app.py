# tests/test_app.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.dependencies import get_db
from app.models.person import Person
from main import app

from sqlalchemy.pool import StaticPool

# Create an in-memory SQLite database for tests
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=test_engine)

# Override FastAPI dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create the tables before running tests
@pytest.fixture(scope="module", autouse=True)
def create_test_db():
    # Create schema
    Base.metadata.bind = test_engine
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    db.add(Person(person_id=1, gender="male", year_of_birth=1980,
                  race="asian", ethnicity="non-hispanic", diagnosis_name="Parkinson"))
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)


client = TestClient(app)


def test_public_search_query():
    payload = {"query": "SELECT * FROM person", "parameters": {"access_tier": "public"}}
    response = client.post("/search", json=payload)
    assert response.status_code == 200
    json_response = response.json()
    assert "data" in json_response
    assert len(json_response["data"]) == 1
    # Public should only see person_id and diagnosis_name
    assert "person_id" in json_response["data"][0]
    assert "diagnosis_name" in json_response["data"][0]
    assert "gender" not in json_response["data"][0]
    assert "year_of_birth" not in json_response["data"][0]

    assert "restricted_fields" in json_response
    assert "gender" in json_response["restricted_fields"]
    assert "year_of_birth" in json_response["restricted_fields"]


def test_registered_search_query_unauthenticated():
    payload = {"query": "SELECT * FROM person", "parameters": {"access_tier": "registered"}}
    response = client.post("/search", json=payload)
    assert response.status_code == 200
    json_response = response.json()
    assert "data" in json_response
    assert len(json_response["data"]) == 1
    # Unauthenticated registered should only see public data
    assert "person_id" in json_response["data"][0]
    assert "diagnosis_name" in json_response["data"][0]
    assert "gender" not in json_response["data"][0]
    assert "year_of_birth" not in json_response["data"][0]

    assert "restricted_fields" in json_response
    assert "gender" in json_response["restricted_fields"]
    assert "year_of_birth" in json_response["restricted_fields"]


def test_registered_search_query_authenticated():
    payload = {"query": "SELECT * FROM person", "parameters": {"access_tier": "registered"}}
    headers = {"Authorization": "Bearer fake-token"}
    response = client.post("/search", json=payload, headers=headers)
    assert response.status_code == 200
    json_response = response.json()
    assert "data" in json_response
    assert len(json_response["data"]) == 1
    # Registered should see demographic data, but not year_of_birth
    assert "person_id" in json_response["data"][0]
    assert "gender" in json_response["data"][0]
    assert "race" in json_response["data"][0]
    assert "ethnicity" in json_response["data"][0]
    assert "year_of_birth" not in json_response["data"][0]

    assert "restricted_fields" in json_response
    assert "gender" not in json_response["restricted_fields"]
    assert "year_of_birth" in json_response["restricted_fields"]


def test_controlled_search_query_unauthenticated():
    payload = {"query": "SELECT * FROM person", "parameters": {"access_tier": "controlled"}}
    response = client.post("/search", json=payload)
    assert response.status_code == 200
    json_response = response.json()
    assert "data" in json_response
    assert len(json_response["data"]) == 1
    # Unauthenticated controlled should only see public data
    assert "person_id" in json_response["data"][0]
    assert "diagnosis_name" in json_response["data"][0]
    assert "gender" not in json_response["data"][0]
    assert "year_of_birth" not in json_response["data"][0]

    assert "restricted_fields" in json_response
    assert "gender" in json_response["restricted_fields"]
    assert "year_of_birth" in json_response["restricted_fields"]


def test_controlled_search_query_authenticated():
    payload = {"query": "SELECT * FROM person", "parameters": {"access_tier": "controlled"}}
    headers = {"Authorization": "Bearer fake-token"}
    response = client.post("/search", json=payload, headers=headers)
    assert response.status_code == 200
    json_response = response.json()
    assert "data" in json_response
    assert len(json_response["data"]) == 1
    # Controlled should see all fields
    assert "person_id" in json_response["data"][0]
    assert "gender" in json_response["data"][0]
    assert "year_of_birth" in json_response["data"][0]

    assert "restricted_fields" in json_response
    assert not json_response["restricted_fields"]


def test_invalid_tier_search_query():
    payload = {"query": "SELECT * FROM person", "parameters": {"access_tier": "invalid_tier"}}
    response = client.post("/search", json=payload)
    assert response.status_code == 400
    json_response = response.json()
    assert "errors" in json_response
    assert json_response["errors"][0]["title"] == "Bad Request"
