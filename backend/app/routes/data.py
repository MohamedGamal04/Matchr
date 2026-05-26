"""
User-submitted resume / job ingest endpoints.

POST /api/ingest/resume — add a single resume to the database
POST /api/ingest/job    — add a single job posting to the database

Each endpoint:
  • validates payload via Pydantic
  • embeds full_text with the default bi-encoder (BGE)
  • sanitises a 250-char preview for resumes
  • inserts a new row into Supabase (`source = "user_submission"`)
"""

from __future__ import annotations

import logging
import re
import uuid

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models.schemas import (
    IngestJobRequest,
    IngestResponse,
    IngestResumeRequest,
)
from app.services.embedder import encode_document
from app.services.preprocessor import sanitize_preview
from app.services.supabase_client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_TEXT_CHARS = 4000  # mirror migrate_*.py — keep stored full_text bounded


def _clean(text: str) -> str:
    """Strip HTML tags and collapse whitespace."""
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


@router.post("/resume", response_model=IngestResponse, status_code=201)
def ingest_resume(req: IngestResumeRequest) -> IngestResponse:
    full_text = _clean(req.full_text)[:MAX_TEXT_CHARS]
    if len(full_text) < 50:
        raise HTTPException(status_code=422, detail="full_text too short after cleaning")

    embedding = encode_document(settings.default_model, full_text)
    source_id = f"user_{uuid.uuid4().hex}"

    row = {
        "source":    "user_submission",
        "source_id": source_id,
        "category":  req.category.strip(),
        "full_text": full_text,
        "preview":   sanitize_preview(full_text),
        "embedding": embedding,
    }

    try:
        result = get_supabase().table("resumes").insert(row).execute()
    except Exception as exc:
        logger.exception("Supabase insert failed for resume %s", source_id)
        raise HTTPException(status_code=500, detail=f"Database insert failed: {exc}")

    inserted_id = result.data[0]["id"] if result.data else source_id
    return IngestResponse(
        id=str(inserted_id),
        source_id=source_id,
        message=f"Resume added to {req.category.strip()} category",
    )


@router.post("/job", response_model=IngestResponse, status_code=201)
def ingest_job(req: IngestJobRequest) -> IngestResponse:
    full_text = _clean(req.full_text)[:MAX_TEXT_CHARS]
    if len(full_text) < 50:
        raise HTTPException(status_code=422, detail="full_text too short after cleaning")

    embedding = encode_document(settings.default_model, full_text)
    source_id = f"user_{uuid.uuid4().hex}"

    skills = [s.strip() for s in req.skills if s and s.strip()][:20]

    row = {
        "source":     "user_submission",
        "source_id":  source_id,
        "title":      req.title.strip(),
        "company":    (req.company or "").strip() or None,
        "salary":     (req.salary or "").strip() or None,
        "experience": (req.experience or "").strip() or None,
        "work_type":  (req.work_type or "").strip() or None,
        "skills":     skills,
        "full_text":  full_text,
        "embedding":  embedding,
    }

    try:
        result = get_supabase().table("jobs").insert(row).execute()
    except Exception as exc:
        logger.exception("Supabase insert failed for job %s", source_id)
        raise HTTPException(status_code=500, detail=f"Database insert failed: {exc}")

    inserted_id = result.data[0]["id"] if result.data else source_id
    return IngestResponse(
        id=str(inserted_id),
        source_id=source_id,
        message=f"Job '{req.title.strip()}' added",
    )
