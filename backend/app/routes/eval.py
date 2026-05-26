from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import FeedbackRequest, FeedbackResponse
from app.services.supabase_client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(req: FeedbackRequest):
    """
    Record a user feedback signal (thumbs-up / thumbs-down / clicked) for one
    result in an evaluation session. The signal is merged into the
    `user_feedback` JSONB column on the matching evaluations row.
    """
    try:
        supabase = get_supabase()

        res = (
            supabase.table("evaluations")
            .select("user_feedback")
            .eq("id", req.eval_id)
            .single()
            .execute()
        )
        if not res.data:
            raise HTTPException(status_code=404, detail="Evaluation not found")

        feedback: dict[str, str] = res.data.get("user_feedback") or {}
        feedback[req.result_id] = req.action

        supabase.table("evaluations").update(
            {"user_feedback": feedback}
        ).eq("id", req.eval_id).execute()

        return FeedbackResponse(status="ok")

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("submit_feedback error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/recent")
def get_recent_evals(limit: int = 20):
    """
    Return the most recent raw evaluation records — useful for debugging.
    """
    try:
        supabase = get_supabase()
        res = (
            supabase.table("evaluations")
            .select("id, query_type, model_name, reranked, latency_ms, created_at")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return {"evaluations": res.data or []}

    except Exception as exc:
        logger.exception("get_recent_evals error")
        raise HTTPException(status_code=500, detail=str(exc))
