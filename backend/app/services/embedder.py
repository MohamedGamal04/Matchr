from __future__ import annotations

import logging
from functools import lru_cache

from sentence_transformers import CrossEncoder, SentenceTransformer

from app.config import settings
from app.services.preprocessor import preprocess_text

logger = logging.getLogger(__name__)

# ── Model loading ─────────────────────────────────────────────────────────────


@lru_cache(maxsize=4)
def get_biencoder(model_name: str) -> SentenceTransformer:
    """Load (and cache) a bi-encoder model by name."""
    logger.info("Loading bi-encoder: %s", model_name)
    return SentenceTransformer(
        model_name,
        token=settings.hf_token or None,
    )


@lru_cache(maxsize=1)
def get_crossencoder() -> CrossEncoder:
    """Load (and cache) the cross-encoder reranker."""
    logger.info("Loading cross-encoder: %s", settings.cross_encoder_model)
    return CrossEncoder(settings.cross_encoder_model, max_length=512)


def preload_models() -> None:
    """
    Called once at startup to warm up both models.
    Avoids cold-start latency on the first real request.
    """
    get_biencoder(settings.default_model)
    get_crossencoder()
    logger.info("Models preloaded.")


# ── Encoding ─────────────────────────────────────────────────────────────────

_BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def encode_query(model_name: str, text: str) -> list[float]:
    """
    Encode a *query* text into a normalised embedding vector.

    BGE models require a task-specific prefix on the query side only
    (not on indexed documents). The prefix is added automatically.
    """
    model = get_biencoder(model_name)
    cleaned = preprocess_text(text)

    if "bge" in model_name.lower():
        cleaned = _BGE_QUERY_PREFIX + cleaned

    embedding = model.encode(cleaned, normalize_embeddings=True)
    return embedding.tolist()


def encode_document(model_name: str, text: str) -> list[float]:
    """
    Encode a *document* (indexed item) into a normalised embedding.
    No query prefix is applied.
    """
    model = get_biencoder(model_name)
    cleaned = preprocess_text(text)
    embedding = model.encode(cleaned, normalize_embeddings=True)
    return embedding.tolist()


def encode_batch_documents(
    model_name: str,
    texts: list[str],
    batch_size: int = 32,
    show_progress: bool = True,
) -> list[list[float]]:
    """Encode a batch of documents. Used by the migration script."""
    model = get_biencoder(model_name)
    cleaned = [preprocess_text(t) for t in texts]
    embeddings = model.encode(
        cleaned,
        normalize_embeddings=True,
        batch_size=batch_size,
        show_progress_bar=show_progress,
    )
    return embeddings.tolist()


# ── Reranking ────────────────────────────────────────────────────────────────


def rerank(
    query: str,
    candidates: list[dict],
    text_key: str = "full_text",
    top_k: int | None = None,
) -> list[dict]:
    """
    Cross-encoder reranking.

    Scores every (query, candidate_text) pair and returns candidates
    sorted by rerank_score descending.  If top_k is given, only that
    many results are returned.

    Parameters
    ----------
    query      : raw query string (not pre-processed)
    candidates : list of dicts; each must have a key named `text_key`
    text_key   : key in each candidate dict that holds the text to score
    top_k      : optional limit on returned results
    """
    if not candidates:
        return candidates

    cross = get_crossencoder()
    pairs = [(query, c.get(text_key, "")[:512]) for c in candidates]
    scores = cross.predict(pairs)

    for i, c in enumerate(candidates):
        c["rerank_score"] = float(scores[i])

    ranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
    return ranked[:top_k] if top_k else ranked
