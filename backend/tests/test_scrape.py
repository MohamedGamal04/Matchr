"""Tests for /api/scrape/jobs-for-query."""


def test_scrape_validation_short_text(client, supabase_mock):
    r = client.post("/api/scrape/jobs-for-query", json={"text": "hi"})
    assert r.status_code == 422


def test_scrape_happy(client, supabase_mock, embedder_mock, jobspy_mock):
    r = client.post("/api/scrape/jobs-for-query", json={
        "text":           "Senior Python Developer with FastAPI experience",
        "results_wanted": 5,
        "sites":          ["indeed"],
    })
    assert r.status_code == 200
    body = r.json()
    assert body["scraped"]  == 1
    assert body["inserted"] == 1
    assert body["errors"]   == 0


def test_scrape_with_explicit_search_term(client, supabase_mock, embedder_mock, jobspy_mock):
    r = client.post("/api/scrape/jobs-for-query", json={
        "text":           "Some long resume text that the route still validates min_length on.",
        "search_term":    "Data Scientist",
        "results_wanted": 5,
        "sites":          ["indeed"],
    })
    assert r.status_code == 200
    assert r.json()["search_term"] == "Data Scientist"


# ── X-API-Key gate ───────────────────────────────────────────────────────────

def test_scrape_unauthenticated_when_gate_enabled(
    client, supabase_mock, embedder_mock, jobspy_mock, monkeypatch
):
    from app.config import settings
    monkeypatch.setattr(settings, "api_key", "secret-abc")

    r = client.post("/api/scrape/jobs-for-query", json={
        "text":  "Senior Python Developer with FastAPI experience",
        "sites": ["indeed"],
    })
    assert r.status_code == 401


def test_scrape_correct_key_when_gate_enabled(
    client, supabase_mock, embedder_mock, jobspy_mock, monkeypatch
):
    from app.config import settings
    monkeypatch.setattr(settings, "api_key", "secret-abc")

    r = client.post(
        "/api/scrape/jobs-for-query",
        headers={"X-API-Key": "secret-abc"},
        json={
            "text":  "Senior Python Developer with FastAPI experience",
            "sites": ["indeed"],
        },
    )
    assert r.status_code == 200
