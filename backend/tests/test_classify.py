"""
Tests the /classify endpoint's wiring — request handling, image validation,
response shape — without needing to actually download/run Fashion-CLIP.
The real model is swapped out via FastAPI's dependency override, which is
exactly what you'd also do to keep CI fast later (no GPU/model download
needed just to check the route logic is correct).
"""
import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.routers.classify import get_classifier


class FakeClassifier:
    """Stands in for FashionClassifier — returns fixed, known outputs so
    we can assert on exact response values instead of unpredictable
    real-model outputs."""

    def classify_category(self, image):
        return "casual shirt", 0.91

    def classify_pattern(self, image):
        return "striped", 0.75

    def classify_formality(self, image):
        return "smart casual", 0.6

    def get_embedding(self, image):
        return [0.1, 0.2, 0.3]


def _fake_upload_image() -> io.BytesIO:
    """A tiny synthetic image with three distinct color blocks — needed so
    color quantization has more than one real color to find. Content
    otherwise doesn't matter; we're testing the plumbing, not real
    classification accuracy."""
    img = Image.new("RGB", (60, 60), color=(30, 60, 90))
    for x in range(20, 40):
        for y in range(60):
            img.putpixel((x, y), (200, 200, 200))
    for x in range(40, 60):
        for y in range(60):
            img.putpixel((x, y), (180, 40, 40))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


app.dependency_overrides[get_classifier] = lambda: FakeClassifier()
client = TestClient(app)


def test_classify_returns_expected_shape():
    buf = _fake_upload_image()
    response = client.post(
        "/classify", files={"file": ("shirt.png", buf, "image/png")}
    )
    assert response.status_code == 200

    body = response.json()
    assert body["category"] == "casual shirt"
    assert body["category_confidence"] == 0.91
    assert body["pattern"] == "striped"
    assert body["formality"] == "smart casual"
    assert len(body["dominant_colors"]) == 3
    assert all(c.startswith("#") for c in body["dominant_colors"])
    assert body["embedding"] is None  # not requested


def test_classify_includes_embedding_when_requested():
    buf = _fake_upload_image()
    response = client.post(
        "/classify?include_embedding=true",
        files={"file": ("shirt.png", buf, "image/png")},
    )
    assert response.status_code == 200
    assert response.json()["embedding"] == [0.1, 0.2, 0.3]


def test_classify_rejects_non_image_file():
    response = client.post(
        "/classify", files={"file": ("notes.txt", b"hello world", "text/plain")}
    )
    assert response.status_code == 400


def test_classify_rejects_corrupt_image_bytes():
    response = client.post(
        "/classify",
        files={"file": ("fake.png", b"not actually a png", "image/png")},
    )
    assert response.status_code == 400
