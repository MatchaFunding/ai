from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_ok():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "ok"
    assert body.get("service") == "IA Service"

def test_create_idea_echo():
    payload = {
        "ID": 1,
        "Usuario": 42,
        "Campo": "Agro",
        "Problema": "Escasez de agua en temporada seca",
        "Publico": "Pymes agrícolas de O'Higgins",
        "Innovacion": "Sensores IoT + riego inteligente"
    }
    r = client.post("/api/v1/ideas/", json=payload)
    assert r.status_code == 200
    data = r.json()

    assert data == payload
