"""
Database seeding script.
Creates all database tables and ensures the default demo account exists:
  Email: demo@aiwardrobe.com
  Password: demo1234
Populates synthetic wardrobe garments if the closet is empty.
"""
import logging
import uuid
import sys
from pathlib import Path

# Add backend directory to sys.path if not present
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.garment import Garment
from app.core.security import hash_password
from app.services.classification import FashionClassifier
from app.services.synthetic_closet import seed_synthetic_closet

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("seed")


def seed():
    log.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "demo@aiwardrobe.com").first()
        if not user:
            user = User(
                id=uuid.uuid4(),
                email="demo@aiwardrobe.com",
                phone="+919876543210",
                password_hash=hash_password("demo1234"),
                email_verified=True,
                phone_verified=True,
                storage_mode="local",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            log.info("Created demo user: demo@aiwardrobe.com (password: demo1234)")
        else:
            log.info("Demo user already exists: demo@aiwardrobe.com")

        count = db.query(Garment).filter(Garment.user_id == user.id).count()
        if count == 0:
            log.info("Closet empty for demo user. Generating synthetic closet...")
            try:
                classifier = FashionClassifier()
                created = seed_synthetic_closet(db, user_id=str(user.id), classifier=classifier, max_items=12)
                log.info(f"Populated {len(created)} garments into demo user's digital closet.")
            except Exception as e:
                log.warning(f"Could not auto-generate synthetic closet: {e}")
        else:
            log.info(f"Demo user has {count} garments in digital closet.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
