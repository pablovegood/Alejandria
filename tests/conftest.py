import sys
import os
import pytest

# Añade automáticamente la carpeta src al sys.path (solo una vez)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_PATH = os.path.join(BASE_DIR, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from services.library_service import LibraryService


@pytest.fixture
def library():
    lib = LibraryService()
    lib.register_user("Pablo")
    lib.upload_book("El Quijote", "Miguel de Cervantes")
    lib.upload_book("Frankenstein", "Mary Shelley")
    return lib
