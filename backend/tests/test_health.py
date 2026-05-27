def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["service"] == "Matchr API"
    assert body["health"] == "/api/health"


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "models_loaded": True}


def test_models(client):
    r = client.get("/api/models")
    assert r.status_code == 200
    body = r.json()
    assert body["default"] == "BAAI/bge-large-en-v1.5"
    assert body["cross_encoder"] == "cross-encoder/ms-marco-MiniLM-L-6-v2"
    ids = [m["id"] for m in body["models"]]
    assert "BAAI/bge-large-en-v1.5" in ids
    assert len(ids) == 1, "Production trims to a single bi-encoder"
