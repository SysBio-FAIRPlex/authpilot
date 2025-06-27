import pytest
import os
import sys
from fastapi.testclient import TestClient

# This adds the parent directory to path so that imports can work from anywhere
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from db import SessionLocal, OAuthState


client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_oauth_state():
    """Clear OAuthState table before each test."""
    db = SessionLocal()
    db.query(OAuthState).delete()
    db.commit()
    db.close()

def test_login_duplicate_state_returns_400():
    params = {
        "redirect_uri": "http://localhost:3000/callback",
        "state": "dupe-state"
    }

    # First call should succeed (redirect)
    response1 = client.get("/login", params=params, follow_redirects=False)
    assert response1.status_code == 307
    assert response1.headers["location"].startswith("https://accounts.google.com/o/oauth2/v2/auth")

    # Second call should fail with 400
    response2 = client.get("/login", params=params)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"]