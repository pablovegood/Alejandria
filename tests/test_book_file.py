import os
import pytest
from models.book import Book


@pytest.fixture
def temp_pdf(tmp_path):
    """Crea un PDF temporal simulado (texto plano)."""
    file = tmp_path / "demo.pdf"
    file.write_text("Primera línea\nSegunda línea\nTercera línea\n")
    return str(file)


@pytest.fixture
def temp_docx(tmp_path):
    """Crea un DOCX temporal (archivo inválido, pero existente)."""
    file = tmp_path / "demo.docx"
    file.write_text("Contenido de prueba DOCX\n")
    return str(file)


def test_attach_and_preview_pdf(temp_pdf):
    b = Book("Demo", "Autor X")
    msg = b.attach_file(temp_pdf)
    assert "asociado correctamente" in msg
    content = b.preview(lines=2)
    assert "Primera línea" in content
    assert "Vista previa" in content


def test_attach_invalid_file(temp_docx):
    """Debe lanzar ValueError si el formato no es PDF o EPUB."""
    b = Book("Demo", "Autor X")
    with pytest.raises(ValueError):
        b.attach_file(temp_docx)


def test_attach_nonexistent_file():
    """Debe lanzar FileNotFoundError si el archivo no existe."""
    b = Book("Demo", "Autor X")
    with pytest.raises(FileNotFoundError):
        b.attach_file("no_existe.pdf")
