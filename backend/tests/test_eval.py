"""Tests for /api/eval/{feedback,recent}."""


def test_feedback_404_on_missing_eval(client, supabase_mock):
    # Default mock returns None for the single() lookup
    r = client.post("/api/eval/feedback", json={
        "eval_id":   "00000000-0000-0000-0000-000000000000",
        "result_id": "11111111-1111-1111-1111-111111111111",
        "action":    "up",
    })
    assert r.status_code == 404


def test_feedback_happy(client, supabase_mock):
    # Make the lookup find an existing evaluation row
    chain = supabase_mock.table.return_value.select.return_value.eq.return_value.single.return_value
    chain.execute.return_value.data = {"user_feedback": {}}

    r = client.post("/api/eval/feedback", json={
        "eval_id":   "abc",
        "result_id": "result-1",
        "action":    "up",
    })
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_feedback_action_validation(client):
    r = client.post("/api/eval/feedback", json={
        "eval_id":   "abc",
        "result_id": "x",
        "action":    "loved-it",   # not in the up|down|clicked enum
    })
    assert r.status_code == 422


def test_recent_evals_empty(client, supabase_mock):
    r = client.get("/api/eval/recent")
    assert r.status_code == 200
    assert r.json() == {"evaluations": []}


def test_recent_evals_returns_rows(client, supabase_mock):
    chain = supabase_mock.table.return_value.select.return_value.order.return_value.limit.return_value
    chain.execute.return_value.data = [
        {"id": "1", "query_type": "resume_to_jobs", "model_name": "bge",
         "reranked": True, "latency_ms": 500, "created_at": "2026-01-01"},
    ]
    r = client.get("/api/eval/recent")
    assert r.status_code == 200
    rows = r.json()["evaluations"]
    assert len(rows) == 1
    assert rows[0]["model_name"] == "bge"
