from fastapi.testclient import TestClient

from api.index import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_ask_returns_contract_shape():
    resp = client.post("/api/ask", json={"query": "下定决心", "channel": "web", "top_k": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"answer", "retrieved"}
    assert set(body["answer"]) == {"summary", "explanation", "examples", "grounded"}
    retrieved_ids = {r["sentence_id"] for r in body["retrieved"]}
    assert set(body["answer"]["examples"]) <= retrieved_ids
    assert body["answer"]["grounded"] is True


def test_ask_without_evidence_is_ungrounded():
    resp = client.post("/api/ask", json={"query": "量子色动力学"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["retrieved"] == []
    assert body["answer"]["grounded"] is False
    assert body["answer"]["examples"] == []


def test_ask_rejects_empty_query():
    resp = client.post("/api/ask", json={"query": ""})
    assert resp.status_code == 422
