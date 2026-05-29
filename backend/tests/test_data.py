"""Tests for /api/ingest/{resume,job} including X-API-Key gating."""

LONG_TEXT = "Python developer with FastAPI experience and PostgreSQL background. " * 5


# ── /api/ingest/resume ───────────────────────────────────────────────────────

def test_ingest_resume_validation_too_short(client, supabase_mock):
    r = client.post("/api/ingest/resume", json={
        "category":  "Software Developer",
        "full_text": "short",
    })
    assert r.status_code == 422


def test_ingest_resume_happy(client, supabase_mock):
    r = client.post("/api/ingest/resume", json={
        "category":  "Python Developer",
        "full_text": LONG_TEXT,
    })
    assert r.status_code == 201
    body = r.json()
    assert body["source_id"].startswith("user_")
    assert "Python Developer" in body["message"]


def test_ingest_resume_embeds_sections(client, supabase_mock):
    """User-submitted resumes must also populate resume_sections so they are
    reachable via section-aware retrieval."""
    r = client.post("/api/ingest/resume", json={
        "category":  "Python Developer",
        "full_text": LONG_TEXT,
    })
    assert r.status_code == 201
    supabase_mock.table.assert_any_call("resume_sections")


# ── /api/ingest/job ──────────────────────────────────────────────────────────

def test_ingest_job_validation_too_short(client, supabase_mock):
    r = client.post("/api/ingest/job", json={
        "title":     "Engineer",
        "full_text": "short",
    })
    assert r.status_code == 422


def test_ingest_job_happy(client, supabase_mock):
    r = client.post("/api/ingest/job", json={
        "title":     "Senior Python Engineer",
        "company":   "Acme",
        "salary":    "$120K",
        "skills":    ["python", "fastapi"],
        "full_text": LONG_TEXT,
    })
    assert r.status_code == 201
    body = r.json()
    assert body["source_id"].startswith("user_")
    assert "Senior Python Engineer" in body["message"]


# ── X-API-Key gate ───────────────────────────────────────────────────────────

def test_ingest_unauthenticated_when_gate_enabled(client, supabase_mock, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "api_key", "secret-123")

    r = client.post("/api/ingest/resume", json={
        "category":  "Tester",
        "full_text": LONG_TEXT,
    })
    assert r.status_code == 401


def test_ingest_wrong_key_when_gate_enabled(client, supabase_mock, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "api_key", "secret-123")

    r = client.post(
        "/api/ingest/resume",
        headers={"X-API-Key": "wrong"},
        json={"category": "Tester", "full_text": LONG_TEXT},
    )
    assert r.status_code == 401


def test_ingest_correct_key_when_gate_enabled(client, supabase_mock, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "api_key", "secret-123")

    r = client.post(
        "/api/ingest/resume",
        headers={"X-API-Key": "secret-123"},
        json={"category": "Tester", "full_text": LONG_TEXT},
    )
    assert r.status_code == 201
