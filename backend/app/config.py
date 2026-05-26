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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
