"""
Render / VTON endpoints (Phase 6).

POST  /render/mannequin          — queue a mannequin render for an outfit
POST  /render/try-on             — queue a try-on render with a user photo
GET   /render/jobs/{job_id}      — poll render job status + result URL

Renders are async: the endpoint returns a job_id immediately (202) and the
background task calls the configured RenderProvider (mock or Colab/IDM-VTON).
Frontend polls GET /render/jobs/{job_id} until status == "done" or "failed".
"""
from __future__ import annotations

import io
import logging
import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_current_user
from app.database import get_db
from app.models.garment import Outfit
from app.models.render_job import RenderJob
from app.models.user import User
from app.schemas.render import RenderJobResponse
from app.services.render import get_render_provider
from app.services.wardrobe_service import get_garment

log = logging.getLogger(__name__)

router = APIRouter(prefix="/render", tags=["render"])


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_outfit_or_404(db: Session, outfit_id: str, user_id: str) -> Outfit:
    """Fetch outfit belonging to this user, or raise 404."""
    outfit = (
        db.query(Outfit)
        .filter(Outfit.id == outfit_id, Outfit.user_id == user_id)
        .first()
    )
    if outfit is None:
        raise HTTPException(status_code=404, detail="Outfit not found")
    return outfit


def _garment_image_path(db: Session, garment_id: str, user_id: str) -> tuple[str, str]:
    """Resolve a garment's local image path and category. Raise 422 if missing."""
    upload_dir = Path(settings.LOCAL_UPLOAD_DIR)
    garment = get_garment(db, garment_id, user_id)
    if garment is None:
        raise HTTPException(status_code=404, detail="Garment not found")
    if not garment.image_url:
        raise HTTPException(status_code=422, detail="Garment has no uploaded image")
    rel = garment.image_url.lstrip("/")
    abs_path = upload_dir.parent / rel
    if not abs_path.exists():
        raise HTTPException(status_code=422, detail=f"Image file not found on disk: {abs_path}")
    return str(abs_path), garment.category or "upper_body"


def _primary_garment_path(db: Session, outfit: Outfit, user_id: str) -> tuple[str, str]:
    """
    Return the local filesystem path and category for the outfit's primary garment image.

    IDM-VTON renders one garment at a time. We pick the first garment_id
    in the outfit whose image_url resolves to an existing file.
    Raises 422 if no usable image can be found.
    """
    upload_dir = Path(settings.LOCAL_UPLOAD_DIR)

    for gid in outfit.garment_ids:
        garment = get_garment(db, gid, user_id)
        if garment and garment.image_url:
            # image_url is "/uploads/<uuid>.jpg" — strip leading "/" and join
            rel = garment.image_url.lstrip("/")
            abs_path = upload_dir.parent / rel
            if abs_path.exists():
                return str(abs_path), garment.category or "upper_body"

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="No uploaded garment images found for this outfit",
    )


def _job_to_response(job: RenderJob) -> RenderJobResponse:
    return RenderJobResponse(
        job_id=str(job.id),
        status=job.status,
        render_type=job.render_type,
        outfit_id=str(job.outfit_id) if job.outfit_id else None,
        output_image_url=job.output_image_url,
        error_message=job.error_message,
        created_at=job.created_at,
    )


# ---------------------------------------------------------------------------
# Background task runners
# ---------------------------------------------------------------------------

def _run_mannequin(job_id: str, garment_path: str, garment_category: str = "upper_body"):
    """Background task: call provider, update job status in DB."""
    # Import here to avoid circular deps at module load time
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        job = db.query(RenderJob).filter(RenderJob.id == job_id).first()
        if job is None:
            return

        job.status = "processing"
        db.commit()

        provider = get_render_provider()
        output_url = provider.mannequin(garment_path, job_id, garment_category=garment_category)

        job.status = "done"
        job.output_image_url = output_url
        db.commit()

    except Exception as exc:
        log.exception("Mannequin render failed for job %s", job_id)
        try:
            job.status = "failed"
            job.error_message = str(exc)
            db.commit()
        except Exception:
            pass
    finally:
        db.close()


