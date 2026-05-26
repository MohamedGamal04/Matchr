from fastapi import APIRouter
from app.config import settings

router = APIRouter()


@router.get("/health")
def health_check():
    """Liveness probe — returns 200 when the server is up."""
    return {"status": "ok", "models_loaded": True}


@router.get("/models")
def list_models():
    """Return the available bi-encoder models and which one is the default."""
    return {
        "models": [
            {
                "id": "BAAI/bge-large-en-v1.5",
                "dims": 1024,
                "recommended": True,
                "description": "Best accuracy — BAAI BGE large English",
            },
        ],
        "default": settings.default_model,
        "cross_encoder": settings.cross_encoder_model,
    }
