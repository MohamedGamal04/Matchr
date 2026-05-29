---
title: Matchr
emoji: 🎯
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Matchr Backend

FastAPI app — semantic resume screening with bi-encoder retrieval and cross-encoder reranking.

## Architecture

```
Request
  └─ FastAPI route (match.py)
       ├─ encode_query()       — bi-encoder (SentenceTransformer)
       ├─ supabase.rpc()       — HNSW ANN search (pgvector)
       ├─ rerank()             — cross-encoder (optional, +200ms)
       └─ Response JSON
```

## Setup (local dev)

```bash
cd backend
pip install -r requirements.txt

# copy and fill in your credentials
cp .env.example .env
# edit .env: set SUPABASE_URL and SUPABASE_KEY

uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET  | `/api/health` | Liveness probe |
| GET  | `/api/models` | List available embedding models |
| POST | `/api/match/resume-jobs` | Resume → Jobs matching |
| POST | `/api/match/job-resumes` | Job → Resumes matching |
| POST | `/api/match/one-to-one` | Direct similarity score |
| POST | `/api/eval/feedback` | Submit thumbs up/down |
| GET  | `/api/eval/summary` | Metrics dashboard data |
| GET  | `/api/eval/recent` | Recent evaluation records |

## Deployment to Hugging Face Spaces

1. Create a new Space: https://huggingface.co/new-space  
   → Docker · CPU Basic (free)

2. Upload:
   - `Dockerfile`
   - `requirements.txt`
   - `app/` folder

3. Add secrets in Space settings:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `CORS_ORIGINS` (your Vercel URL)

4. The Space builds automatically (~5–10 min, models are baked in).

## Database setup

Run `supabase/schema.sql` in your Supabase SQL Editor before deploying.

Then populate the database:

```bash
cd scripts
python migrate_resumes.py   # ~15 min on CPU, ~30k resumes
```

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | ✅ | Your Supabase project URL |
| `SUPABASE_KEY` | ✅ | Service-role key (not anon key) |
| `CORS_ORIGINS` | ✅ | Comma-separated allowed origins |
| `HF_TOKEN` | optional | For gated HF models |
| `DEFAULT_MODEL` | optional | Override default bi-encoder |
| `CROSS_ENCODER_MODEL` | optional | Override cross-encoder |

## Security notes

- **Never expose `resumes.full_text` via the API** — only `preview` is returned.  
  The `match_resumes` RPC function deliberately omits `full_text`.
- Use the **service-role key** server-side only; never expose it in the frontend.
- Set `CORS_ORIGINS` to your exact frontend domain in production.
