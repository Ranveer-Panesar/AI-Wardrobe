"""
Auth flow tests against a real (but isolated, file-based, auto-deleted)
SQLite DB — unlike the classify tests, this needs actual DB read/write
behavior (uniqueness constraints, password verification), so mocking the
DB layer wouldn't actually tell us anything useful.
"""
import os

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

TEST_DB_PATH = "./test_auth.db"
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH}"


@pytest.fixture(scope="function", autouse=True)
def test_db():
    """Fresh DB file per test function — no state leaking between tests."""
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)
    engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


client = TestClient(app)

# Registered once at module level (not inside a test) so it exists
# regardless of test execution order — a stand-in for "any real protected
# route," which don't exist yet (wardrobe/outfit endpoints land in later phases).
from app.core.deps import get_current_user  # noqa: E402


@app.get("/_test_protected")
def _protected_test_route(user=Depends(get_current_user)):
    return {"id": str(user.id)}


VALID_SIGNUP = {"email": "test@example.com", "phone": "+919876543210", "password": "Secret@123"}


def test_signup_creates_user():
    response = client.post("/auth/signup", json=VALID_SIGNUP)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == VALID_SIGNUP["email"]
    assert body["phone"] == VALID_SIGNUP["phone"]
    assert "password" not in body  # never leak the hash or raw password


def test_signup_rejects_duplicate_email():
    client.post("/auth/signup", json=VALID_SIGNUP)
    dupe = {**VALID_SIGNUP, "phone": "+919876543211"}
    response = client.post("/auth/signup", json=dupe)
    assert response.status_code == 409


def test_signup_rejects_short_password():
    bad = {**VALID_SIGNUP, "password": "short"}
    response = client.post("/auth/signup", json=bad)
    assert response.status_code == 422


def test_signup_rejects_invalid_phone():
    bad = {**VALID_SIGNUP, "phone": "not-a-phone"}
    response = client.post("/auth/signup", json=bad)
    assert response.status_code == 422


def test_login_succeeds_with_correct_credentials():
    client.post("/auth/signup", json=VALID_SIGNUP)
    response = client.post(
        "/auth/login", json={"email": VALID_SIGNUP["email"], "password": VALID_SIGNUP["password"]}
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_login_fails_with_wrong_password():
    client.post("/auth/signup", json=VALID_SIGNUP)
    response = client.post("/auth/login", json={"email": VALID_SIGNUP["email"], "password": "wrongpassword"})
    assert response.status_code == 401


def test_login_fails_for_nonexistent_user():
    response = client.post("/auth/login", json={"email": "nobody@example.com", "password": "whatever123"})
    assert response.status_code == 401


def test_refresh_issues_new_tokens():
    client.post("/auth/signup", json=VALID_SIGNUP)
    login_resp = client.post(
        "/auth/login", json={"email": VALID_SIGNUP["email"], "password": VALID_SIGNUP["password"]}
    )
    refresh_token = login_resp.json()["refresh_token"]

    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_refresh_rejects_an_access_token_used_as_refresh_token():
    """An access token should NOT work where a refresh token is expected —
    this is exactly the kind of mix-up a bug could silently allow."""
    client.post("/auth/signup", json=VALID_SIGNUP)
    login_resp = client.post(
        "/auth/login", json={"email": VALID_SIGNUP["email"], "password": VALID_SIGNUP["password"]}
    )
    access_token = login_resp.json()["access_token"]

    response = client.post("/auth/refresh", json={"refresh_token": access_token})
    assert response.status_code == 401


def test_protected_route_rejects_missing_token():
    response = client.get("/_test_protected")
    assert response.status_code in (401, 403)  # HTTPBearer returns 403 when header is entirely missing


def test_protected_route_accepts_valid_token():
    client.post("/auth/signup", json=VALID_SIGNUP)
    login_resp = client.post(
        "/auth/login", json={"email": VALID_SIGNUP["email"], "password": VALID_SIGNUP["password"]}
    )
    access_token = login_resp.json()["access_token"]

    response = client.get("/_test_protected", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
