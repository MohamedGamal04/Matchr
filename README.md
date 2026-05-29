# Matchr — Semantic Resume Screening

Match resumes to jobs (and vice-versa) with a transformer bi-encoder over
pgvector, a cross-encoder reranker, and live job ingest from Indeed via
[JobSpy](https://github.com/Bunsly/JobSpy). FastAPI on the backend, a
vanilla React + Babel single-page app on the frontend, Supabase for storage.

Beyond plain similarity, Matchr adds spaCy-NER-driven skill extraction,
section-aware retrieval (match against a resume's experience/skills/education
separately), a per-match **explainability** endpoint (top matching sentences +
skill gap), and a **metrics dashboard** that aggregates feedback signals.

> **🚀 Live demo:** **https://matchr-sand.vercel.app**
> Backend: [`mohamedgamal04-matchr.hf.space`](https://mohamedgamal04-matchr.hf.space) (Hugging Face Spaces)
> First request after idle waits ~10 s for the Space to wake.

## Architecture

```
                           ┌────────────────────────────────────────────┐
                           │ Frontend (Vanilla React + Babel, no build) │
                           │  match · add-data · landing                │
                           └──────────────┬─────────────────────────────┘
                                          │ fetch()
                                          ▼
┌──────────────────────────────────────────────────────────────────────┐
│ FastAPI backend (app/)                                               │
│                                                                      │
│  /api/health       → liveness + model load status                    │
│  /api/match/...    → resume↔job similarity (bi-encoder + reranker)   │
│  /api/explain/...  → per-match top sentences + skill gap             │
│  /api/eval/...     → feedback signals + aggregated metrics view      │
│  /api/ingest/...   → user-submitted resume / job                     │
│  /api/scrape/...   → live Indeed scrape via JobSpy                   │
└──────────────────────────────────────────────────────────────────────┘
                        │                       │
                        ▼                       ▼
            ┌────────────────────┐   ┌────────────────────────┐
            │ BAAI/bge-large-en  │   │ Supabase (pgvector)    │
            │  + cross-encoder   │   │  resumes / jobs /      │
            │  ms-marco-MiniLM   │   │  evaluations           │
            └────────────────────┘   └────────────────────────┘
```

Embeddings are 1024-dim BGE vectors. Retrieval uses HNSW ANN search on
`vector_cosine_ops`. Top-50 candidates are then reranked with a small
cross-encoder before being cut to `top_k`. With `section_aware: true`, retrieval
runs against per-section resume embeddings (`resume_sections`) and returns the
best-matching section per result instead of a whole-document score.

## Repository layout

```
backend/        FastAPI app, uv-managed Python env, Dockerfile
  app/
    main.py            FastAPI + lifespan + request-logging middleware
    config.py          pydantic-settings (.env)
    models/schemas.py  request/response Pydantic models
    routes/
      health.py        /api/health
      match.py         /api/match/{resume-jobs,job-resumes,one-to-one}
      explain.py       /api/explain/match  (top sentences + skill gap)
      eval.py          /api/eval/{feedback,recent,metrics}
      data.py          /api/ingest/{resume,job}
      scrape.py        /api/scrape/jobs-for-query
    services/
      embedder.py      bi-encoder + cross-encoder (lru_cache)
      preprocessor.py  text cleaning, PII strip, spaCy-NER skill extraction
      section_parser.py  splits resume text into experience/skills/education/…
      nlp_client.py    shared spaCy model loader (lru_cache)
      scraper.py       JobSpy → embed → upsert helper
      supabase_client.py
frontend/       Single-page React app, no build step (Babel in-browser)
  index.html         entry point
  app.jsx            hash routing + Tweaks panel
  landing.jsx        marketing page + Nav
  match.jsx          the actual product surface (incl. Explain panel)
  metrics.jsx        #/metrics dashboard — daily feedback aggregation
  add-data.jsx       user-submitted resume / job ingest
  primitives.jsx     icons, Logo, ScoreBar, Pill, Feedback
  data.jsx           sample resume + sample JD
  styles.css
scripts/        One-shot CLIs (importable from backend.app.services.scraper)
  migrate_resumes.py   load HF dataset, embed, upsert (sample 20/category)
  migrate_jobs.py      load samples/JOB_data_sample.csv, embed, upsert
  scrape_jobs.py       JobSpy CLI (--search, --location, --country, --sites)
samples/        Seed CSVs (gitignored by extension)
supabase/       schema.sql — vector(1024) columns, HNSW indexes, RPC funcs
prototype/      Original Streamlit + pickle version (archived)
```

## Tech choices, briefly

- **Bi-encoder: `BAAI/bge-large-en-v1.5`** (1024-dim). Best open accuracy at
  this size. BGE needs a task-specific prefix on queries only — handled in
  `encode_query`.
- **Cross-encoder: `cross-encoder/ms-marco-MiniLM-L-6-v2`**. Reranks 50 → top_k.
- **pgvector + HNSW** (m=16, ef_construction=64). Sub-100 ms ANN at this scale.
- **uv** for the Python env. `pyproject.toml` + lockfile in `backend/`.
- **No frontend build step.** Babel transpiles JSX in the browser. Fine for a
  portfolio demo; if this ever needs to be production-fast, swap to esbuild.
- **spaCy NER for skills.** `en_core_web_sm` (baked into the image) plus a
  curated alias map + word-boundary regex. Resolves variants like `k8s →
  kubernetes`, `golang → go` independently of NER, and avoids false positives
  on common words.

## Quick start (local)

You'll need: Python ≥ 3.11, `uv`, a Supabase project, a free Hugging Face
token (for downloading model weights, not for inference at runtime).

```bash
# 1. Clone + set up backend env
git clone <this-repo>
cd Resume-Screening/backend
uv sync                        # creates .venv with all deps
cp .env.example .env           # then fill SUPABASE_URL / SUPABASE_KEY / HF_TOKEN

# 2. Apply the DB schema once
#    Open supabase/schema.sql in the Supabase SQL Editor and run it.

# 3. Seed the database (~2 min on CPU)
cd ..
backend/.venv/bin/python scripts/migrate_resumes.py
backend/.venv/bin/python scripts/migrate_jobs.py

# 4. Start the API
cd backend
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Serve the frontend (any static server works)
cd ../frontend
python -m http.server 5500
# Open http://localhost:5500
```

Frontend config lives in [frontend/config.js](frontend/config.js) — set
`window.MATCHR_API` to your backend URL and `window.MATCHR_API_KEY` to the
value of the backend's `API_KEY` env var (or leave `null` for open access).

## Endpoints (key ones)

| Method | Path | Notes |
|---|---|---|
| `POST` | `/api/match/resume-jobs` | Resume → ranked jobs. Supports `sources` filter (pill IDs) and `rerank` toggle. |
| `POST` | `/api/match/job-resumes` | Job → ranked resumes. |
| `POST` | `/api/match/one-to-one` | Single-pair similarity + skill overlap. |
| `POST` | `/api/explain/match` | Why a result matched: top cross-encoder-scored sentences, skill gap, per-section scores. |
| `POST` | `/api/eval/feedback` | Records `{result_id: up/down/clicked}` into the row's `user_feedback` JSONB. |
| `GET`  | `/api/eval/metrics` | Aggregated daily metrics from the `feedback_metrics` view (query counts, latency, up/down/click totals). |
| `POST` | `/api/ingest/resume` | Add a resume — embeds, sanitises preview, inserts. |
| `POST` | `/api/ingest/job` | Add a job posting — embeds, inserts. |
| `POST` | `/api/scrape/jobs-for-query` | Live Indeed scrape via JobSpy. Inputs: `text` (auto-extracts a job title from it), optional `search_term`, `country`, `location`. |

`/api/match/*` also accepts `section_aware: true` to retrieve against per-section
resume embeddings and return a `best_section` per result.

OpenAPI / Swagger UI at `http://localhost:8000/docs`.

## Frontend features

- **Match page** — three tabs (Resume→Jobs, Job→Resumes, One-to-one), top-K
  selector, sort controls, clickable job/company links when the row is from
  JobSpy.
- **Source pills** — control both the result-list filter and the scrape
  destinations. Two pills: `Indeed` (live, scrape + filter) and
  `Sample / User` (filter-only, covers the CSV seed + user submissions).
- **Refresh from Indeed** — pastes the resume → derives a job title →
  scrapes ~25 fresh Indeed rows → embeds → upserts → re-runs the match.
  Country dropdown (USA/UK/Egypt/…) + optional search override.
- **Add data page** (`#/add`) — submit a single resume or job posting
  with category/title metadata.
- **Explain panel** — an "Explain this match" expander on each result card
  calls `/api/explain/match` and shows the top matching sentences, the skill
  gap, and per-section scores. Opening it also records a `clicked` signal.
- **Metrics dashboard** (`#/metrics`) — daily summary cards + table from the
  `feedback_metrics` view: query counts, average latency, thumbs up/down/clicks.
- **Feedback** — thumbs up/down on each result card; signal lands in the
  `evaluations.user_feedback` JSONB column.

## Database schema

`supabase/schema.sql` is the source of truth. Tables:

- `resumes(id, source, source_id, category, preview, full_text, embedding vector(1024), created_at)`
- `jobs(id, source, source_id, title, company, salary, experience, work_type, skills text[], full_text, job_url, company_url, embedding vector(1024), created_at)`
- `evaluations(id, query_text, query_type, model_name, reranked, result_ids uuid[], similarity_scores float[], rerank_scores float[], user_feedback jsonb, latency_ms, created_at)`
- `resume_sections(id, resume_id → resumes, section_type, content, embedding vector(1024), created_at)` — one row per parsed section, used for section-aware retrieval.

RPC functions: `match_resumes(query_embedding, match_count, filter_category)`,
`match_jobs(query_embedding, match_count)`, and
`match_resumes_sectioned(query_embedding, match_count)` (returns `best_section`).

View: `feedback_metrics` — daily aggregation of query counts, latency, and
up/down/click feedback totals, backing `GET /api/eval/metrics`.

`full_text` is never returned through the API — only `preview` (sanitised).

## Scraping notes

JobSpy supports Indeed, Glassdoor, ZipRecruiter, Google Jobs, LinkedIn, and more.
In practice only **Indeed** is reliable from most IPs — the others get
rate-limited / 0-result silently. The UI only exposes Indeed; the CLI
([scripts/scrape_jobs.py](scripts/scrape_jobs.py)) accepts `--sites glassdoor,zip_recruiter,google` if you want to experiment.

LinkedIn is intentionally not wired up — it violates ToS and JobSpy's
scraper for it works only with paid residential proxies.

## Deployment

This repo is already deployed:

- **Backend:** [`mohamedgamal04-matchr.hf.space`](https://mohamedgamal04-matchr.hf.space) — Hugging Face Space, Docker SDK, CPU Basic (free).
- **Frontend:** [`matchr-sand.vercel.app`](https://matchr-sand.vercel.app) — Vercel, static (no build step), root directory set to `frontend/`.

To redeploy your own copy:

**Backend → Hugging Face Spaces (Docker).** The `backend/Dockerfile` bakes
both models and the spaCy `en_core_web_sm` model at build time so cold start is
~10 s instead of minutes. The Space is **backend-only** — HF expects the
`Dockerfile` and a frontmatter `README.md` at its repo root, so deploy the
`backend/` subtree (not the monorepo root):

```bash
git remote add hf https://huggingface.co/spaces/<user>/<space>   # one-time
git subtree split --prefix=backend -b hf-deploy                  # backend/ → root
git push hf hf-deploy:main --force
```

`backend/README.md` carries the required HF YAML frontmatter (`sdk: docker`,
`app_port: 7860`). Set these in the Space settings — `SUPABASE_KEY` and
`API_KEY` as **secrets**, the rest as **variables**:

- `SUPABASE_URL`, `SUPABASE_KEY` (service-role key)
- `API_KEY` — random string; gates `/api/ingest/*` and `/api/scrape/*`, and must
  match the frontend's `MATCHR_API_KEY`
- `CORS_ORIGINS` — your deployed frontend URL, no trailing slash
- `HF_TOKEN` — optional, only needed if you swap in a gated model

**Frontend → Vercel (static).** Import the repo, set **Root Directory** to
`frontend`, **Framework Preset** to "Other", leave Build/Output commands
empty. Before pushing, edit [`frontend/config.js`](frontend/config.js) so
`MATCHR_API` points at the HF Space and `MATCHR_API_KEY` matches the backend's
`API_KEY` secret.

The free HF Spaces tier hibernates after ~48 h idle; the first request after
sleep waits while the container restarts. The frontend shows a "Backend is
warming up" banner. Either accept the cold start, upgrade to "Always-on",
or hit `/api/health` periodically from an external cron.

## License

MIT.
