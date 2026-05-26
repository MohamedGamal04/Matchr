"""
JobSpy ingest helper, shared by the CLI script (`scripts/scrape_jobs.py`)
and the HTTP endpoint (`/api/scrape/jobs-for-query`).

Encapsulates: search-term extraction from free text, JobSpy invocation,
salary formatting, and the embed + upsert into Supabase. The `jobspy`
import is lazy so the rest of the app still runs if it's not installed.
"""

from __future__ import annotations

import logging
import re
from typing import Iterable

from app.config import settings
from app.services.embedder import encode_batch_documents
from app.services.preprocessor import extract_skills
from app.services.supabase_client import get_supabase

logger = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────────────

DEFAULT_SITES   = ("indeed",)
DEFAULT_RESULTS = 25
MAX_CHARS       = 4000
BATCH_SIZE      = 32

_ROLE_KEYWORDS = [
    "engineer", "developer", "analyst", "manager", "scientist", "designer",
    "specialist", "architect", "lead", "consultant", "administrator",
    "researcher", "director", "officer",
]


# ── Public API ───────────────────────────────────────────────────────────────

_TITLE_SEPARATORS = ["—", "–", " - ", " | ", ":", ","]


def extract_query_from_text(text: str, max_len: int = 80) -> str:
    """
    Pick a reasonable job-board search query from a resume or job description.

    Strategy:
      1. Scan the first 12 lines for one containing a role keyword.
      2. Strip name-like prefix on that line by splitting on common separators
         ("—", "–", " - ", " | ", ":", ",") and keeping the longest part that
         still contains a role keyword. So "Maya Chen — Senior Machine
         Learning Engineer" becomes "Senior Machine Learning Engineer".
      3. Fall back to the top 3 keywords from `extract_skills`.
      4. Last resort: first `max_len` chars of cleaned text.
    """
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    if not cleaned:
        return ""

    for raw in (text or "").split("\n")[:12]:
        line = raw.strip("•- *\t ").strip()
        if not (5 < len(line) < 100 and any(k in line.lower() for k in _ROLE_KEYWORDS)):
            continue
        for sep in _TITLE_SEPARATORS:
            if sep in line:
                parts = [p.strip() for p in line.split(sep) if p.strip()]
                role_parts = [p for p in parts if any(k in p.lower() for k in _ROLE_KEYWORDS)]
                if role_parts:
                    line = max(role_parts, key=len)
                    break
        return line[:max_len]

    skills = extract_skills(cleaned)[:3]
    if skills:
        return " ".join(skills)[:max_len]

    return cleaned[:max_len]


