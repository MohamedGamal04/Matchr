from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models.schemas import ExplainRequest, ExplainResponse, MatchedSpan
from app.services.embedder import encode_query, get_crossencoder
from app.services.nlp_client import get_nlp
from app.services.preprocessor import extract_skills
from app.services.supabase_client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/match", response_model=ExplainResponse)
def explain_match(req: ExplainRequest):
    """
    Explain why a job/resume scored highly against a query.

    Returns the top 3 matched sentence pairs (cross-encoder scored),
    a skill gap analysis, and per-section similarity scores (resumes only).
    """
    supabase = get_supabase()

    table = "jobs" if req.result_type == "job" else "resumes"
    res = (
        supabase.table(table)
        .select("full_text")
        .eq("id", req.result_id)
        .single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail=f"{req.result_type} not found")

    full_text: str = res.data.get("full_text") or ""
    if not full_text.strip():
        raise HTTPException(status_code=422, detail="Document has no text content")

    nlp = get_nlp()
    if nlp is None:
        query_sents = [s.strip() for s in req.query_text.split(". ") if s.strip()]
        doc_sents   = [s.strip() for s in full_text[:5000].split(". ") if s.strip()]
    else:
        query_sents = [s.text.strip() for s in nlp(req.query_text).sents if s.text.strip()]
        doc_sents   = [s.text.strip() for s in nlp(full_text[:5000]).sents if s.text.strip()]

    if not query_sents:
        query_sents = [req.query_text[:500]]
    if not doc_sents:
        doc_sents = [full_text[:500]]

    # Cap sentence counts — only the top-3 pairs are returned, and an
    # unbounded |query|×|doc| pair set could overwhelm the cross-encoder.
    query_sents = query_sents[:10]
    doc_sents = doc_sents[:100]

    cross = get_crossencoder()
    pairs = [(qs, ds) for qs in query_sents for ds in doc_sents]
    raw_scores = cross.predict(pairs)

    scores = list(raw_scores) if hasattr(raw_scores, "__iter__") else [raw_scores]
    if len(scores) < len(pairs):
        logger.warning(
            "Cross-encoder returned %d scores for %d pairs; padding with zeros",
            len(scores), len(pairs),
        )
        scores.extend([0.0] * (len(pairs) - len(scores)))

    indexed = sorted(enumerate(pairs), key=lambda x: scores[x[0]], reverse=True)
    matched_spans = [
        MatchedSpan(
            query_sentence=pairs[i][0],
            doc_sentence=pairs[i][1],
            score=round(float(scores[i]), 4),
        )
        for i, _ in indexed[:3]
    ]

    query_skills = set(extract_skills(req.query_text))
    doc_skills   = set(extract_skills(full_text))
    skill_analysis = {
        "matched": sorted(query_skills & doc_skills),
        "missing": sorted(query_skills - doc_skills),
    }

    section_scores: dict[str, float] = {}
    if req.result_type == "resume":
        query_emb = encode_query(settings.default_model, req.query_text)
        sec_res = (
            supabase.table("resume_sections")
            .select("section_type, embedding")
            .eq("resume_id", req.result_id)
            .execute()
        )
        for row in (sec_res.data or []):
            emb = row.get("embedding")
            if emb and len(emb) == len(query_emb):
                sim = float(sum(a * b for a, b in zip(query_emb, emb)))
                section_scores[row["section_type"]] = round(max(0.0, min(1.0, sim)), 4)
            elif emb:
                logger.debug(
                    "Skipping section %s: embedding dim %d != query dim %d",
                    row.get("section_type"), len(emb), len(query_emb),
                )

    return ExplainResponse(
        matched_spans=matched_spans,
        skill_analysis=skill_analysis,
        section_scores=section_scores,
    )
