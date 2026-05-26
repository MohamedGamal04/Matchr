import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import data, eval, health, match
from app.services.embedder import preload_models

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan: warm-up models at startup ──────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading bi-encoder and cross-encoder into memory …")
    preload_models()
    logger.info("Models ready. Server accepting requests.")
    yield
    logger.info("Shutting down.")


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Matchr API",
    description="Semantic resume screening — bi-encoder retrieval + cross-encoder reranking.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS ─────────────────────────────────────────────────────────────────────

_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request/response logging ─────────────────────────────────────────────────

_access_logger = logging.getLogger("matchr.access")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = (time.perf_counter() - start) * 1000
        _access_logger.exception(
            "%s %s → 500 (%.1fms) [unhandled]",
            request.method, request.url.path, elapsed_ms,
        )
        raise

    elapsed_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.1f}"

    msg = "%s %s → %d (%.1fms)"
    args = (request.method, request.url.path, response.status_code, elapsed_ms)
    if response.status_code >= 500:
        _access_logger.error(msg, *args)
    elif response.status_code >= 400:
        _access_logger.warning(msg, *args)
    else:
        _access_logger.info(msg, *args)

    return response


# ── Routes ───────────────────────────────────────────────────────────────────

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(match.router,  prefix="/api/match", tags=["Match"])
app.include_router(eval.router,   prefix="/api/eval",  tags=["Evaluation"])
app.include_router(data.router,   prefix="/api/ingest", tags=["Ingest"])


@app.get("/", tags=["Root"])
def root():
    return {
        "service": "Matchr API",
        "docs": "/docs",
        "health": "/api/health",
    }
