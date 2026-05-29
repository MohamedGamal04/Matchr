"""Shared pytest fixtures.

The bi-encoder + cross-encoder, Supabase client, and JobSpy library are
all replaced with fast in-memory fakes so the test suite runs in <2 s
without network access, model downloads, or DB writes.
"""

from __future__ import annotations

import math
from unittest.mock import MagicMock

import pandas as pd
import pytest
from fastapi.testclient import TestClient

# Unit vector — dot product with itself = 1.0, so the one-to-one route
# returns similarity == 1.0 and quality == "Excellent".
UNIT_VAL = 1.0 / math.sqrt(1024)


@pytest.fixture
def embedder_mock(monkeypatch):
    """Patch every encoder + the cross-encoder to return constant vectors."""

    def fake_encode_query(model_name, text):
        return [UNIT_VAL] * 1024

    def fake_encode_document(model_name, text):
        return [UNIT_VAL] * 1024

    def fake_encode_batch_documents(model_name, texts, **kw):
        return [[UNIT_VAL] * 1024 for _ in texts]

    def fake_rerank(query, candidates, text_key="full_text", top_k=None):
        for c in candidates:
            c["rerank_score"] = 0.95
        ranked = sorted(candidates, key=lambda x: x.get("rerank_score", 0), reverse=True)
        return ranked[:top_k] if top_k else ranked

    def fake_preload_models():
        return None

    targets = {
        # Service module itself
        "app.services.embedder.encode_query":            fake_encode_query,
        "app.services.embedder.encode_document":         fake_encode_document,
        "app.services.embedder.encode_batch_documents":  fake_encode_batch_documents,
        "app.services.embedder.rerank":                  fake_rerank,
        "app.services.embedder.preload_models":          fake_preload_models,
        # Re-import sites
        "app.routes.match.encode_query":                 fake_encode_query,
        "app.routes.match.rerank":                       fake_rerank,
        "app.routes.data.encode_document":               fake_encode_document,
        "app.services.scraper.encode_batch_documents":   fake_encode_batch_documents,
        "app.main.preload_models":                       fake_preload_models,
    }
    for path, fn in targets.items():
        monkeypatch.setattr(path, fn)


@pytest.fixture
def supabase_mock(monkeypatch):
    """A MagicMock Supabase client patched at every import site.

    Default chain returns:
      - .rpc(...).execute().data          → []
      - .table(...).insert(...).execute() → data=[{"id": "ins-1", ...}]
      - .table(...).upsert(...).execute() → data=[]
      - .table(...).select(...).execute() → []   (and all chained filters)

    Override per-test by writing into the relevant chain, e.g.:
      supabase_mock.rpc.return_value.execute.return_value.data = [...]
    """
    mock = MagicMock(name="supabase")
    # Useful defaults so the common write path doesn't need configuration
    mock.table.return_value.insert.return_value.execute.return_value.data = [{"id": "ins-1"}]
    mock.table.return_value.upsert.return_value.execute.return_value.data = []
    mock.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []
    mock.rpc.return_value.execute.return_value.data = []
    mock.table.return_value.select.return_value.execute.return_value.data = []
    mock.table.return_value.select.return_value.in_.return_value.execute.return_value.data = []
    mock.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None
    mock.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value.data = []

    for path in [
        "app.services.supabase_client.get_supabase",
        "app.routes.match.get_supabase",
        "app.routes.data.get_supabase",
        "app.routes.eval.get_supabase",
        "app.services.scraper.get_supabase",
    ]:
        monkeypatch.setattr(path, lambda _m=mock: _m)

    return mock


@pytest.fixture
def jobspy_mock(monkeypatch):
    """Replace jobspy.scrape_jobs with a function returning one synthetic row."""
    df = pd.DataFrame([{
        "id":           "j1",
        "site":         "indeed",
        "title":        "Senior Python Developer",
        "company":      "Acme Corp",
        "location":     "Remote",
        "job_type":     "fulltime",
        "description":  "Python developer with FastAPI and PostgreSQL experience. " * 5,
        "min_amount":   100000,
        "max_amount":   150000,
        "currency":     "USD",
        "interval":     "yearly",
        "job_url":      "https://www.indeed.com/viewjob?jk=fake-j1",
        "company_url":  "https://acme.example",
    }])

    def fake_scrape_jobs(**kwargs):
        return df

    monkeypatch.setattr("jobspy.scrape_jobs", fake_scrape_jobs)
    return df


@pytest.fixture(autouse=True)
def nlp_mock(monkeypatch):
    """
    Patch get_nlp() everywhere to return a fake NLP that produces no entities.
    Word-boundary regex in extract_skills still runs — tests rely on that.
    The NER branch is tested separately in test_preprocessor.py.
    """
    from unittest.mock import MagicMock

    class _FakeEnt:
        def __init__(self, text, label):
            self.text = text
            self.label_ = label

    class _FakeDoc:
        def __init__(self, text):
            self._text = text
            self.ents = []
            # Minimal sentence splitting on ". " for explain tests
            raw_sents = [s.strip() for s in text.split(". ") if s.strip()]
            self.sents = [type("Sent", (), {"text": s})() for s in raw_sents]

    fake_nlp = MagicMock(side_effect=lambda text: _FakeDoc(text))

    for path in [
        "app.services.preprocessor.get_nlp",
        "app.routes.explain.get_nlp",
    ]:
        try:
            monkeypatch.setattr(path, lambda _fn=fake_nlp: _fn)
        except (AttributeError, ImportError):
            pass  # explain.py not yet created — skip


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Clear rate-limit state between tests so we never hit 429 from a neighbour."""
    from app.services.limiter import limiter
    try:
        limiter.reset()
    except Exception:
        pass
    yield


@pytest.fixture
def client(embedder_mock, supabase_mock):
    """TestClient with embedder + Supabase mocked. Lifespan is NOT triggered
    (we don't use the `with` context), so preload_models isn't invoked even
    though it's patched."""
    from app.main import app
    return TestClient(app)
