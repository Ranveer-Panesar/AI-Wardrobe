"""
Tests for the outfit engine (Phase 3).

Section 1 — Pure unit tests for each scoring function.
Section 2 — Integration tests for the combination generator.
Section 3 — API-level tests for POST /outfits/generate and GET /outfits/saved.

The engine itself (outfit_engine.py) has no DB/FastAPI deps, so Sections 1–2
run without TestClient or any mocking.
"""
from __future__ import annotations

import uuid
import io
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.deps import get_current_user
from app.main import app
from app.models.user import User
from app.routers.classify import get_classifier
from app.services.outfit_engine import (
    GarmentData,
    CategoryType,
    assign_style_tags,
    category_structure_score,
    color_harmony_score,
    formality_score,
    generate_outfits,
    get_category_type,
    pattern_clash_penalty,
    score_outfit,
)


# ===========================================================================
# Section 1 — Unit tests for individual scoring functions
# ===========================================================================

class TestGetCategoryType:
    def test_known_labels(self):
        assert get_category_type("t-shirt") == CategoryType.TOP
        assert get_category_type("Jeans") == CategoryType.BOTTOM
        assert get_category_type("blazer") == CategoryType.OUTERWEAR
        assert get_category_type("dress") == CategoryType.DRESS

    def test_unknown_label(self):
        assert get_category_type("sombrero") == CategoryType.UNKNOWN

    def test_case_insensitive(self):
        assert get_category_type("CASUAL SHIRT") == CategoryType.TOP


class TestColorHarmonyScore:
    def test_both_neutral(self):
        # White + grey → 0.90
        score = color_harmony_score(["#f5f5f5"], ["#cccccc"])
        assert score == pytest.approx(0.90)

    def test_one_neutral(self):
        score = color_harmony_score(["#f5f5f5"], ["#e63946"])
        assert score == pytest.approx(0.85)

    def test_analogous(self):
        # Both blue hues — hue distance < 30°
        score = color_harmony_score(["#1a1aff"], ["#0000cc"])
        assert score == pytest.approx(1.0)

    def test_empty_colors_returns_neutral(self):
        assert color_harmony_score([], ["#ff0000"]) == 0.5
        assert color_harmony_score([], []) == 0.5


class TestFormalityScore:
    def test_all_same_level_is_perfect(self):
        assert formality_score(["casual", "casual", "casual"]) == pytest.approx(1.0)

    def test_extreme_mismatch_is_penalised(self):
        score = formality_score(["very casual", "formal"])
        assert score < 0.5

    def test_adjacent_levels_acceptable(self):
        # casual=1, smart casual=2 → std-dev=0.5 → score = 1 - 0.5/1.5 ≈ 0.667
        score = formality_score(["casual", "smart casual"])
        assert score > 0.6

    def test_single_garment_is_perfect(self):
        assert formality_score(["formal"]) == pytest.approx(1.0)


class TestPatternClashPenalty:
    def test_all_solid_no_penalty(self):
        assert pattern_clash_penalty(["solid", "solid"]) == 0.0

    def test_solid_plus_busy_no_penalty(self):
        assert pattern_clash_penalty(["solid", "striped"]) == 0.0

    def test_two_distinct_busy_patterns_clash(self):
        assert pattern_clash_penalty(["striped", "floral"]) == pytest.approx(0.35)

    def test_same_busy_pattern_repeated_soft_penalty(self):
        assert pattern_clash_penalty(["striped", "striped"]) == pytest.approx(0.15)

    def test_three_busy_patterns_clash(self):
        assert pattern_clash_penalty(["striped", "floral", "checked"]) == pytest.approx(0.35)


class TestCategoryStructureScore:
    def test_top_and_bottom_complete(self):
        assert category_structure_score(["t-shirt", "jeans"]) == pytest.approx(1.0)

    def test_dress_alone_complete(self):
        assert category_structure_score(["dress"]) == pytest.approx(1.0)

    def test_two_tops_no_structure(self):
        assert category_structure_score(["t-shirt", "casual shirt"]) < 0.5

    def test_full_outfit_scores_one(self):
        assert category_structure_score(["t-shirt", "jeans", "jacket"]) == pytest.approx(1.0)


