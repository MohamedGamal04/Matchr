# ── Matchr Backend — Hugging Face Spaces Dockerfile ──────────────────────────
#
# Build target : python:3.11-slim  +  uv (package manager)
# Exposed port : 7860 (HF Spaces default)
# Models baked : BAAI/bge-large-en-v1.5  +  cross-encoder/ms-marco-MiniLM-L-6-v2
#
# Deploy steps:
#   1. Create a new HF Space (Docker, CPU Basic)
#   2. Upload this Dockerfile, pyproject.toml, uv.lock, and the app/ folder
#   3. Add secrets: SUPABASE_URL, SUPABASE_KEY, CORS_ORIGINS
#   4. HF will build and start automatically
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# System deps needed by sentence-transformers / tokenizers
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        curl \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy lockfile first — Docker layer cache skips install if unchanged
COPY pyproject.toml uv.lock ./

# Install dependencies from the frozen lockfile (no network lookup)
RUN uv sync --frozen --no-install-project

# Download the en_core_web_sm model (spaCy already installed by uv sync above)
RUN uv run python -m spacy download en_core_web_sm

# Copy application code
COPY ./app ./app

# ── Bake models into the image at build time ──────────────────────────────────
# This avoids downloading ~1.5 GB on every cold start.
ARG HF_TOKEN=""
ENV HF_TOKEN=${HF_TOKEN}
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface
ENV SENTENCE_TRANSFORMERS_HOME=/app/.cache/sentence_transformers

RUN uv run python -c "\
from sentence_transformers import SentenceTransformer, CrossEncoder; \
import os; \
token = os.environ.get('HF_TOKEN') or None; \
print('Downloading bi-encoder …'); \
SentenceTransformer('BAAI/bge-large-en-v1.5', token=token); \
print('Downloading cross-encoder …'); \
CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2'); \
print('Done.')"

# ── Runtime config ────────────────────────────────────────────────────────────
# HF Spaces injects secrets as environment variables at runtime.
ENV SUPABASE_URL="https://your-project-ref.supabase.co"
ENV SUPABASE_KEY="your-service-role-key-here"
ENV CORS_ORIGINS="*"
ENV DEFAULT_MODEL="BAAI/bge-large-en-v1.5"
ENV CROSS_ENCODER_MODEL="cross-encoder/ms-marco-MiniLM-L-6-v2"

EXPOSE 7860

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

CMD ["./entrypoint.sh"]
