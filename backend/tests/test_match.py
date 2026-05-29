"""Tests for /api/match/{resume-jobs,job-resumes,one-to-one}."""


# ── /api/match/resume-jobs ───────────────────────────────────────────────────

def test_resume_jobs_validation_short_text(client):
    r = client.post("/api/match/resume-jobs", json={"text": "hi"})
    assert r.status_code == 422


def test_resume_jobs_empty_db_returns_zero_results(client, supabase_mock):
    # Default mock: rpc returns []
    r = client.post("/api/match/resume-jobs", json={
        "text": "Senior Python Developer with FastAPI",
        "top_k": 5,
        "rerank": False,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["results"] == []
    assert body["model_used"] == "BAAI/bge-large-en-v1.5"


def test_resume_jobs_happy_path(client, supabase_mock):
    # RPC returns one candidate
    supabase_mock.rpc.return_value.execute.return_value.data = [{
        "id": "j1", "title": "Senior Python Developer", "company": "Acme",
        "salary": "$140K-$180K", "experience": "5+ yrs", "work_type": "Full-Time",
        "skills": ["python", "fastapi"], "similarity": 0.85,
    }]
    # Follow-up select for full_text/source/URLs
    supabase_mock.table.return_value.select.return_value.in_.return_value.execute.return_value.data = [{
        "id": "j1",
        "full_text":   "Python developer with FastAPI and PostgreSQL experience",
        "source":      "jobspy:indeed",
        "job_url":     "https://www.indeed.com/viewjob?jk=j1",
        "company_url": "https://acme.example",
    }]

    r = client.post("/api/match/resume-jobs", json={
        "text": "Senior Python developer with FastAPI",
        "top_k": 5,
        "rerank": False,
    })
    assert r.status_code == 200
    body = r.json()
    assert len(body["results"]) == 1
    job = body["results"][0]
    assert job["job_id"] == "j1"
    assert job["source"] == "jobspy:indeed"
    assert job["job_url"].startswith("https://")
    assert "python" in job["matched_skills"]


def test_resume_jobs_source_filter_strips_csv(client, supabase_mock):
    supabase_mock.rpc.return_value.execute.return_value.data = [
        {"id": "a", "title": "Indeed Job",  "company": "Acme",    "salary": "",
         "experience": "", "work_type": "", "skills": [], "similarity": 0.9},
        {"id": "b", "title": "CSV Job",     "company": "Sample",  "salary": "",
         "experience": "", "work_type": "", "skills": [], "similarity": 0.8},
    ]
    supabase_mock.table.return_value.select.return_value.in_.return_value.execute.return_value.data = [
        {"id": "a", "full_text": "fastapi python", "source": "jobspy:indeed"},
        {"id": "b", "full_text": "fastapi python", "source": "JOB_data_sample.csv"},
    ]
    r = client.post("/api/match/resume-jobs", json={
        "text": "Senior Python Developer with FastAPI",
        "top_k": 5, "rerank": False, "sources": ["indeed"],   # exclude CSV
    })
    assert r.status_code == 200
    ids = [j["job_id"] for j in r.json()["results"]]
    assert ids == ["a"]


# ── /api/match/job-resumes ───────────────────────────────────────────────────

def test_job_resumes_validation_short_text(client):
    r = client.post("/api/match/job-resumes", json={"text": "hi"})
    assert r.status_code == 422


def test_job_resumes_section_aware_calls_sectioned_rpc(client, supabase_mock):
    """When section_aware=True, the route calls match_resumes_sectioned RPC."""
    # sectioned RPC returns resume_id (not id); route must normalise to "id" key
    supabase_mock.rpc.return_value.execute.return_value.data = [{
        "resume_id": "r1",
        "category": "Python Developer",
        "preview": "Python developer with FastAPI experience",
        "similarity": 0.88,
        "best_section": "experience",
    }]
    # After normalisation the route does .in_("id", ["r1"]) on the resumes table
    supabase_mock.table.return_value.select.return_value.in_.return_value.execute.return_value.data = [{
        "id": "r1",
        "full_text": "Python developer with FastAPI Django PostgreSQL",
        "source": "sid1877/Resume-dataset-2024",
    }]

    r = client.post("/api/match/job-resumes", json={
        "text": "Looking for a Python developer with FastAPI experience",
        "top_k": 3, "rerank": False, "section_aware": True,
    })
    assert r.status_code == 200
    body = r.json()
    assert len(body["results"]) == 1
    rpc_name = supabase_mock.rpc.call_args[0][0]
    assert rpc_name == "match_resumes_sectioned"
    assert body["results"][0]["best_section"] == "experience"


def test_job_resumes_happy_path(client, supabase_mock):
    supabase_mock.rpc.return_value.execute.return_value.data = [{
        "id": "r1", "category": "Python Developer",
        "preview": "Python developer with 5 years experience...",
        "similarity": 0.91,
    }]
    supabase_mock.table.return_value.select.return_value.in_.return_value.execute.return_value.data = [{
        "id": "r1",
        "full_text": "Python developer with FastAPI Django PostgreSQL",
        "source": "sid1877/Resume-dataset-2024",
    }]
    r = client.post("/api/match/job-resumes", json={
        "text": "Looking for a Python developer with FastAPI experience",
        "top_k": 3, "rerank": False,
    })
    assert r.status_code == 200
    body = r.json()
    assert len(body["results"]) == 1
    res = body["results"][0]
    assert res["resume_id"] == "r1"
    assert res["category"] == "Python Developer"
    assert "preview" in res


# ── /api/match/one-to-one ────────────────────────────────────────────────────

def test_one_to_one_validation_short_inputs(client):
    r = client.post("/api/match/one-to-one", json={"job_text": "hi", "resume_text": "hi"})
    assert r.status_code == 422


def test_one_to_one_happy(client, embedder_mock):
    r = client.post("/api/match/one-to-one", json={
        "job_text":    "Senior Python Developer needed with FastAPI and PostgreSQL",
        "resume_text": "I have 5 years of Python FastAPI PostgreSQL experience",
    })
    assert r.status_code == 200
    body = r.json()
    # Both inputs encode to the same unit vector → similarity = 1.0
    assert body["similarity"] == 1.0
    assert body["quality"] == "Excellent"
    assert "python"     in body["matched_skills"]
    assert "fastapi"    in body["job_skills"]
    assert "postgresql" in body["resume_skills"]
