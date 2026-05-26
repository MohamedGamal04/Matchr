from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase
    supabase_url: str = "https://your-project-ref.supabase.co"
    supabase_key: str = "your-service-role-key-here"

    # Models
    default_model: str = "BAAI/bge-large-en-v1.5"
    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # CORS — comma-separated in prod: "https://matchr.vercel.app,https://matchr.com"
    cors_origins: str = "*"

    # Optional
    hf_token: str | None = None

    # Gates the mutating endpoints (/api/ingest/*, /api/scrape/*).
    # Unset → endpoints are open (local dev). Set → clients must send
    # `X-API-Key: <value>` header.
    api_key: str | None = None

    # Rate-limit defaults (slowapi syntax). Override per env if needed.
    rate_limit_match:  str = "20/minute"
    rate_limit_scrape: str = "3/minute"
    rate_limit_ingest: str = "10/minute"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
