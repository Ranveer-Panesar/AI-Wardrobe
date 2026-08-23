"""
Quick demo seeder: creates a test user + inserts a realistic wardrobe
directly into the DB (bypassing image upload/Fashion-CLIP), then calls
POST /outfits/generate via the API and prints the results.

Run from backend/:
    python demo_seed.py
"""
import json
import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.core.security import hash_password
from app.database import Base
from app.models.garment import Garment
from app.models.user import User

# ---------------------------------------------------------------------------
# 1. Connect to the same DB the server uses
# ---------------------------------------------------------------------------
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
db = Session()

# ---------------------------------------------------------------------------
# 2. Create / reuse a demo user
# ---------------------------------------------------------------------------
DEMO_EMAIL = "demo@aiwardrobe.com"
DEMO_PASSWORD = "demo1234"

user = db.query(User).filter(User.email == DEMO_EMAIL).first()
if not user:
    user = User(
        id=uuid.uuid4(),
        email=DEMO_EMAIL,
        phone="+919999999999",
        password_hash=hash_password(DEMO_PASSWORD),
        storage_mode="local",
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"✓ Created demo user: {DEMO_EMAIL}")
else:
    print(f"✓ Demo user already exists: {DEMO_EMAIL}")

user_id = str(user.id)

# ---------------------------------------------------------------------------
# 3. Seed a realistic wardrobe (8 garments — tops, bottoms, outerwear)
# ---------------------------------------------------------------------------
WARDROBE = [
    {"category": "t-shirt",         "pattern": "solid",         "formality": "casual",       "dominant_colors": ["#ffffff", "#f0f0f0", "#e0e0e0"]},
    {"category": "casual shirt",    "pattern": "striped",       "formality": "smart casual", "dominant_colors": ["#1a3c5e", "#f2f2f2", "#0d2a45"]},
    {"category": "formal shirt",    "pattern": "solid",         "formality": "formal",       "dominant_colors": ["#f5f5f0", "#e8e4dc", "#ddd9ce"]},
    {"category": "polo shirt",      "pattern": "solid",         "formality": "smart casual", "dominant_colors": ["#2e7d32", "#1b5e20", "#388e3c"]},
    {"category": "jeans",           "pattern": "solid",         "formality": "casual",       "dominant_colors": ["#1565c0", "#0d47a1", "#1976d2"]},
    {"category": "formal trousers", "pattern": "solid",         "formality": "formal",       "dominant_colors": ["#212121", "#1a1a1a", "#303030"]},
    {"category": "shorts",          "pattern": "checked",       "formality": "very casual",  "dominant_colors": ["#8d6e63", "#795548", "#a1887f"]},
    {"category": "jacket",          "pattern": "solid",         "formality": "smart casual", "dominant_colors": ["#37474f", "#263238", "#455a64"]},
]

existing = db.query(Garment).filter(Garment.user_id == user_id).count()
if existing == 0:
    for i, g in enumerate(WARDROBE):
        db.add(Garment(
            id=uuid.uuid4(),
            user_id=user_id,
            category=g["category"],
            category_confidence=0.92,
            pattern=g["pattern"],
            formality=g["formality"],
            dominant_colors=g["dominant_colors"],
            embedding=None,
            image_url=f"/uploads/demo_{i}.jpg",
            created_at=datetime.now(timezone.utc),
        ))
    db.commit()
    print(f"✓ Seeded {len(WARDROBE)} garments")
else:
    print(f"✓ Wardrobe already has {existing} garments — skipping seed")

db.close()

# ---------------------------------------------------------------------------
# 4. Hit the live API: login → generate outfits → print results
# ---------------------------------------------------------------------------
BASE = "http://localhost:8000"
print("\n--- Calling live API ---")

login = httpx.post(f"{BASE}/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
token = login.json()["access_token"]
print(f"✓ Logged in, got access token")

headers = {"Authorization": f"Bearer {token}"}
resp = httpx.post(f"{BASE}/outfits/generate", json={"count": 5}, headers=headers)
outfits = resp.json()["outfits"]

print(f"\n🎽 Top {len(outfits)} outfit combos:\n")
for i, o in enumerate(outfits, 1):
    print(f"  #{i}  score={o['score']:.3f}  "
          f"garments={len(o['garment_ids'])}  "
          f"style={max(o['style_tags'], key=o['style_tags'].get)}")
    print(f"       style_tags={json.dumps(o['style_tags'])}")

print(f"\n✓ Outfit IDs saved to DB — ready for VTON render (Phase 6)")
print(f"\n🌐 Swagger UI → http://localhost:8000/docs")
print(f"   Email: {DEMO_EMAIL}  |  Password: {DEMO_PASSWORD}")
