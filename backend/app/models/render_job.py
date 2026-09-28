"""
RenderJob DB model — tracks async VTON render requests.

Each call to POST /render/try-on or POST /render/mannequin creates one row.
The background task updates status as it progresses:
  queued → processing → done | failed
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String
from sqlalchemy import ForeignKey

from app.database import Base
from app.models.user import GUID


class RenderJob(Base):
    __tablename__ = "render_jobs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Owner — jobs are always scoped to the user who requested them
    user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Which outfit this render is for (nullable — outfit may be deleted later)
    outfit_id = Column(
        GUID(),
        ForeignKey("outfits.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # "mannequin" | "try_on"
    render_type = Column(String, nullable=False)

    # "queued" | "processing" | "done" | "failed"
    status = Column(String, nullable=False, default="queued")

    # Relative URL to the rendered output image, set when status == "done"
    # e.g. "/renders/<uuid>.jpg" — served as static files by the backend
    output_image_url = Column(String, nullable=True)

    # Human-readable error, set when status == "failed"
    error_message = Column(String, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
