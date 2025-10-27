def test_borrow_and_return(library):
    rb = library.borrow_book("Pablo", "El Quijote")
    assert "ha tomado prestado" in rb

    rr = library.return_book("Pablo", "El Quijote")
    assert "ha devuelto" in rr

def test_borrow_unavailable(library):
    # Primer préstamo deja el libro no disponible
    library.borrow_book("Pablo", "El Quijote")
    msg = library.borrow_book("Pablo", "El Quijote")
    assert "no está disponible" in msg

def test_review_book_valid(library):
    msg = library.review_book("Pablo", "Frankenstein", "Obra maestra", 5)
    assert "Reseña añadida" in msg

def test_review_book_invalid_rating(library):
    msg = library.review_book("Pablo", "Frankenstein", "meh", 6)
    assert "puntuación debe estar entre 1 y 5" in msg.lower()

def test_user_or_book_not_found(library):
    msg1 = library.borrow_book("Desconocido", "El Quijote")
    msg2 = library.borrow_book("Pablo", "Libro Inexistente")
    assert "Usuario o libro no encontrado." in msg1
    assert "Usuario o libro no encontrado." in msg2

def test_avg_rating_rounding(library):
    library.review_book("Pablo", "Frankenstein", "Top", 5)
    library.review_book("Pablo", "Frankenstein", "Bien", 4)
    book = library.find_book("Frankenstein")
    assert book.average_rating() == 4.5