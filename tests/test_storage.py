import json
import os
import pytest
from services.library_service import LibraryService

@pytest.fixture
def tmp_storage(tmp_path):
    from services import storage
    storage.DATA_FILE = tmp_path / "persist.json"
    lib = LibraryService()
    return lib, storage.DATA_FILE

def test_save_and_load_persistence(tmp_storage):
    lib, path = tmp_storage
    lib.register_user("Tutankamón")
    lib.upload_book("El Despertar del Faraón", "Ra")

    lib._save()
    assert os.path.exists(path)

    with open(path) as f:
        data = json.load(f)
    assert "users" in data and "books" in data

def test_persistence_restores_users(tmp_storage):
    lib, path = tmp_storage
    lib.register_user("Hatshepsut")
    lib._save()

    new_lib = LibraryService()
    found = new_lib.find_user("Hatshepsut")
    assert found is not None
