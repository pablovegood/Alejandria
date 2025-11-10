import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

USERNAME = "pablo_test"
PASSWORD = "1234"
BOOK_ID = 10
BOOK_TITLE = "Test Book"
BOOK_AUTHOR = "Anon Author"

# ----------------------------
# AUTH TESTS
# ----------------------------

def test_01_signup_user():
    res = client.post("/auth/signup", json={
        "username": USERNAME,
        "password": PASSWORD
    })
    assert res.status_code in (200, 409)
    data = res.json()
    if res.status_code == 200:
        assert "username" in data
    else:
        assert data.get("detail") == "El usuario ya existe"


def test_02_login_user():
    res = client.post("/auth/login", json={
        "username": USERNAME,
        "password": PASSWORD
    })
    assert res.status_code == 200
    data = res.json()
    assert data["username"] == USERNAME

# ----------------------------
# CATALOG TESTS
# ----------------------------

def test_03_search_catalog():
    res = client.get("/catalog/search?q=test")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, dict)
    assert "results" in data
    if len(data["results"]) > 0:
        first = data["results"][0]
        assert "title" in first

def test_04_read_catalog_book():
    res = client.get(f"/catalog/read/{BOOK_ID}")
    assert res.status_code in (200, 404, 422)

# ----------------------------
# LOAN TESTS
# ----------------------------

def test_05_create_loan():
    res = client.post("/loans/", json={
        "username": USERNAME,
        "guten_id": BOOK_ID,
        "title": BOOK_TITLE,
        "author": BOOK_AUTHOR
    })
    assert res.status_code in (200, 409)
    data = res.json()
    assert "book" in data or "detail" in data

def test_06_list_loans():
    res = client.get(f"/loans/?username={USERNAME}")
    assert res.status_code == 200
    data = res.json()
    assert "loans" in data
    assert isinstance(data["loans"], list)

def test_07_delete_loan():
    res = client.delete(f"/loans/{USERNAME}/{BOOK_ID}")
    assert res.status_code in (200, 404)
    data = res.json()
    assert isinstance(data, dict)

# ----------------------------
# REVIEW TESTS
# ----------------------------

def test_08_add_review():
    res = client.post(f"/reviews/{BOOK_ID}", json={
        "username": USERNAME,
        "rating": 5,
        "text": "Muy buen libro."
    })
    assert res.status_code in (200, 201)
    data = res.json()
    assert "username" in data
    assert "text" in data

def test_09_list_reviews():
    res = client.get(f"/reviews/{BOOK_ID}")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    if data:
        assert "username" in data[0]
        assert "rating" in data[0]
