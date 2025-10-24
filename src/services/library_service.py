from src.models.book import Book
from src.models.user import User

class LibraryService:
    def __init__(self):
        self.books = []
        self.users = []

    def register_user(self, username, role="lector"):
        user = User(username, role)
        self.users.append(user)
        return user

    def upload_book(self, title, author, public_domain=True):
        if not public_domain:
            raise ValueError("Solo se pueden subir libros de dominio público.")
        book = Book(title, author, public_domain)
        self.books.append(book)
        return book

    def find_book(self, title):
        return next((b for b in self.books if b.title == title), None)

    def borrow_book(self, username, title):
        user = next((u for u in self.users if u.username == username), None)
        book = self.find_book(title)
        if not user or not book:
            return "Usuario o libro no encontrado."
        return user.borrow_book(book)

    def return_book(self, username, title):
        user = next((u for u in self.users if u.username == username), None)
        book = self.find_book(title)
        if not user or not book:
            return "Usuario o libro no encontrado."
        return user.return_book(book)

    def review_book(self, username, title, text, rating):
        user = next((u for u in self.users if u.username == username), None)
        book = self.find_book(title)
        if not user or not book:
            return "Usuario o libro no encontrado."

        result = user.write_review(book, text, rating)
        if 1 <= rating <= 5:
            book.add_review({"user": username, "text": text, "rating": rating})
        return result
