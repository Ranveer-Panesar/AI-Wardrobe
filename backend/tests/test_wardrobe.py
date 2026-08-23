"""
Tests for the wardrobe endpoints (POST/GET/PATCH/DELETE /wardrobe/items).

Uses the same dependency-override pattern as test_classify.py to avoid
loading Fashion-CLIP or touching the real filesystem.

Overrides:
  • get_classifier → FakeClassifier (fixed labels, no GPU needed)
  • The router's _save_image helper is NOT mocked — we let it write to a
    real temp dir so we also verify the file-persistence path doesn't blow up.
"""
import io
import shutil
import tempfile
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.deps import get_current_user
from app.main import app
from app.models.user import User
from app.routers.classify import get_classifier

# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class FakeClassifier:
    def classify_category(self, image):
        return "casual shirt", 0.91

    def classify_pattern(self, image):
        return "solid", 0.80

    def classify_formality(self, image):
        return "casual", 0.70

    def get_embedding(self, image):
        return [0.1] * 512


def fake_user():
    u = User()
    u.id = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
    u.email = "test@example.com"
    u.phone = "+919876543210"
    u.password_hash = "irrelevant"
    return u


def _png_bytes(colors=None) -> io.BytesIO:
    """Create a small multi-colour PNG in memory."""
    img = Image.new("RGB", (60, 60), color=(30, 60, 90))
    for x in range(20, 40):
        for y in range(60):
            img.putpixel((x, y), (200, 200, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def override_deps(tmp_path):
    """
    Apply dependency overrides for the entire test module and patch the
    upload directory to a temp folder so we don't litter the repo.

    Also overrides get_db with a fresh in-memory SQLite DB so every test
    run starts with an empty wardrobe and never touches wardrobe.db.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.database import Base, get_db

    # StaticPool forces all sessions to reuse the same underlying connection,
    # which is required for SQLite :memory: — without it each new Session
    # opens a fresh connection to a brand-new empty in-memory DB.
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    _saved_overrides = dict(app.dependency_overrides)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_classifier] = lambda: FakeClassifier()
    app.dependency_overrides[get_current_user] = fake_user

    with patch("app.routers.wardrobe.settings") as mock_settings:
        mock_settings.LOCAL_UPLOAD_DIR = str(tmp_path / "uploads")
        yield

    # Restore to pre-fixture state (don't wipe overrides from other modules).
    app.dependency_overrides.clear()
    app.dependency_overrides.update(_saved_overrides)


@pytest.fixture()
def client(tmp_path):
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Upload tests
# ---------------------------------------------------------------------------

def test_upload_returns_201_with_correct_shape(client):
    response = client.post(
        "/wardrobe/items",
        files={"file": ("shirt.png", _png_bytes(), "image/png")},
        headers={"Authorization": "Bearer fake-token"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["category"] == "casual shirt"
    assert body["pattern"] == "solid"
    assert body["formality"] == "casual"
    assert body["category_confidence"] == pytest.approx(0.91, abs=1e-4)
    assert len(body["dominant_colors"]) == 3
    assert body["image_url"].startswith("/uploads/")
    assert "id" in body
    assert "created_at" in body


def test_upload_rejects_non_image(client):
    response = client.post(
        "/wardrobe/items",
        files={"file": ("notes.txt", b"hello", "text/plain")},
        headers={"Authorization": "Bearer fake-token"},
    )
    assert response.status_code == 400


def test_upload_rejects_corrupt_bytes(client):
    response = client.post(
        "/wardrobe/items",
        files={"file": ("fake.png", b"not-an-image", "image/png")},
        headers={"Authorization": "Bearer fake-token"},
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# List tests
# ---------------------------------------------------------------------------

def test_list_returns_uploaded_garment(client):
    # Upload one item first
    client.post(
        "/wardrobe/items",
        files={"file": ("shirt.png", _png_bytes(), "image/png")},
        headers={"Authorization": "Bearer fake-token"},
    )

    response = client.get("/wardrobe/items", headers={"Authorization": "Bearer fake-token"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert len(body["items"]) >= 1
    assert body["items"][0]["category"] == "casual shirt"


# ---------------------------------------------------------------------------
# Patch tests
# ---------------------------------------------------------------------------

def test_patch_updates_category(client):
    upload = client.post(
        "/wardrobe/items",
        files={"file": ("shirt.png", _png_bytes(), "image/png")},
        headers={"Authorization": "Bearer fake-token"},
    )
    garment_id = upload.json()["id"]

    patch_resp = client.patch(
        f"/wardrobe/items/{garment_id}",
        json={"category": "formal shirt"},
        headers={"Authorization": "Bearer fake-token"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["category"] == "formal shirt"


def test_patch_nonexistent_garment_returns_404(client):
    response = client.patch(
        f"/wardrobe/items/{uuid.uuid4()}",
        json={"category": "formal shirt"},
        headers={"Authorization": "Bearer fake-token"},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Delete tests
# ---------------------------------------------------------------------------

def test_delete_removes_garment(client):
    upload = client.post(
        "/wardrobe/items",
        files={"file": ("shirt.png", _png_bytes(), "image/png")},
        headers={"Authorization": "Bearer fake-token"},
    )
    garment_id = upload.json()["id"]

    del_resp = client.delete(
        f"/wardrobe/items/{garment_id}",
        headers={"Authorization": "Bearer fake-token"},
    )
    assert del_resp.status_code == 204

    # Subsequent patch/delete on same ID → 404
    resp = client.patch(
        f"/wardrobe/items/{garment_id}",
        json={"category": "t-shirt"},
        headers={"Authorization": "Bearer fake-token"},
    )
    assert resp.status_code == 404
