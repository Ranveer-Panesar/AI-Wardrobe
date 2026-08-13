import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import CHAR, TypeDecorator

from app.database import Base


class GUID(TypeDecorator):
    """
    Platform-independent UUID column: uses native UUID on Postgres,
    falls back to CHAR(36) on SQLite (dev default). Lets you write the
    model once and not worry about which DB you're running against.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return uuid.UUID(value) if not isinstance(value, uuid.UUID) else value


class User(Base):
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)

    # "local" = device-only storage, "cloud" = synced to object storage.
    # Set at signup, changeable later in settings.
    storage_mode = Column(String, default="local")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
