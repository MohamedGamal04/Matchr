from functools import lru_cache


@lru_cache(maxsize=1)
def get_nlp():
    """Load en_core_web_sm once per process. Returns None if model not installed."""
    try:
        import spacy
        return spacy.load("en_core_web_sm")
    except (OSError, ImportError):
        return None
