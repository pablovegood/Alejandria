from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)
USERNAME = "integration_user"
PASSWORD = "12345"

def test_complete_loan_flow():
    # Signup/Login
    client.post("/auth/signup", json={"username": USERNAME, "password": PASSWORD})
    client.post("/auth/login", json={"username": USERNAME, "password": PASSWORD})

    # Buscar libro
    res = client.get("/catalog/search?q=Alice")
    assert res.status_code == 200
    book = res.json()["results"][0]

    # Crear préstamo
    res = client.post("/loans/", json={
        "username": USERNAME,
        "guten_id": book["guten_id"],
        "title": book["title"],
        "author": book["author"]
    })
    assert res.status_code in (200, 201)

    # Listar
    res = client.get(f"/loans/?username={USERNAME}")
    loans = res.json()["loans"]
    assert any(l["title"] == book["title"] for l in loans)

    # Devolver
    client.delete(f"/loans/{USERNAME}/{book['guten_id']}")