def _run_try_on(job_id: str, garment_path: str, person_bytes: bytes, garment_category: str = "upper_body"):
    """Background task: call provider, update job status in DB."""
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        job = db.query(RenderJob).filter(RenderJob.id == job_id).first()
        if job is None:
            return

        job.status = "processing"
        db.commit()

        provider = get_render_provider()
        output_url = provider.try_on(garment_path, person_bytes, job_id, garment_category=garment_category)

        job.status = "done"
        job.output_image_url = output_url
        db.commit()

    except Exception as exc:
        log.exception("Try-on render failed for job %s", job_id)
        try:
            job.status = "failed"
            job.error_message = str(exc)
            db.commit()
        except Exception:
            pass
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post(
    "/garment",
    response_model=RenderJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def render_garment(
    garment_id: str = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Queue a mannequin render for a single garment (no outfit needed).
    Returns 202 immediately with a job_id.
    Poll GET /render/jobs/{job_id} for status + result.
    """
    garment_path, garment_category = _garment_image_path(db, garment_id, str(current_user.id))

    job_id = str(uuid.uuid4())
    job = RenderJob(
        id=job_id,
        user_id=str(current_user.id),
        outfit_id=None,
        render_type="mannequin",
        status="queued",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(_run_mannequin, job_id, garment_path, garment_category)

    return _job_to_response(job)


@router.post(
    "/mannequin",
    response_model=RenderJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def render_mannequin(
    outfit_id: str = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Queue a mannequin render for the given outfit.

    Returns 202 immediately with a job_id.
    Poll GET /render/jobs/{job_id} for status + result.
    """
    outfit = _get_outfit_or_404(db, outfit_id, str(current_user.id))
    garment_path, garment_category = _primary_garment_path(db, outfit, str(current_user.id))

    job_id = str(uuid.uuid4())
    job = RenderJob(
        id=job_id,
        user_id=str(current_user.id),
        outfit_id=outfit_id,
        render_type="mannequin",
        status="queued",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(_run_mannequin, job_id, garment_path, garment_category)

    return _job_to_response(job)


@router.post(
    "/try-on",
    response_model=RenderJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def render_try_on(
    outfit_id: str = Form(...),
    file: UploadFile = File(..., description="Full-body photo of the person"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Queue a virtual try-on render.

    Accepts a full-body person photo as multipart + the outfit_id as a form field.
    Returns 202 immediately. Poll GET /render/jobs/{job_id} for the result.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    outfit = _get_outfit_or_404(db, outfit_id, str(current_user.id))
    garment_path, garment_category = _primary_garment_path(db, outfit, str(current_user.id))
    person_bytes = await file.read()

    job_id = str(uuid.uuid4())
    job = RenderJob(
        id=job_id,
        user_id=str(current_user.id),
        outfit_id=outfit_id,
        render_type="try_on",
        status="queued",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(_run_try_on, job_id, garment_path, person_bytes, garment_category)

    return _job_to_response(job)


@router.get("/jobs/{job_id}", response_model=RenderJobResponse)
def get_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Poll render job status.

    Returns the job's current status and, once done, the output_image_url.
    Frontend should poll every 2–3 s with a 60 s timeout.
    """
    job = (
        db.query(RenderJob)
        .filter(RenderJob.id == job_id, RenderJob.user_id == str(current_user.id))
        .first()
    )
    if job is None:
        raise HTTPException(status_code=404, detail="Render job not found")

    return _job_to_response(job)


@router.get("/jobs", response_model=list[RenderJobResponse])
def list_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all render jobs for the current user, newest first."""
    jobs = (
        db.query(RenderJob)
        .filter(RenderJob.user_id == str(current_user.id))
        .order_by(RenderJob.created_at.desc())
        .limit(50)
        .all()
    )
    return [_job_to_response(j) for j in jobs]