def scrape_and_upsert(
    *,
    search_term: str,
    location: str = "remote",
    country: str | None = None,
    results_wanted: int = DEFAULT_RESULTS,
    sites: Iterable[str] = DEFAULT_SITES,
    hours_old: int = 168,
) -> dict:
    """Scrape JobSpy → embed → upsert into `jobs`. Returns a summary dict.

    `country` is forwarded to JobSpy as `country_indeed` (Indeed-only param;
    the other sites ignore it). Defaults to 'USA' when None.
    """
    try:
        from jobspy import scrape_jobs as _scrape_jobs
    except ImportError:
        raise RuntimeError(
            "python-jobspy is not installed. Run `uv add python-jobspy` (or "
            "add it to the runtime image)."
        )

    if not search_term.strip():
        raise ValueError("search_term cannot be empty")

    site_list = [s.strip() for s in sites if s.strip()]
    indeed_country = (country or "USA").strip() or "USA"
    logger.info(
        "scrape_and_upsert: term=%r location=%r country=%r results=%d sites=%s",
        search_term, location, indeed_country, results_wanted, site_list,
    )

    try:
        df = _scrape_jobs(
            site_name=site_list,
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_old,
            country_indeed=indeed_country,
            verbose=0,
        )
    except Exception as exc:
        logger.exception("JobSpy scrape failed")
        return {
            "search_term": search_term, "scraped": 0, "inserted": 0,
            "errors": 1, "error_message": str(exc),
        }

    if df is None or df.empty:
        return {
            "search_term": search_term, "scraped": 0, "inserted": 0,
            "errors": 0, "by_site": {s: 0 for s in site_list},
        }

    # Per-site counts before dedup, useful for the UI banner.
    by_site: dict[str, int] = {s: 0 for s in site_list}
    if "site" in df.columns:
        for s, count in df["site"].fillna("unknown").value_counts().items():
            by_site[str(s)] = int(count)

    records, seen = [], set()
    for _, row in df.iterrows():
        jid = str(row.get("id") or row.get("job_url") or "").strip()
        if not jid or jid in seen:
            continue
        seen.add(jid)

        description = _clean_text(str(row.get("description") or ""))
        if len(description) < 50:
            continue

        title    = _clean_text(str(row.get("title") or "")) or "Untitled"
        company  = _clean_text(str(row.get("company") or "")) or None
        location_str = _clean_text(str(row.get("location") or "")) or None
        job_type = _clean_text(str(row.get("job_type") or "")) or None
        site     = _clean_text(str(row.get("site") or "")) or "jobspy"

        full_text = " ".join(
            x for x in [title, company, location_str, description] if x
        )[:MAX_CHARS]

        records.append({
            "source":      f"jobspy:{site}",
            "source_id":   f"jobspy_{site}_{jid}"[:255],
            "title":       title,
            "company":     company,
            "salary":      _fmt_salary(
                row.get("min_amount"), row.get("max_amount"),
                row.get("currency"), row.get("interval"),
            ),
            "experience":  None,
            "work_type":   job_type,
            "skills":      [],
            "full_text":   full_text,
            "job_url":     _str_or_none(row.get("job_url") or row.get("job_url_direct")),
            "company_url": _str_or_none(row.get("company_url")),
        })

    if not records:
        return {
            "search_term": search_term,
            "scraped": int(len(df)),
            "inserted": 0,
            "errors": 0,
            "by_site": by_site,
        }

    supabase = get_supabase()
    inserted = 0
    errors   = 0
    for batch_start in range(0, len(records), BATCH_SIZE):
        batch = records[batch_start : batch_start + BATCH_SIZE]
        try:
            embeddings = encode_batch_documents(
                settings.default_model,
                [r["full_text"] for r in batch],
                batch_size=BATCH_SIZE,
                show_progress=False,
            )
            rows = [{**r, "embedding": e} for r, e in zip(batch, embeddings)]
            supabase.table("jobs").upsert(rows, on_conflict="source_id").execute()
            inserted += len(batch)
        except Exception as exc:
            logger.exception("Supabase upsert batch failed")
            errors += 1

    return {
        "search_term": search_term,
        "scraped":     int(len(df)),
        "deduped":     len(records),
        "inserted":    inserted,
        "errors":      errors,
        "by_site":     by_site,
    }


# ── Internal helpers ─────────────────────────────────────────────────────────

def _clean_text(text: str) -> str:
    s = (text or "").strip()
    if s.lower() == "nan":
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _str_or_none(x) -> str | None:
    if x is None:
        return None
    s = str(x).strip()
    if not s or s.lower() == "nan":
        return None
    return s


def _is_number(x) -> bool:
    try:
        return x is not None and float(x) == float(x) and float(x) > 0
    except (TypeError, ValueError):
        return False


def _fmt_salary(min_amount, max_amount, currency, interval) -> str | None:
    lo = float(min_amount) if _is_number(min_amount) else None
    hi = float(max_amount) if _is_number(max_amount) else None
    if lo is None and hi is None:
        return None

    cur = str(currency).strip().upper() if isinstance(currency, str) and currency.strip() else "USD"
    sym = "$" if cur in {"USD", "$"} else f"{cur} "
    iv = str(interval or "").strip().lower()

    if iv == "hourly":
        if lo and hi and lo != hi:
            return f"{sym}{lo:.0f}-{sym}{hi:.0f}/hr"
        return f"{sym}{(lo or hi):.0f}/hr"

    lo_k = int(lo / 1000) if lo else 0
    hi_k = int(hi / 1000) if hi else 0
    if lo_k == 0 and hi_k == 0:
        return None
    if lo_k and hi_k and lo_k != hi_k:
        return f"{sym}{lo_k}K-{sym}{hi_k}K"
    return f"{sym}{lo_k or hi_k}K"
