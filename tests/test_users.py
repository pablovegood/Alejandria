import pytest
from services.library_service import LibraryService

@pytest.fixture
def library(tmp_path):
    from services import storage
    storage.DATA_FILE = tmp_path / "test_data.json"
    lib = LibraryService()
    return lib

def test_register_user_success(library):
    msg = library.register_user("Cleopatra")
    assert hasattr(msg, "username")
    assert msg.username == "Cleopatra"

def test_register_user_duplicate(library):
    library.register_user("Ramsés")
    msg = library.register_user("ramsés")
    assert "ya está registrado" in msg

def test_find_user(library):
    library.register_user("Imhotep")
    user = library.find_user("imhotep")
    assert user is not None
    assert user.username == "Imhotep"