class TestScoreOutfit:
    def test_perfect_outfit_near_one(self):
        garments = [
            GarmentData("1", "t-shirt", "solid", "casual", ["#1a1aff"]),
            GarmentData("2", "jeans", "solid", "casual", ["#0000cc"]),
        ]
        assert score_outfit(garments) > 0.75

    def test_clashing_outfit_is_penalised(self):
        # striped+floral clash, very casual+formal mismatch, red+green colour clash
        # scores ~0.55 — well below a harmonious outfit's 0.75+
        garments = [
            GarmentData("1", "t-shirt", "striped", "very casual", ["#ff0000"]),
            GarmentData("2", "jeans", "floral", "formal", ["#00ff00"]),
        ]
        assert score_outfit(garments) < 0.60

    def test_score_bounded_0_to_1(self):
        garments = [GarmentData("1", "dress", "solid", "casual", [])]
        s = score_outfit(garments)
        assert 0.0 <= s <= 1.0


class TestAssignStyleTags:
    def test_formal_solid_scores_high_formal(self):
        garments = [
            GarmentData("1", "formal shirt", "solid", "formal", []),
            GarmentData("2", "formal trousers", "solid", "formal", []),
        ]
        tags = assign_style_tags(garments)
        assert tags["formal"] > tags["casual"]

    def test_graphic_print_scores_bold(self):
        garments = [
            GarmentData("1", "t-shirt", "graphic print", "casual", []),
            GarmentData("2", "jeans", "solid", "casual", []),
        ]
        tags = assign_style_tags(garments)
        assert tags["bold"] == pytest.approx(0.6)

    def test_returns_all_four_keys(self):
        garments = [GarmentData("1", "t-shirt", "solid", "casual", [])]
        tags = assign_style_tags(garments)
        assert set(tags.keys()) == {"casual", "bold", "formal", "retro"}


# ===========================================================================
# Section 2 — Combination generator integration tests
# ===========================================================================

def _garment(category: str, pattern: str = "solid", formality: str = "casual",
             colors: list | None = None, gid: str | None = None) -> GarmentData:
    return GarmentData(
        id=gid or str(uuid.uuid4()),
        category=category,
        pattern=pattern,
        formality=formality,
        dominant_colors=colors or ["#cccccc"],
    )


class TestGenerateOutfits:
    def test_empty_wardrobe_returns_empty(self):
        assert generate_outfits([]) == []

    def test_top_and_bottom_generates_outfit(self):
        garments = [_garment("t-shirt"), _garment("jeans")]
        outfits = generate_outfits(garments, count=5)
        assert len(outfits) >= 1

    def test_dress_generates_outfit(self):
        garments = [_garment("dress")]
        outfits = generate_outfits(garments, count=5)
        assert len(outfits) >= 1

    def test_dress_with_top_is_invalid(self):
        # DRESS + TOP is an invalid combo — engine should filter it out
        garments = [_garment("dress"), _garment("t-shirt")]
        outfits = generate_outfits(garments, count=10)
        for o in outfits:
            assert len(o.garment_ids) == 1  # only the dress alone is valid here

    def test_count_respected(self):
        garments = [
            _garment("t-shirt"), _garment("casual shirt"), _garment("polo shirt"),
            _garment("jeans"), _garment("formal trousers"), _garment("shorts"),
        ]
        outfits = generate_outfits(garments, count=3)
        assert len(outfits) <= 3

    def test_outfits_sorted_by_score_descending(self):
        garments = [
            _garment("t-shirt"), _garment("casual shirt"),
            _garment("jeans"), _garment("formal trousers"),
        ]
        outfits = generate_outfits(garments, count=10)
        scores = [o.score for o in outfits]
        assert scores == sorted(scores, reverse=True)

    def test_no_duplicates(self):
        garments = [_garment("t-shirt"), _garment("jeans")]
        outfits = generate_outfits(garments, count=50)
        seen = set()
        for o in outfits:
            key = frozenset(o.garment_ids)
            assert key not in seen, "Duplicate outfit returned"
            seen.add(key)

    def test_outerwear_included_in_some_combos(self):
        garments = [
            _garment("t-shirt"), _garment("jeans"), _garment("jacket"),
        ]
        outfits = generate_outfits(garments, count=10)
        ids = {g.id for g in garments if g.category == "jacket"}
        combos_with_jacket = [o for o in outfits if any(gid in ids for gid in o.garment_ids)]
        assert len(combos_with_jacket) >= 1

    def test_style_tags_present(self):
        garments = [_garment("t-shirt"), _garment("jeans")]
        outfits = generate_outfits(garments)
        for o in outfits:
            assert set(o.style_tags.keys()) == {"casual", "bold", "formal", "retro"}


