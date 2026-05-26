from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import EvalSummary, FeedbackRequest, FeedbackResponse
from app.services.metrics import compute_metrics_from_feedback
from app.services.supabase_client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(req: FeedbackRequest):
    """
    Store user feedback (thumbs-up / thumbs-down / clicked) for one result
    in an evaluation session, then recompute NDCG@5, MRR, P@5 for the whole
    session and persist the updated metrics.
    """
    try:
        supabase = get_supabase()

        # Fetch the evaluation record
        res = (
            supabase.table("evaluations")
            .select("*")
            .eq("id", req.eval_id)
            .single()
            .execute()
        )
        if not res.data:
            raise HTTPException(status_code=404, detail="Evaluation not found")

        record = res.data

        # Merge the new feedback signal
        feedback: dict[str, str] = record.get("user_feedback") or {}
        feedback[req.result_id] = req.action

        # Recompute metrics
        result_ids: list[str] = record.get("result_ids") or []
        metrics = compute_metrics_from_feedback(result_ids, feedback)

        # Persist
        supabase.table("evaluations").update(
            {"user_feedback": feedback, **metrics}
        ).eq("id", req.eval_id).execute()

        return FeedbackResponse(status="ok", metrics=metrics)

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("submit_feedback error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/summary")
def get_eval_summary():
    """
    Return per-model metric averages from the eval_summary database view.
    The frontend Evaluation page consumes this to power the dashboard.
    """
    try:
        supabase = get_supabase()
        res = supabase.table("eval_summary").select("*").execute()
        rows = res.data or []

        # Coerce types in case Supabase returns strings for numeric columns
        summaries = []
        for row in rows:
            summaries.append(
                EvalSummary(
                    model_name=row["model_name"],
                    reranked=bool(row["reranked"]),
                    query_type=row["query_type"],
                    total_queries=int(row["total_queries"]),
                    avg_ndcg5=float(row["avg_ndcg5"] or 0),
                    avg_mrr=float(row["avg_mrr"] or 0),
                    avg_p5=float(row["avg_p5"] or 0),
                    avg_latency_ms=int(row["avg_latency_ms"] or 0),
                )
            )
        return {"models": summaries}

    except Exception as exc:
        logger.exception("get_eval_summary error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/recent")
def get_recent_evals(limit: int = 20):
    """
    Return the most recent raw evaluation records.
    Useful for debugging and monitoring.
    """
    try:
        supabase = get_supabase()
        res = (
            supabase.table("evaluations")
            .select(
                "id, query_type, model_name, reranked, ndcg_at_5, mrr, "
                "precision_at_5, latency_ms, created_at"
            )
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return {"evaluations": res.data or []}

    except Exception as exc:
        logger.exception("get_recent_evals error")
        raise HTTPException(status_code=500, detail=str(exc))
