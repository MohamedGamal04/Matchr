"""Tests for POST /api/explain/match."""


def test_explain_match_resume_happy_path(client, supabase_mock):
    """Explain endpoint returns matched_spans, skill_analysis, section_scores."""
    supabase_mock.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "full_text": "Python developer. FastAPI and PostgreSQL experience. Deployed on AWS."
    }
    supabase_mock.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"section_type": "experience", "embedding": [1.0 / 1024**0.5] * 1024},
        {"section_type": "skills", "embedding": [1.0 / 1024**0.5] * 1024},
    ]

    r = client.post("/api/explain/match", json={
        "query_text": "Looking for Python developer with FastAPI. AWS experience preferred.",
        "result_id": "r1",
        "result_type": "resume",
    })
    assert r.status_code == 200
    body = r.json()
    assert "matched_spans" in body
    assert isinstance(body["matched_spans"], list)
    assert len(body["matched_spans"]) <= 3
    # spans must be sorted by descending score
    scores = [s["score"] for s in body["matched_spans"]]
    assert scores == sorted(scores, reverse=True)
    assert "skill_analysis" in body
    assert "matched" in body["skill_analysis"]
    assert "missing" in body["skill_analysis"]
    assert "section_scores" in body
    assert "experience" in body["section_scores"]


def test_explain_match_job_no_section_scores(client, supabase_mock):
    """For result_type=job, section_scores must be empty dict."""
    supabase_mock.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "full_text": "We need a Python developer. FastAPI is required."
    }

    r = client.post("/api/explain/match", json={
        "query_text": "Python developer with FastAPI experience looking for remote work.",
        "result_id": "j1",
        "result_type": "job",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["section_scores"] == {}


def test_explain_match_not_found(client, supabase_mock):
    """Returns 404 when result_id does not exist in DB."""
    supabase_mock.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None

    r = client.post("/api/explain/match", json={
        "query_text": "Python developer with FastAPI experience.",
        "result_id": "nonexistent-id",
        "result_type": "resume",
    })
    assert r.status_code == 404


def test_explain_match_invalid_result_type(client):
    r = client.post("/api/explain/match", json={
        "query_text": "Python developer with FastAPI experience.",
        "result_id": "r1",
        "result_type": "invalid",
    })
    assert r.status_code == 422
