#!/bin/bash
# Matchr Backend — entrypoint for HF Spaces Docker container
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-7860}"
WORKERS="${WORKERS:-1}"
LOG_LEVEL="${LOG_LEVEL:-info}"
echo "Starting Matchr API on ${HOST}:${PORT} (workers=${WORKERS})"
exec uv run uvicorn app.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --log-level "$LOG_LEVEL"
