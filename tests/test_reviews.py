import pytest
from services.library_service import LibraryService

@pytest.fixture
def library(tmp_path):
    from services import storage
    storage.DATA_FILE = tmp_path / "test_data.json"
    lib = LibraryService()
    lib.register_user("Pablo")
    lib.upload_book("El Juicio de Osiris", "Thot")
    return lib

def test_review_book_valid(library):
    msg = library.review_book("Pablo", "El Juicio de Osiris", "Obra maestra", 5)
    assert "Reseña añadida" in msg

def test_review_invalid_rating(library):
    msg = library.review_book("Pablo", "El Juicio de Osiris", "meh", 10)
    assert "puntuación debe estar entre 1 y 5" in msg.lower()

def test_average_rating(library):
    book = library.find_book("El Juicio de Osiris")
    book.add_review({"user": "A", "comment": "bien", "rating": 4})
    book.add_review({"user": "B", "comment": "meh", "rating": 2})
    assert book.average_rating() == 3
