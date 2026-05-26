"""
scripts/scrape_jobs.py
======================
Pull live job postings via JobSpy (https://github.com/Bunsly/JobSpy),
embed with BAAI/bge-large-en-v1.5, and upsert into Supabase `jobs`.

Default sources: Indeed, Glassdoor, ZipRecruiter, Google Jobs.
LinkedIn is opt-in via --include-linkedin and is often blocked.

Examples
--------
  backend/.venv/bin/python scripts/scrape_jobs.py \\
      --search "python developer" --search "data engineer" \\
      --location "remote" --results 30

  # Dry run (scrape, embed, but don't insert)
  backend/.venv/bin/python scripts/scrape_jobs.py \\
      --search "ml engineer" --location "san francisco" --dry-run

SUPABASE_URL / SUPABASE_KEY are read from backend/.env (same as the other
migration scripts).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

os.environ.setdefault("HF_HUB_HTTP_TIMEOUT", "300")
os.environ.setdefault("HUGGINGFACE_HUB_VERBOSITY", "warning")

_root = Path(__file__).resolve().parent.parent
load_dotenv(_root / "backend" / ".env")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
HF_TOKEN     = os.environ.get("HF_TOKEN") or None

if not SUPABASE_URL or SUPABASE_URL.startswith("https://your"):
    sys.exit("ERROR: SUPABASE_URL is not set in backend/.env")
if not SUPABASE_KEY or SUPABASE_KEY.startswith("your"):
    sys.exit("ERROR: SUPABASE_KEY is not set in backend/.env")

from jobspy import scrape_jobs
from sentence_transformers import SentenceTransformer
from supabase import create_client

# ── Config ───────────────────────────────────────────────────────────────────

MODEL_NAME    = "BAAI/bge-large-en-v1.5"
BATCH_SIZE    = 32
MAX_CHARS     = 4000
DEFAULT_SITES = ["indeed", "glassdoor", "zip_recruiter", "google"]


# ── Helpers ──────────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Strip HTML, collapse whitespace, and treat pandas' string 'nan' as empty."""
    s = (text or "").strip()
    if s.lower() == "nan":
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _is_number(x) -> bool:
    """True for usable positive numerics. Filters out None and NaN."""
    try:
        return x is not None and float(x) == float(x) and float(x) > 0
    except (TypeError, ValueError):
        return False


def fmt_salary(min_amount, max_amount, currency, interval) -> str | None:
    """Format a salary range into a compact display string.

    Yearly amounts → '$120K-$160K'. Hourly → '$45/hr' or '$45-$60/hr'.
    Returns None when both ends round to 0 (avoids ugly '$0K-$0K').
    """
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
        amt = lo or hi
        return f"{sym}{amt:.0f}/hr"

    # Yearly (default). Suppress if both round down to 0K.
    lo_k = int(lo / 1000) if lo else 0
    hi_k = int(hi / 1000) if hi else 0
    if lo_k == 0 and hi_k == 0:
        return None
    if lo_k and hi_k and lo_k != hi_k:
        return f"{sym}{lo_k}K-{sym}{hi_k}K"
    return f"{sym}{lo_k or hi_k}K"


