"""
scripts/scrape_jobs.py
======================
Thin CLI around `app.services.scraper.scrape_and_upsert`. Pulls live job
postings via JobSpy (https://github.com/Bunsly/JobSpy), embeds with
BAAI/bge-large-en-v1.5, and upserts into Supabase `jobs`.

Default sources: Indeed only (most reliable). Add more via --sites; LinkedIn
is opt-in via --include-linkedin and is often blocked.

Examples
--------
  backend/.venv/bin/python scripts/scrape_jobs.py \\
      --search "python developer" --search "data engineer" \\
      --location "remote" --results 30

  # Dry run: derive a search term from a resume file but don't insert
  backend/.venv/bin/python scripts/scrape_jobs.py \\
      --from-text "$(cat /tmp/maya-resume.txt)" --dry-run
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

os.environ.setdefault("HF_HUB_HTTP_TIMEOUT", "300")
os.environ.setdefault("HUGGINGFACE_HUB_VERBOSITY", "warning")

_root = Path(__file__).resolve().parent.parent
load_dotenv(_root / "backend" / ".env")

# Make the backend `app` package importable.
sys.path.insert(0, str(_root / "backend"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
if not SUPABASE_URL or SUPABASE_URL.startswith("https://your"):
    sys.exit("ERROR: SUPABASE_URL is not set in backend/.env")
if not SUPABASE_KEY or SUPABASE_KEY.startswith("your"):
    sys.exit("ERROR: SUPABASE_KEY is not set in backend/.env")

from app.services.scraper import (  # noqa: E402  (env must be set first)
    DEFAULT_SITES,
    extract_query_from_text,
    scrape_and_upsert,
)


def parse_args():
    p = argparse.ArgumentParser(
        description="Scrape jobs via JobSpy and upsert them into Supabase.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--search", action="append", default=[],
                   help="Search term (can be repeated).")
    p.add_argument("--from-text",
                   help="Derive a single search term from this free-text input "
                        "(mutually exclusive with --search).")
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
                   help="Show the resolved search terms but skip scraping + upsert.")
    return p.parse_args()


def main():
    args = parse_args()

    if args.from_text and args.search:
        sys.exit("ERROR: --from-text and --search are mutually exclusive.")

    if args.from_text:
        term = extract_query_from_text(args.from_text)
        if not term:
            sys.exit("ERROR: could not derive a search term from --from-text.")
        terms = [term]
    elif args.search:
        terms = args.search
    else:
        sys.exit("ERROR: provide --search (repeatable) or --from-text.")

    sites = [s.strip() for s in args.sites.split(",") if s.strip()]
    if args.include_linkedin and "linkedin" not in sites:
        sites.append("linkedin")

    if args.dry_run:
        print("DRY RUN — would scrape:")
        for t in terms:
            print(f"  '{t}' @ '{args.location}' | sites={sites} | results={args.results}")
        return

    totals = {"scraped": 0, "inserted": 0, "errors": 0}
    for t in terms:
        print(f"\n=== Scraping '{t}' @ '{args.location}' (sites={sites}, n={args.results}) ===")
        result = scrape_and_upsert(
            search_term=t,
            location=args.location,
            results_wanted=args.results,
            sites=sites,
            hours_old=args.hours_old,
        )
        print(f"  scraped={result['scraped']} deduped={result.get('deduped','-')} "
              f"inserted={result['inserted']} errors={result['errors']}")
        if result.get("error_message"):
            print(f"  error: {result['error_message']}")
        totals["scraped"]  += result["scraped"]
        totals["inserted"] += result["inserted"]
        totals["errors"]   += result["errors"]

    print(f"\n=== JobSpy ingest complete ===")
    print(f"  Scraped  : {totals['scraped']}")
    print(f"  Inserted : {totals['inserted']}")
    print(f"  Errors   : {totals['errors']}")


if __name__ == "__main__":
    main()
