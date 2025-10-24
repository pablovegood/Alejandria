class User:
    def __init__(self, username, role="lector"):
        self.username = username
        self.role = role
        self.borrowed_books = []
        self.reviews = {}

    def borrow_book(self, book):
        if book.available:
            self.borrowed_books.append(book)
            book.available = False
            return f"{self.username} ha tomado prestado '{book.title}'."
        return f"'{book.title}' no está disponible."

    def return_book(self, book):
        if book in self.borrowed_books:
            self.borrowed_books.remove(book)
            book.available = True
            return f"{self.username} ha devuelto '{book.title}'."
        return f"{self.username} no tenía '{book.title}'."

    def write_review(self, book, text, rating):
        if not 1 <= rating <= 5:
            return "La puntuación debe estar entre 1 y 5."
        self.reviews[book.title] = {"text": text, "rating": rating}
        return f"Reseña añadida para '{book.title}' con puntuación {rating}."
