import re

try:
    from num2words import num2words as _num2words  # kept for backwards compat, unused
    _HAS_NUM2WORDS = True
except ImportError:
    _HAS_NUM2WORDS = False


def preprocess_text(text: str) -> str:
    """
    Clean text before embedding. Preserves case and numerics — BGE was
    trained on natural-cased text; lowercasing degrades cosine similarity.
    """
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"\S+@\S+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def sanitize_preview(text: str, max_chars: int = 250) -> str:
    """
    Strip PII from resume text and truncate for safe public display.
    Never expose full_text via API — use this for the preview field.
    """
    text = re.sub(r"\S+@\S+\.\S+", "[email]", text)
    text = re.sub(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", "[phone]", text)
    text = re.sub(r"https?://\S+", "[url]", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


# ── Simple keyword-based skill extractor ──────────────────────────────────────
# Covers the most common skills that appear in resume datasets.
# Can be replaced with a spaCy NER model for higher accuracy.

_SKILL_KEYWORDS: list[str] = [
    # Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "kotlin", "swift", "scala", "r", "matlab", "php", "ruby", "bash", "sql",
    # ML / Data
    "machine learning", "deep learning", "nlp", "computer vision", "pytorch",
    "tensorflow", "keras", "scikit-learn", "pandas", "numpy", "spark", "hadoop",
    "transformers", "bert", "gpt", "llm", "rag", "vector database",
    # Cloud & DevOps
    "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "ci/cd",
    "github actions", "jenkins", "ansible",
    # Web
    "react", "vue", "angular", "next.js", "fastapi", "django", "flask",
    "node.js", "graphql", "rest api",
    # Databases
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "supabase",
    "bigquery", "snowflake",
    # Soft / general
    "agile", "scrum", "leadership", "communication", "project management",
]


def extract_skills(text: str) -> list[str]:
    """Return skill keywords found in *text* (case-insensitive)."""
    text_lower = text.lower()
    return [s for s in _SKILL_KEYWORDS if s in text_lower]


def overlap_skills(text_a: str, text_b: str) -> tuple[list[str], list[str], list[str]]:
    """
    Return (matched, only_in_a, only_in_b) skill lists for two texts.
    Useful for one-to-one comparison and result card skill pills.
    """
    skills_a = set(extract_skills(text_a))
    skills_b = set(extract_skills(text_b))
    matched = sorted(skills_a & skills_b)
    only_a = sorted(skills_a - skills_b)
    only_b = sorted(skills_b - skills_a)
    return matched, only_a, only_b
