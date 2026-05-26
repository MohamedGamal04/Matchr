"""
POST /api/scrape/jobs-for-query

Live JobSpy scrape triggered from the match page's "Refresh from Indeed"
button. Synchronous (takes 15-60s). Inserts fresh jobs into Supabase
so the subsequent match request can rank them alongside seed data.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from app.config import settings
from app.models.schemas import ScrapeRequest, ScrapeResponse
from app.services.auth import require_api_key
from app.services.limiter import limiter
from app.services.scraper import extract_query_from_text, scrape_and_upsert

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(require_api_key)])


@router.post("/jobs-for-query", response_model=ScrapeResponse)
@limiter.limit(settings.rate_limit_scrape)
def scrape_jobs_for_query(request: Request, req: ScrapeRequest) -> ScrapeResponse:
    search_term = (req.search_term or "").strip() or extract_query_from_text(req.text)
    if not search_term:
        raise HTTPException(status_code=422, detail="Could not derive a search term from the input text.")

    try:
        result = scrape_and_upsert(
            search_term=search_term,
            location=req.location,
            country=req.country,
            results_wanted=req.results_wanted,
            sites=req.sites or ["indeed"],
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("scrape_jobs_for_query unexpected failure")
        raise HTTPException(status_code=500, detail=str(exc))

    return ScrapeResponse(**result)
