import pytest
from services.library_service import LibraryService

@pytest.fixture
def library(tmp_path):
    from services import storage
    storage.DATA_FILE = tmp_path / "test_data.json"
    lib = LibraryService()
    return lib

def test_upload_book_creates_entry(library):
    b = library.upload_book("Libro del Nilo", "Anubis")
    assert b.title == "Libro del Nilo"
    assert b.available

def test_find_book_case_insensitive(library):
    library.upload_book("Sol de Tebas", "Ra")
    found = library.find_book("sol de tebas")
    assert found is not None
    assert found.author == "Ra"

def test_preview_without_file(library):
    library.upload_book("Vacío", "Isis")
    msg = library.preview_book("Vacío")
    assert "no tiene archivo asociado" in msg.lower()
