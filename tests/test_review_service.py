# tests/test_review_service.py
from src.review.service import ReviewService
from pathlib import Path
import tempfile
import os
import sqlite3

def test_create_and_list_review(tmp_path):
    """Debe crear y listar reseñas en una BD aislada."""
    # Crear base de datos temporal
    db_path = tmp_path / "review_test.db"

    # Instanciar el servicio con la BD temporal
    service = ReviewService()
    service.db = sqlite3.connect(db_path)
    service.db.row_factory = sqlite3.Row
    service._init_db()  # crea tablas si no existen

    guten_id = 12
    username = "pablo"
    rating = 5
    text = "Excelente libro."

    # Crear reseña
    service.create_review(guten_id, username, rating, text)

    # Comprobar que se guarda
    reviews = service.list_reviews(guten_id)
    assert len(reviews) == 1
    r = reviews[0]
    assert r["username"] == username
    assert r["rating"] == rating
    assert text in r["text"]

    # Limpieza
    service.db.close()
    if db_path.exists():
        os.remove(db_path)
