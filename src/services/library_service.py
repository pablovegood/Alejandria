from datetime import datetime, timedelta
from models.user import User
from models.book import Book


class LibraryService:
    """Servicio principal que gestiona usuarios, libros, préstamos y reseñas."""

    def __init__(self):
        self.users = []
        self.books = []
        self.reservations = []

    # ---------------------- USUARIOS ----------------------

    def register_user(self, username, role="lector"):
        """Registra un nuevo usuario si no existe."""
        if any(u.username.lower() == username.lower() for u in self.users):
            return f"⚠️ El usuario '{username}' ya está registrado."
        user = User(username, role)
        self.users.append(user)
        return user

    def find_user(self, username):
        """Busca un usuario por nombre (ignorando mayúsculas/minúsculas)."""
        return next((u for u in self.users if u.username.lower() == username.lower()), None)

    # ---------------------- LIBROS ----------------------

    def upload_book(self, title, author, public_domain=True, file_path=None):
        """Sube un libro nuevo, con o sin archivo asociado."""
        book = Book(title, author, public_domain, file_path)
        self.books.append(book)
        return book

    def find_book(self, title):
        """Busca un libro por título."""
        return next((b for b in self.books if b.title.lower() == title.lower()), None)

    def list_books(self):
        """Devuelve todos los libros cargados."""
        return self.books

    # ---------------------- PRÉSTAMOS ----------------------

    def borrow_book(self, username, title):
        """Permite a un usuario tomar prestado un libro disponible."""
        user = self.find_user(username)
        book = self.find_book(title)

        if not user or not book:
            return "❌ Usuario o libro no encontrado."
        if not book.available:
            return f"❌ El libro '{book.title}' no está disponible actualmente."

        # Crear la reserva
        reservation = {
            "user": user,
            "book": book,
            "date_borrowed": datetime.now(),
            "date_due": datetime.now() + timedelta(days=14),
            "active": True
        }

        book.available = False
        self.reservations.append(reservation)

        return (f"📕 {user.username} ha tomado prestado '{book.title}' "
                f"hasta el {reservation['date_due'].strftime('%d/%m/%Y')}.")

    def return_book(self, username, title):
        """Permite devolver un libro prestado."""
        user = self.find_user(username)
        book = self.find_book(title)

        if not user or not book:
            return "❌ Usuario o libro no encontrado."

        for r in self.reservations:
            if r["user"] == user and r["book"] == book and r["active"]:
                r["active"] = False
                book.available = True
                return f"✅ {user.username} ha devuelto '{book.title}'."

        return "⚠️ No se encontró una reserva activa para ese usuario y libro."

    def list_active_reservations(self):
        """Lista todos los préstamos activos."""
        activos = [r for r in self.reservations if r["active"]]
        if not activos:
            return "No hay préstamos activos."

        lineas = []
        for r in activos:
            linea = (
                f"📚 {r['book'].title} → {r['user'].username} "
                f"(vence el {r['date_due'].strftime('%d/%m/%Y')})"
            )
            lineas.append(linea)

        # Une todas las líneas con un salto de línea real
        return "\n".join(lineas)

    # ---------------------- RESEÑAS ----------------------

    def review_book(self, username, title, comment, rating):
        """Añade una reseña a un libro."""
        user = self.find_user(username)
        book = self.find_book(title)

        if not user or not book:
            return "❌ Usuario o libro no encontrado."
        if not (1 <= rating <= 5):
            return "⚠️ La puntuación debe estar entre 1 y 5."

        book.add_review({"user": user.username, "comment": comment, "rating": rating})
        return f"📝 Reseña añadida por {user.username} a '{book.title}'."

    # ---------------------- VISTA PREVIA ----------------------

    def preview_book(self, title):
        """Muestra la vista previa del archivo asociado a un libro."""
        book = self.find_book(title)
        if not book:
            return "❌ Libro no encontrado."
        return book.preview()

    def open_borrowed_book(self, username, title):
        """Permite abrir un libro solo si el usuario lo tiene en préstamo activo."""
        user = self.find_user(username)
        book = self.find_book(title)
        if not user or not book:
            return "❌ Usuario o libro no encontrado."

        # Verifica que el usuario tenga ese préstamo activo
        for r in self.reservations:
            if r["user"] == user and r["book"] == book and r["active"]:
                return book.open_book()

        return "⚠️ No puedes abrir este libro porque no lo tienes en préstamo activo."

