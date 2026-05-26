from __future__ import annotations

import time
import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    JobResult,
    MatchRequest,
    OneToOneRequest,
    OneToOneResponse,
    ResumeResult,
)
from app.services.embedder import encode_query, rerank
from app.services.preprocessor import extract_skills, overlap_skills
from app.services.supabase_client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Helper ───────────────────────────────────────────────────────────────────


def _save_eval(
    *,
    supabase,
    query_type: str,
    query_text: str,
    model_name: str,
    reranked: bool,
    result_ids: list[str],
    similarity_scores: list[float],
    rerank_scores: list[float | None],
    elapsed_ms: int,
) -> str | None:
    """Persist an evaluation record and return its UUID (best-effort)."""
    try:
        row = {
            "query_text": query_text[:500],   # cap for storage
            "query_type": query_type,
            "model_name": model_name,
            "reranked": reranked,
            "result_ids": result_ids,
            "similarity_scores": similarity_scores,
            "rerank_scores": [s for s in rerank_scores if s is not None],
            "latency_ms": elapsed_ms,
        }
        res = supabase.table("evaluations").insert(row).execute()
        return str(res.data[0]["id"]) if res.data else None
    except Exception as exc:
        logger.warning("Could not save eval record: %s", exc)
        return None


# ── Routes ───────────────────────────────────────────────────────────────────


@router.post("/resume-jobs")
def match_resume_to_jobs(req: MatchRequest):
    """
    Resume → Jobs
    Upload a resume; get back a ranked list of matching job postings.
    """
    start = time.time()

    try:
        # 1. Encode query
        embedding = encode_query(req.model_name, req.text)

        # 2. Nearest-neighbour search in Supabase (top 50 candidates)
        supabase = get_supabase()
        result = supabase.rpc(
            "match_jobs",
            {"query_embedding": embedding, "match_count": 50},
        ).execute()
        candidates: list[dict] = result.data or []

        if not candidates:
            return {
                "results": [],
                "model_used": req.model_name,
                "reranked": False,
                "elapsed_ms": int((time.time() - start) * 1000),
                "eval_id": None,
            }

        # 3. Optionally rerank with cross-encoder, then trim to top_k.
        #    Either way we always fetch full_text for the kept candidates so
        #    the result loop can extract clean skill keywords for display.
        if req.rerank and candidates:
            ids = [c["id"] for c in candidates]
            ft_res = (
                supabase.table("jobs")
                .select("id, full_text")
                .in_("id", ids)
                .execute()
            )
            ft_map = {str(r["id"]): r["full_text"] for r in (ft_res.data or [])}
            for c in candidates:
                c["full_text"] = ft_map.get(str(c["id"]), "")
            candidates = rerank(req.text, candidates, text_key="full_text", top_k=req.top_k)
        else:
            candidates = candidates[: req.top_k]
            ids = [c["id"] for c in candidates]
            ft_res = (
                supabase.table("jobs")
                .select("id, full_text")
                .in_("id", ids)
                .execute()
            )
            ft_map = {str(r["id"]): r["full_text"] for r in (ft_res.data or [])}
            for c in candidates:
                c["full_text"] = ft_map.get(str(c["id"]), "")

        # 4. Build skill overlap per result.
        #    Prefer skills extracted from the description text (clean,
        #    keyword-list driven); fall back to the noisy stored skills
        #    array only when extraction yields nothing.
        resume_skills = set(extract_skills(req.text))

        results = []
        for c in candidates:
            extracted = set(extract_skills(c.get("full_text", "")))
            stored = set(c.get("skills") or [])
            job_skills = extracted or stored
            matched = sorted(resume_skills & job_skills)
            missing = sorted(job_skills - resume_skills)
            results.append(
                JobResult(
                    job_id=str(c["id"]),
                    similarity=round(float(c["similarity"]), 4),
                    rerank_score=round(float(c["rerank_score"]), 4) if c.get("rerank_score") is not None else None,
                    title=c.get("title") or "",
                    company=c.get("company") or "",
                    salary=c.get("salary") or "",
                    experience=c.get("experience") or "",
                    work_type=c.get("work_type") or "",
                    skills=list(job_skills),
                    matched_skills=matched,
                    missing_skills=missing,
                )
            )

        elapsed_ms = int((time.time() - start) * 1000)

        # 5. Persist eval record (non-blocking best-effort)
        eval_id = _save_eval(
            supabase=supabase,
            query_type="resume_to_jobs",
            query_text=req.text,
            model_name=req.model_name,
            reranked=req.rerank,
            result_ids=[r.job_id for r in results],
            similarity_scores=[r.similarity for r in results],
            rerank_scores=[r.rerank_score for r in results],
            elapsed_ms=elapsed_ms,
        )

        return {
            "results": results,
            "model_used": req.model_name,
            "reranked": req.rerank,
            "elapsed_ms": elapsed_ms,
            "eval_id": eval_id,
        }

    except Exception as exc:
        logger.exception("match_resume_to_jobs error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/job-resumes")
