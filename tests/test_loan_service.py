# tests/test_loan_service.py
from src.loan.service import LoanService
from pathlib import Path
import tempfile
import os

def test_create_list_delete_loan():
    """Debe crear, listar y eliminar préstamos correctamente."""
    # Crear base de datos temporal aislada
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "loan_test.db"

    service = LoanService()
    service.db = service.db  # usa la conexión ya inicializada

    username = "pablo_test"
    book_id = 9999
    title = "Libro de prueba"
    author = "Autor Desconocido"

    # --- Crear préstamo ---
    result = service.create_loan(username, book_id, title, author)
    assert result["user"] == username
    assert result["book"]["guten_id"] == book_id

    # --- Listar préstamos ---
    loans = service.list_loans(username)
    assert any(l["guten_id"] == book_id for l in loans)

    # --- Eliminar préstamo ---
    service.delete_loan(username, book_id)
    loans_after = service.list_loans(username)
    assert not any(l["guten_id"] == book_id for l in loans_after)

    # Limpieza
    service.db.close()
    if db_path.exists():
        os.remove(db_path)
