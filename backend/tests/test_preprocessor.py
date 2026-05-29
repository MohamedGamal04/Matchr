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
