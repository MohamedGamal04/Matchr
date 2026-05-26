"""
scripts/migrate_jobs.py
=======================
Loads samples/JOB_data_sample.csv, embeds each row with BAAI/bge-large-en-v1.5,
and upserts into Supabase `jobs`. Caps at PER_TITLE rows per Job Title so the
demo DB stays small while still covering every role in the sample.

Run from the project root:

    backend/.venv/bin/python scripts/migrate_jobs.py

SUPABASE_URL / SUPABASE_KEY are read from backend/.env (same as migrate_resumes.py).
"""

from __future__ import annotations

import csv
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

from sentence_transformers import SentenceTransformer
from supabase import create_client

# ── Config ───────────────────────────────────────────────────────────────────

MODEL_NAME  = "BAAI/bge-large-en-v1.5"
BATCH_SIZE  = 32
MAX_CHARS   = 4000
PER_TITLE   = 20
CSV_PATH    = _root / "samples" / "JOB_data_sample.csv"

# ── Clients ──────────────────────────────────────────────────────────────────

print(f"Connecting to Supabase: {SUPABASE_URL[:40]}…")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print(f"Loading embedding model: {MODEL_NAME}")
model = SentenceTransformer(MODEL_NAME, token=HF_TOKEN)


# ── Helpers ──────────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_skills(raw: str) -> list[str]:
    """The CSV stores skills as a free-text string — split on commas/newlines."""
    raw = (raw or "").strip()
    if not raw:
        return []
    parts = re.split(r"[,\n;|]+", raw)
    cleaned = [p.strip().strip("'\"") for p in parts]
    return [p for p in cleaned if 1 < len(p) < 50][:15]


def parse_work_type(raw: str) -> str:
    raw = (raw or "").strip()
    return raw if raw else "Unknown"


def encode_batch(texts: list[str]) -> list[list[float]]:
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False,
        batch_size=BATCH_SIZE,
    )
    return embeddings.tolist()


# ── Load CSV and bucket by Job Title ─────────────────────────────────────────

if not CSV_PATH.exists():
    sys.exit(f"ERROR: {CSV_PATH} not found")

print(f"\n=== Reading {CSV_PATH.name} ===")
by_title: dict[str, list[dict]] = {}

with CSV_PATH.open(newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        title = clean_text(row.get("Job Title", ""))
        if not title:
            continue

        bucket = by_title.setdefault(title, [])
        if len(bucket) >= PER_TITLE:
            continue

        role        = clean_text(row.get("Role", ""))
        description = clean_text(row.get("Job Description", ""))
        responsibilities = clean_text(row.get("Responsibilities", ""))
        skills_raw  = row.get("skills", "")

        full_text = " ".join(
            x for x in [title, role, description, responsibilities, skills_raw] if x
        )[:MAX_CHARS]

        bucket.append(
            {
                "source":     "JOB_data_sample.csv",
                "source_id":  f"csv_{row.get('Job Id','').strip()}",
                "title":      title,
                "company":    clean_text(row.get("Company", "")) or None,
                "salary":     clean_text(row.get("Salary Range", "")) or None,
                "experience": clean_text(row.get("Experience", "")) or None,
                "work_type":  parse_work_type(row.get("Work Type", "")),
                "skills":     parse_skills(skills_raw),
                "full_text":  full_text,
            }
        )

all_records: list[dict] = [r for rows in by_title.values() for r in rows]

print(f"Job titles: {len(by_title)} | per-title cap: {PER_TITLE}")
for title, rows in sorted(by_title.items()):
    print(f"  {title:45s} {len(rows):3d}")
print(f"\nTotal to embed + insert: {len(all_records)}")
print("Starting …\n")


# ── Embed and upsert ─────────────────────────────────────────────────────────

inserted = 0
errors   = 0

for batch_start in range(0, len(all_records), BATCH_SIZE):
    batch = all_records[batch_start : batch_start + BATCH_SIZE]
    try:
        embeddings = encode_batch([r["full_text"] for r in batch])
        rows = [{**r, "embedding": emb} for r, emb in zip(batch, embeddings)]
        supabase.table("jobs").upsert(rows, on_conflict="source_id").execute()
        inserted += len(batch)
        pct = inserted / len(all_records) * 100
        print(f"[{pct:5.1f}%] {inserted}/{len(all_records)} inserted")
    except Exception as exc:
        errors += 1
        print(f"ERROR at batch {batch_start}: {exc}")
        time.sleep(2)

print(f"\n=== Jobs migration complete ===")
print(f"  Inserted : {inserted}")
print(f"  Failed   : {len(all_records) - inserted}")
print(f"  Errors   : {errors}   (batches that failed)")
