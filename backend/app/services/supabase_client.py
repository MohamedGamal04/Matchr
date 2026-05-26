from supabase import create_client, Client
from functools import lru_cache
from app.config import settings


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """Return a singleton Supabase client."""
    return create_client(settings.supabase_url, settings.supabase_key)
