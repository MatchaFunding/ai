import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_process_idea(monkeypatch):
    # Fake provider con vector fijo
    class FakeProv:
        async def embed(self, texts): return [[0.1, 0.2, 0.3]]

    from app.api import ia
    monkeypatch.setattr(ia, "_provider", FakeProv())

    payload = {
        "ID": 1, "Usuario": 42, "Campo": "Agro",
        "Problema": "Escasez de agua", "Publico": "Pymes",
        "Innovacion": "IoT riego"
    }
    r = client.post("/api/v1/ia/process-idea", json=payload)
    assert r.status_code == 200
    assert r.json()["Embedding"] == [0.1, 0.2, 0.3]
