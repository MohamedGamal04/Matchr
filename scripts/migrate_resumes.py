"""
scripts/migrate_resumes.py
==========================
One-time data migration: loads two free resume datasets from Hugging Face,
embeds them with BAAI/bge-large-en-v1.5, and inserts them into Supabase.

Datasets (no Kaggle account needed):
  • opensporks/resumes   — 2,484 labelled resumes
  • sid1877/Resume-dataset-2024  — 32,500 synthetic resumes

Run locally BEFORE deploying the backend:

    cd /path/to/project
    pip install datasets sentence-transformers supabase python-dotenv num2words
    python scripts/migrate_resumes.py

Set SUPABASE_URL and SUPABASE_KEY in backend/.env (or export them to the
shell environment) before running.
"""

from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# ── Increase HuggingFace timeouts BEFORE importing datasets/huggingface_hub ──
os.environ.setdefault("HF_HUB_HTTP_TIMEOUT", "300")   # 5 min per request
os.environ.setdefault("HF_DATASETS_TIMEOUT", "300")
os.environ.setdefault("HUGGINGFACE_HUB_VERBOSITY", "warning")

# Load backend/.env so we pick up SUPABASE_URL / SUPABASE_KEY
_env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
load_dotenv(_env_path)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
HF_TOKEN     = os.environ.get("HF_TOKEN", "") or None

if not SUPABASE_URL or SUPABASE_URL.startswith("https://your"):
    sys.exit(
        "ERROR: SUPABASE_URL is not set. "
        "Edit backend/.env and add your real project URL."
    )
if not SUPABASE_KEY or SUPABASE_KEY.startswith("your"):
    sys.exit(
        "ERROR: SUPABASE_KEY is not set. "
        "Edit backend/.env and add your service-role key."
    )

from datasets import load_dataset
from sentence_transformers import SentenceTransformer
from supabase import create_client

# ── Config ───────────────────────────────────────────────────────────────────

MODEL_NAME    = "BAAI/bge-large-en-v1.5"
BATCH_SIZE    = 32
MAX_CHARS     = 4000    # max chars of full_text stored
PREVIEW_CHARS = 250     # snippet shown in UI (PII-stripped)
PER_CATEGORY  = 20      # sample cap — keeps the demo DB small

# ── Clients ───────────────────────────────────────────────────────────────────

print(f"Connecting to Supabase: {SUPABASE_URL[:40]}…")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print(f"Loading embedding model: {MODEL_NAME}")
model = SentenceTransformer(MODEL_NAME, token=HF_TOKEN)


# ── Text utilities ────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Strip HTML tags and normalise whitespace."""
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def sanitize_preview(text: str) -> str:
    """Remove obvious PII and truncate to PREVIEW_CHARS."""
    text = re.sub(r"\S+@\S+\.\S+", "[email]", text)
    text = re.sub(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", "[phone]", text)
    text = re.sub(r"https?://\S+", "[url]", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:PREVIEW_CHARS]


# ── Embedding ─────────────────────────────────────────────────────────────────

def encode_batch(texts: list[str]) -> list[list[float]]:
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False,
        batch_size=BATCH_SIZE,
    )
    return embeddings.tolist()


# ── Dataset loader ────────────────────────────────────────────────────────────

def load_with_retry(name, split="train", retries=5):
    for attempt in range(1, retries + 1):
        try:
            return load_dataset(name, split=split)
        except Exception as e:
            if attempt == retries:
                raise
            wait = 10 * attempt
            print(f"  Attempt {attempt} failed ({e.__class__.__name__}). Retrying in {wait}s…")
            time.sleep(wait)


# ── Dataset: sid1877/Resume-dataset-2024 (32,480 resumes) ────────────────────
# opensporks/resumes is skipped — it stores PDFs that fail to decode reliably.

print("\n=== Loading sid1877/Resume-dataset-2024 (≈32,500 resumes) ===")
ds = load_with_retry("sid1877/Resume-dataset-2024")

seen_fingerprints: set[str] = set()
by_category: dict[str, list[dict]] = {}

for i, row in enumerate(ds):
    text = clean_text(str(row.get("Resume_test", "")))
    if len(text) < 50:
        continue
    fp = text[:80]
    if fp in seen_fingerprints:
        continue
    seen_fingerprints.add(fp)

    instruction = str(row.get("instruction", ""))
    cat_match = re.search(r"for a (.+?) Job", instruction, re.IGNORECASE)
    category = cat_match.group(1).strip() if cat_match else "Unknown"

    bucket = by_category.setdefault(category, [])
    if len(bucket) >= PER_CATEGORY:
        continue

    bucket.append(
        {
            "source":    "sid1877/Resume-dataset-2024",
            "source_id": f"sid1877_{i}",
            "category":  category,
            "full_text": text[:MAX_CHARS],
            "preview":   sanitize_preview(text),
        }
    )

all_records: list[dict] = [r for rows in by_category.values() for r in rows]

print(f"Categories: {len(by_category)} | per-category cap: {PER_CATEGORY}")
for cat, rows in sorted(by_category.items()):
    print(f"  {cat:35s} {len(rows):3d}")
print(f"\nTotal to embed + insert: {len(all_records)}")
print("Starting (~1–2 min on CPU) …\n")

# ── Embed and upsert ──────────────────────────────────────────────────────────
# Uses upsert (on_conflict=source_id) so re-runs are safe without per-row checks.

inserted = 0
errors   = 0

for batch_start in range(0, len(all_records), BATCH_SIZE):
    batch = all_records[batch_start : batch_start + BATCH_SIZE]
    try:
        embeddings = encode_batch([r["full_text"] for r in batch])
        rows = [{**r, "embedding": emb} for r, emb in zip(batch, embeddings)]
        supabase.table("resumes").upsert(rows, on_conflict="source_id").execute()
        inserted += len(batch)
        pct = inserted / len(all_records) * 100
        print(f"[{pct:5.1f}%] {inserted}/{len(all_records)} inserted")
    except Exception as exc:
        errors += 1
        print(f"ERROR at batch {batch_start}: {exc}")
        time.sleep(2)

print(f"\n=== Migration complete ===")
print(f"  Inserted : {inserted}")
print(f"  Failed   : {len(all_records) - inserted}")
print(f"  Errors   : {errors}   (batches that failed)")
