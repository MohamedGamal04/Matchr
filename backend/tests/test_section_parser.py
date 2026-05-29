"""Unit tests for resume section parser."""
from app.services.section_parser import parse_sections


SAMPLE_RESUME = """
Summary
Experienced Python developer with 5 years in backend engineering.

Experience
Software Engineer at Acme Corp 2020-2024
Built FastAPI microservices deployed on Kubernetes.

Skills
Python, FastAPI, PostgreSQL, Docker, Kubernetes

Education
B.Sc. Computer Science, State University 2018
"""

RESUME_NO_HEADERS = """
Python developer with FastAPI and PostgreSQL experience.
Built microservices. Deployed on AWS.
"""


def test_parse_sections_detects_standard_headers():
    sections = parse_sections(SAMPLE_RESUME)
    assert "experience" in sections
    assert "skills" in sections
    assert "education" in sections
    assert "summary" in sections


def test_parse_sections_experience_contains_fastapi():
    sections = parse_sections(SAMPLE_RESUME)
    assert "FastAPI" in sections["experience"]


def test_parse_sections_skills_section_content():
    sections = parse_sections(SAMPLE_RESUME)
    assert "Python" in sections["skills"]
    assert "Kubernetes" in sections["skills"]


def test_parse_sections_fallback_when_no_headers():
    sections = parse_sections(RESUME_NO_HEADERS)
    assert sections == {"other": RESUME_NO_HEADERS}


def test_parse_sections_empty_text():
    sections = parse_sections("")
    assert "other" in sections


def test_parse_sections_case_insensitive_headers():
    text = "EXPERIENCE\nBuilt Python services.\n\nSKILLS\nPython, Go"
    sections = parse_sections(text)
    assert "experience" in sections
    assert "skills" in sections


def test_parse_sections_colon_suffix_stripped():
    text = "Experience:\nBuilt Python services.\n\nSkills:\nPython"
    sections = parse_sections(text)
    assert "experience" in sections
    assert "skills" in sections