def parse_args():
    p = argparse.ArgumentParser(
        description="Scrape jobs via JobSpy and upsert them into Supabase.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--search", action="append", required=True,
                   help="Search term (can be repeated).")
    p.add_argument("--location", default="remote",
                   help="Geographic location filter. Default: remote")
    p.add_argument("--results", type=int, default=25,
                   help="Results per search per site. Default: 25")
    p.add_argument("--hours-old", type=int, default=168,
                   help="Only jobs posted in the last N hours. Default: 168 (one week)")
    p.add_argument("--sites", default=",".join(DEFAULT_SITES),
                   help=f"Comma-separated sites. Default: {','.join(DEFAULT_SITES)}")
    p.add_argument("--include-linkedin", action="store_true",
                   help="Add LinkedIn to the site list (often blocked).")
    p.add_argument("--dry-run", action="store_true",
                   help="Scrape and embed but skip the Supabase upsert.")
    return p.parse_args()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    sites = [s.strip() for s in args.sites.split(",") if s.strip()]
    if args.include_linkedin and "linkedin" not in sites:
        sites.append("linkedin")

    print(f"Connecting to Supabase: {SUPABASE_URL[:40]}…")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    print(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME, token=HF_TOKEN)

    seen_ids: set[str] = set()
    all_records: list[dict] = []

    for term in args.search:
        print(f"\n=== Scraping '{term}' @ '{args.location}' (sites={sites}, n={args.results}) ===")
        try:
            df = scrape_jobs(
                site_name=sites,
                search_term=term,
                location=args.location,
                results_wanted=args.results,
                hours_old=args.hours_old,
                country_indeed="USA",
                verbose=1,
            )
        except Exception as exc:
            print(f"  scrape_jobs failed: {exc}")
            continue

        if df is None or df.empty:
            print(f"  0 rows for '{term}'")
            continue

        print(f"  Got {len(df)} rows")

        for _, row in df.iterrows():
            jid = str(row.get("id") or row.get("job_url") or "").strip()
            if not jid or jid in seen_ids:
                continue
            seen_ids.add(jid)

            description = clean_text(str(row.get("description") or ""))
            if len(description) < 50:
                continue

            title    = clean_text(str(row.get("title") or "")) or "Untitled"
            company  = clean_text(str(row.get("company") or "")) or None
            location = clean_text(str(row.get("location") or "")) or None
            job_type = clean_text(str(row.get("job_type") or "")) or None
            site     = clean_text(str(row.get("site") or "")) or "jobspy"

            full_text = " ".join(x for x in [title, company, location, description] if x)[:MAX_CHARS]

            salary = fmt_salary(
                row.get("min_amount"),
                row.get("max_amount"),
                row.get("currency"),
                row.get("interval"),
            )

            all_records.append({
                "source":     f"jobspy:{site}",
                "source_id":  f"jobspy_{site}_{jid}"[:255],
                "title":      title,
                "company":    company,
                "salary":     salary,
                "experience": None,            # JobSpy doesn't surface this
                "work_type":  job_type,
                "skills":     [],              # extracted at query time from full_text
                "full_text":  full_text,
            })

    if not all_records:
        sys.exit("\nNo records to insert.")

    print(f"\nTotal unique jobs to embed: {len(all_records)}")

    if args.dry_run:
        print("\nDRY RUN — first 3 records:")
        for r in all_records[:3]:
            print(f"  [{r['source']}] {r['title']} @ {r['company']} ({r['salary']})")
        print(f"\nWould have embedded + upserted {len(all_records)} rows.")
        return

    print("Embedding + upserting …\n")
    inserted = 0
    errors   = 0
    for batch_start in range(0, len(all_records), BATCH_SIZE):
        batch = all_records[batch_start : batch_start + BATCH_SIZE]
        try:
            embeddings = model.encode(
                [r["full_text"] for r in batch],
                normalize_embeddings=True,
                show_progress_bar=False,
                batch_size=BATCH_SIZE,
            ).tolist()
            rows = [{**r, "embedding": emb} for r, emb in zip(batch, embeddings)]
            supabase.table("jobs").upsert(rows, on_conflict="source_id").execute()
            inserted += len(batch)
            pct = inserted / len(all_records) * 100
            print(f"[{pct:5.1f}%] {inserted}/{len(all_records)} inserted")
        except Exception as exc:
            errors += 1
            print(f"ERROR at batch {batch_start}: {exc}")
            time.sleep(2)

    print(f"\n=== JobSpy ingest complete ===")
    print(f"  Inserted : {inserted}")
    print(f"  Failed   : {len(all_records) - inserted}")
    print(f"  Errors   : {errors}")


if __name__ == "__main__":
    main()
