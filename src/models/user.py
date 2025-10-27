class User:
    def __init__(self, username, role="lector"):
        self.username = username
        self.role = role
        self.borrowed_books = []   # títulos de los libros prestados
        self.reviews = {}          # {titulo: {"text":..., "rating":...}}

    def borrow_book(self, book):
        if book.available:
            self.borrowed_books.append(book.title)
            book.available = False
            return f"{self.username} ha tomado prestado '{book.title}'."
        return f"'{book.title}' no está disponible."

    def return_book(self, book):
        if book.title in self.borrowed_books:
            self.borrowed_books.remove(book.title)
            book.available = True
            return f"{self.username} ha devuelto '{book.title}'."
        return f"{self.username} no tenía '{book.title}'."

    def write_review(self, book, text, rating):
        if not 1 <= rating <= 5:
            return "La puntuación debe estar entre 1 y 5."
        self.reviews[book.title] = {"text": text, "rating": rating}
        return f"Reseña añadida para '{book.title}' con puntuación {rating}."

    # ---------------- SERIALIZACIÓN ----------------
    def to_dict(self):
        """Convierte el usuario a un dict serializable en JSON."""
        return {
            "username": self.username,
            "role": self.role,
            "borrowed_books": self.borrowed_books,
            "reviews": self.reviews,
        }

    @classmethod
    def from_dict(cls, data):
        """Crea un objeto User desde un dict (recuperado del JSON)."""
        user = cls(data["username"], data.get("role", "lector"))
        user.borrowed_books = data.get("borrowed_books", [])
        user.reviews = data.get("reviews", {})
        return user

    def __repr__(self):
        return f"User({self.username}, role={self.role})"
