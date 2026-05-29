import re

from app.services.nlp_client import get_nlp

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


# ── spaCy NER + alias taxonomy + word-boundary skill extractor ────────────────

# Alias map: lowercase variant → canonical skill name (~100 key mappings)
_ALIAS_MAP: dict[str, str] = {
    # JavaScript / TypeScript
    "js":                    "javascript",
    "node.js":               "javascript",
    "nodejs":                "javascript",
    "node js":               "javascript",
    "ecmascript":            "javascript",
    "es6":                   "javascript",
    "vanilla js":            "javascript",
    "ts":                    "typescript",
    "reactjs":               "react",
    "react.js":              "react",
    "react js":              "react",
    "react native":          "react",
    "vuejs":                 "vue",
    "vue.js":                "vue",
    "vue js":                "vue",
    "angular.js":            "angular",
    "angularjs":             "angular",
    "nextjs":                "next.js",
    "next js":               "next.js",
    "express.js":            "node.js",
    # Python
    "py":                    "python",
    "python3":               "python",
    # ML / AI
    "sklearn":               "scikit-learn",
    "scikit learn":          "scikit-learn",
    "tf":                    "tensorflow",
    "tf2":                   "tensorflow",
    "huggingface":           "transformers",
    "hugging face":          "transformers",
    "ml":                    "machine learning",
    "dl":                    "deep learning",
    "cv":                    "computer vision",
    "llms":                  "llm",
    "large language model":  "llm",
    "large language models": "llm",
    "vector db":             "vector database",
    "vector store":          "vector database",
    "vectordb":              "vector database",
    "retrieval augmented":   "rag",
    # Cloud
    "amazon web services":   "aws",
    "google cloud":          "gcp",
    "google cloud platform": "gcp",
    "microsoft azure":       "azure",
    # DevOps
    "k8s":                   "kubernetes",
    "k8":                    "kubernetes",
    "kube":                  "kubernetes",
    "kubectl":               "kubernetes",
    "iac":                   "terraform",
    "gh actions":            "github actions",
    "github action":         "github actions",
    # Databases
    "postgres":              "postgresql",
    "psql":                  "postgresql",
    "pg":                    "postgresql",
    "mongo":                 "mongodb",
    "mongo db":              "mongodb",
    "elastic":               "elasticsearch",
    "elastic search":        "elasticsearch",
    "bq":                    "bigquery",
    # Languages
    "golang":                "go",
    "golang lang":           "go",
    "rb":                    "ruby",
    "rails":                 "ruby",
    "ruby on rails":         "ruby",
    "rust lang":             "rust",
    "csharp":                "c#",
    "c sharp":               "c#",
    "dotnet":                "c#",
    ".net":                  "c#",
    "asp.net":               "c#",
    "cpp":                   "c++",
    "c plus plus":           "c++",
    "cplusplus":             "c++",
    "bash scripting":        "bash",
    "shell scripting":       "bash",
    "shell script":          "bash",
    # Web
    "graphql api":           "graphql",
    "restful":               "rest api",
    "restful api":           "rest api",
    "fast api":              "fastapi",
    # Data
    "hadoop mapreduce":      "hadoop",
    "apache spark":          "spark",
    "pyspark":               "spark",
    # Soft skills
    "agile methodology":     "agile",
    "agile development":     "agile",
    "scrum master":          "scrum",
    "pm":                    "project management",
}

# Canonical skill list — word-boundary regex applied against all of these
_CANONICAL_SKILLS: list[str] = [
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


def _make_skill_pattern(skill: str) -> re.Pattern:
    """Word-boundary pattern that handles special chars (c++, c#, ci/cd, next.js)."""
    escaped = re.escape(skill)
    return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", re.IGNORECASE)


# Pre-compile all patterns at import time (not on each call)
_SKILL_PATTERNS: list[tuple[str, re.Pattern]] = [
    (skill, _make_skill_pattern(skill)) for skill in _CANONICAL_SKILLS
]

# Pre-compile alias patterns too — resolve aliases via word boundaries,
# independent of NER (which is unreliable for tokens like "k8s"/"golang").
_ALIAS_PATTERNS: list[tuple[str, re.Pattern]] = [
    (canonical, _make_skill_pattern(alias)) for alias, canonical in _ALIAS_MAP.items()
]


def extract_skills(text: str) -> list[str]:
    """
    Return canonical skill names found in text.

    Strategy:
    1. spaCy NER (PRODUCT/ORG entities) → alias normalization
    2. Word-boundary regex on all canonical skills (always runs; handles
       false positives like 'r' in 'engineer', 'java' in 'javascript')
    """
    found: set[str] = set()
    text_lower = text.lower()

    # 1. spaCy NER: catch variants and aliases (e.g. "k8s" → "kubernetes")
    nlp = get_nlp()
    if nlp is not None:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ in ("PRODUCT", "ORG"):
                canonical = _ALIAS_MAP.get(ent.text.lower())
                if canonical:
                    found.add(canonical)

    # 2. Word-boundary regex on canonical names (fixes false positives)
    for skill, pattern in _SKILL_PATTERNS:
        if pattern.search(text_lower):
            found.add(skill)

    # 3. Word-boundary regex on alias variants → canonical (NER-independent)
    for canonical, pattern in _ALIAS_PATTERNS:
        if pattern.search(text_lower):
            found.add(canonical)

    return sorted(found)


def overlap_skills(text_a: str, text_b: str) -> tuple[list[str], list[str], list[str]]:
    """Return (matched, only_in_a, only_in_b) skill lists for two texts."""
    skills_a = set(extract_skills(text_a))
    skills_b = set(extract_skills(text_b))
    matched = sorted(skills_a & skills_b)
    only_a = sorted(skills_a - skills_b)
    only_b = sorted(skills_b - skills_a)
    return matched, only_a, only_b
