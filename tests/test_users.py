from src.loan.service import LoanService

def test_create_and_delete_loan(tmp_path):
    db_path = tmp_path / "loan_test.db"
    service = LoanService()
    service.db = service.db  # usar la conexión interna

    service.create_loan("pablo", 123, "Libro test", "Autor X")
    loans = service.list_loans("pablo")
    assert any(l["guten_id"] == 123 for l in loans)

    service.delete_loan("pablo", 123)
    loans_after = service.list_loans("pablo")
    assert not any(l["guten_id"] == 123 for l in loans_after)
