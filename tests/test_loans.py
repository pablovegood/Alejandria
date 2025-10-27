import pytest
from services.library_service import LibraryService

@pytest.fixture
def library(tmp_path):
    from services import storage
    storage.DATA_FILE = tmp_path / "test_data.json"
    lib = LibraryService()
    lib.register_user("Nefertari")
    lib.upload_book("Historia del Desierto", "Horus")
    return lib

def test_borrow_and_return(library):
    rb = library.borrow_book("Nefertari", "Historia del Desierto")
    assert "ha tomado prestado" in rb

    rr = library.return_book("Nefertari", "Historia del Desierto")
    assert "ha devuelto" in rr

def test_borrow_unavailable(library):
    library.borrow_book("Nefertari", "Historia del Desierto")
    msg = library.borrow_book("Nefertari", "Historia del Desierto")
    assert "no está disponible" in msg

def test_list_active_reservations(library):
    library.borrow_book("Nefertari", "Historia del Desierto")
    text = library.list_active_reservations()
    assert "Historia del Desierto" in text
    assert "Nefertari" in text
