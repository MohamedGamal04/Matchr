"""
Lightweight X-API-Key gate for the mutating endpoints (/api/ingest/*,
/api/scrape/*). Applied as a FastAPI dependency on the affected routers.

Behaviour:
- `settings.api_key` unset (None or empty) → gate is OPEN. Useful for
  local dev where you don't want to fuss with headers.
- `settings.api_key` set → request must include matching `X-API-Key`
  header, otherwise 401.

Read endpoints (/api/match/*, /api/health, /api/eval/*) intentionally
stay open — they're rate-limited via slowapi and don't write data.
"""

from fastapi import Header, HTTPException, status

from app.config import settings


async def require_api_key(x_api_key: str | None = Header(default=None)):
    if not settings.api_key:
        return  # open mode — no gate configured
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header",
        )
