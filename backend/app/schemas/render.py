"""
Pydantic schemas for the render / VTON endpoints (Phase 6).
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


RenderStatus = Literal["queued", "processing", "done", "failed"]
RenderType = Literal["mannequin", "try_on"]


class RenderJobResponse(BaseModel):
    """Returned from POST /render/* and GET /render/jobs/{id}."""
    job_id: str
    status: RenderStatus
    render_type: RenderType
    outfit_id: str | None
    output_image_url: str | None = None
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MannequinRenderRequest(BaseModel):
    outfit_id: str


class TryOnRenderRequest(BaseModel):
    outfit_id: str
    # person_image is sent as a multipart file, not JSON — handled in the router
