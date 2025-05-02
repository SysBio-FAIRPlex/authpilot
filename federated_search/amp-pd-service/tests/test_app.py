# tests/test_app.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.dependencies import get_db
from app.models import Person
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

def test_search_query():
    # You may want to insert test data here
    payload = {"sql": "SELECT * FROM foo"}
    response = client.post("/search", json=payload)
    assert response.status_code == 200
    assert "columns" in response.json()
    assert "rows" in response.json()