# ===========================================================================
# Section 3 — API tests for /outfits endpoints
# ===========================================================================

class FakeClassifier:
    def classify_category(self, image):
        return "casual shirt", 0.91
    def classify_pattern(self, image):
        return "solid", 0.80
    def classify_formality(self, image):
        return "casual", 0.70
    def get_embedding(self, image):
        return [0.1] * 512


def _fake_user():
    u = User()
    u.id = uuid.UUID("bbbbbbbb-0000-0000-0000-000000000002")
    u.email = "outfit@example.com"
    u.phone = "+919876543211"
    u.password_hash = "irrelevant"
    return u


def _png() -> io.BytesIO:
    img = Image.new("RGB", (60, 60), (50, 100, 150))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


@pytest.fixture()
def api_client(tmp_path):
    """
    Creates a TestClient backed by a fresh in-memory SQLite database for
    every test that uses it.  This prevents garments written in one test
    from bleeding into another and avoids any dependency on wardrobe.db.
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
    app.dependency_overrides[get_current_user] = _fake_user

    with patch("app.routers.wardrobe.settings") as ms:
        ms.LOCAL_UPLOAD_DIR = str(tmp_path / "uploads")
        with TestClient(app) as c:
            yield c

    # Restore to pre-fixture state (don't wipe overrides from other modules).
    app.dependency_overrides.clear()
    app.dependency_overrides.update(_saved_overrides)


AUTH = {"Authorization": "Bearer fake-token"}


def _upload_garment(client, category_override=None) -> str:
    """Upload one image and optionally patch its category, returning the garment ID."""
    resp = client.post("/wardrobe/items", files={"file": ("g.png", _png(), "image/png")}, headers=AUTH)
    assert resp.status_code == 201
    gid = resp.json()["id"]
    if category_override:
        client.patch(f"/wardrobe/items/{gid}", json={"category": category_override}, headers=AUTH)
    return gid


def test_generate_returns_422_with_fewer_than_2_garments(api_client):
    _upload_garment(api_client, "t-shirt")
    resp = api_client.post("/outfits/generate", json={"count": 5}, headers=AUTH)
    assert resp.status_code == 422


def test_generate_returns_outfits(api_client):
    _upload_garment(api_client, "t-shirt")
    _upload_garment(api_client, "jeans")
    resp = api_client.post("/outfits/generate", json={"count": 3}, headers=AUTH)
    assert resp.status_code == 200
    body = resp.json()
    assert "outfits" in body
    assert len(body["outfits"]) >= 1
    outfit = body["outfits"][0]
    assert "id" in outfit
    assert "garment_ids" in outfit
    assert "score" in outfit
    assert "style_tags" in outfit
    assert 0.0 <= outfit["score"] <= 1.0


def test_generate_count_respected(api_client):
    _upload_garment(api_client, "t-shirt")
    _upload_garment(api_client, "jeans")
    resp = api_client.post("/outfits/generate", json={"count": 1}, headers=AUTH)
    assert resp.status_code == 200
    assert len(resp.json()["outfits"]) <= 1


def test_saved_outfits_returns_generated(api_client):
    _upload_garment(api_client, "t-shirt")
    _upload_garment(api_client, "jeans")
    api_client.post("/outfits/generate", json={"count": 3}, headers=AUTH)

    resp = api_client.get("/outfits/saved", headers=AUTH)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert len(body["outfits"]) >= 1
