"""Unit tests for preprocessor service."""
from app.services.preprocessor import preprocess_text, extract_skills


def test_preprocess_preserves_case():
    result = preprocess_text("Python Developer at Google")
    assert "Python" in result
    assert "Google" in result


def test_preprocess_strips_url():
    result = preprocess_text("Visit https://example.com for details")
    assert "https" not in result
    assert "example.com" not in result


def test_preprocess_strips_email():
    result = preprocess_text("Contact john@acme.com for info")
    assert "@" not in result


def test_preprocess_collapses_whitespace():
    result = preprocess_text("Python   Developer\n\nFastAPI")
    assert "  " not in result
    assert "\n" not in result


def test_preprocess_preserves_numbers():
    result = preprocess_text("5 years of experience")
    assert "5" in result
    assert "five" not in result


# ── False-positive regression tests ──────────────────────────────────────────

def test_no_r_false_positive_in_engineer():
    """'r' must not match 'engineer'."""
    skills = extract_skills("Senior Software Engineer Manager")
    assert "r" not in skills


def test_no_go_false_positive_in_google():
    """'go' must not match 'google'."""
    skills = extract_skills("Experience with Google Cloud Platform")
    assert "go" not in skills


def test_no_java_false_positive_in_javascript():
    """'java' must not match 'javascript'."""
    skills = extract_skills("5 years of JavaScript development")
    assert "java" not in skills


def test_go_matches_standalone():
    skills = extract_skills("Go developer with microservices experience")
    assert "go" in skills


def test_java_matches_standalone():
    skills = extract_skills("Java developer with Spring Boot experience")
    assert "java" in skills


def test_alias_k8s_normalizes_to_kubernetes():
    skills = extract_skills("Deployed services on k8s clusters")
    assert "kubernetes" in skills
    assert "k8s" not in skills


def test_alias_golang_normalizes_to_go():
    skills = extract_skills("Golang developer for 3 years")
    assert "go" in skills


def test_alias_postgres_normalizes_to_postgresql():
    skills = extract_skills("Managed postgres databases")
    assert "postgresql" in skills


def test_python_detected():
    skills = extract_skills("Senior Python Developer with FastAPI experience")
    assert "python" in skills


def test_fastapi_detected():
    skills = extract_skills("Building REST APIs with FastAPI and PostgreSQL")
    assert "fastapi" in skills
    assert "postgresql" in skills