def match_job_to_resumes(req: MatchRequest):
    """
    Job → Resumes
    Submit a job description; get back the most relevant candidate resumes.
    """
    start = time.time()

    try:
        embedding = encode_query(req.model_name, req.text)

        supabase = get_supabase()
        result = supabase.rpc(
            "match_resumes",
            {
                "query_embedding": embedding,
                "match_count": 50,
                "filter_category": None,
            },
        ).execute()
        candidates: list[dict] = result.data or []

        if not candidates:
            return {
                "results": [],
                "model_used": req.model_name,
                "reranked": False,
                "elapsed_ms": int((time.time() - start) * 1000),
                "eval_id": None,
            }

        # Cross-encoder reranking requires full_text
        if req.rerank and candidates:
            ids = [c["id"] for c in candidates]
            ft_res = (
                supabase.table("resumes")
                .select("id, full_text")
                .in_("id", ids)
                .execute()
            )
            ft_map = {str(r["id"]): r["full_text"] for r in (ft_res.data or [])}
            for c in candidates:
                c["full_text"] = ft_map.get(str(c["id"]), "")
            candidates = rerank(req.text, candidates, text_key="full_text", top_k=req.top_k)
        else:
            candidates = candidates[: req.top_k]

        job_skills = set(extract_skills(req.text))

        results = []
        for c in candidates:
            resume_text = c.get("full_text", c.get("preview", ""))
            resume_skills = set(extract_skills(resume_text))
            matched = sorted(job_skills & resume_skills)
            missing = sorted(job_skills - resume_skills)
            results.append(
                ResumeResult(
                    resume_id=str(c["id"]),
                    similarity=round(float(c["similarity"]), 4),
                    rerank_score=round(float(c["rerank_score"]), 4) if c.get("rerank_score") is not None else None,
                    category=c.get("category") or "",
                    preview=c.get("preview") or "",
                    matched_skills=matched,
                    missing_skills=missing,
                )
            )

        elapsed_ms = int((time.time() - start) * 1000)

        eval_id = _save_eval(
            supabase=supabase,
            query_type="job_to_resumes",
            query_text=req.text,
            model_name=req.model_name,
            reranked=req.rerank,
            result_ids=[r.resume_id for r in results],
            similarity_scores=[r.similarity for r in results],
            rerank_scores=[r.rerank_score for r in results],
            elapsed_ms=elapsed_ms,
        )

        return {
            "results": results,
            "model_used": req.model_name,
            "reranked": req.rerank,
            "elapsed_ms": elapsed_ms,
            "eval_id": eval_id,
        }

    except Exception as exc:
        logger.exception("match_job_to_resumes error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/one-to-one", response_model=OneToOneResponse)
def match_one_to_one(req: OneToOneRequest):
    """
    One-to-one
    Compute direct similarity between a single job description and a single resume.
    Returns a score, quality label, and skill overlap breakdown.
    """
    try:
        job_emb = encode_query(req.model_name, req.job_text)
        resume_emb = encode_query(req.model_name, req.resume_text)

        # Both vectors are already L2-normalised, so dot product == cosine similarity
        similarity = float(sum(a * b for a, b in zip(job_emb, resume_emb)))
        similarity = round(max(0.0, min(1.0, similarity)), 4)

        # Quality label (matches frontend labelFor thresholds)
        if similarity >= 0.90:
            quality = "Excellent"
        elif similarity >= 0.80:
            quality = "Very Good"
        elif similarity >= 0.70:
            quality = "Good"
        elif similarity >= 0.55:
            quality = "Fair"
        else:
            quality = "Poor"

        # Skill analysis
        matched, job_only, resume_only = overlap_skills(req.job_text, req.resume_text)

        return OneToOneResponse(
            similarity=similarity,
            quality=quality,
            matched_skills=matched,
            job_skills=list(set(extract_skills(req.job_text))),
            resume_skills=list(set(extract_skills(req.resume_text))),
        )

    except Exception as exc:
        logger.exception("match_one_to_one error")
        raise HTTPException(status_code=500, detail=str(exc))
