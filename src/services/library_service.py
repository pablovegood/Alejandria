from datetime import datetime, timedelta
from models.user import User
from models.book import Book
from services.storage import save_data, load_data  # 👈 nuevo

class LibraryService:
    """Servicio principal que gestiona usuarios, libros, préstamos y reseñas."""

    def __init__(self):
        data = load_data()
        self.users = [User.from_dict(u) if isinstance(u, dict) else u for u in data["users"]]
        self.books = [Book.from_dict(b) if isinstance(b, dict) else b for b in data["books"]]
        self.reservations = []

        # Reconstruir reservas (pasar de strings a objetos)
        for r in data.get("reservations", []):
            user_obj = self.find_user(r["user"]) if isinstance(r["user"], str) else r["user"]
            book_obj = self.find_book(r["book"]) if isinstance(r["book"], str) else r["book"]
            if user_obj and book_obj:
                self.reservations.append({
                    "user": user_obj,
                    "book": book_obj,
                    "date_borrowed": datetime.fromisoformat(r["date_borrowed"]),
                    "date_due": datetime.fromisoformat(r["date_due"]),
                    "active": r["active"]
                })

    def _save(self):
        """Guarda todo el estado actual del sistema."""
        data = {
            "users": [u.to_dict() for u in self.users],
            "books": [b.to_dict() for b in self.books],
            "reservations": [
                {
                    "user": r["user"].username,  # guarda solo el nombre
                    "book": r["book"].title,  # guarda solo el título
                    "date_borrowed": r["date_borrowed"].isoformat(),
                    "date_due": r["date_due"].isoformat(),
                    "active": r["active"],
                }
                for r in self.reservations
            ],
        }
        save_data(data)

    # ---------------------- USUARIOS ----------------------

    def register_user(self, username, role="lector"):
        if any(u.username.lower() == username.lower() for u in self.users):
            return f"⚠️ El usuario '{username}' ya está registrado."
        user = User(username, role)
        self.users.append(user)
        self._save()  # 👈 persistir
        return user

    def find_user(self, username):
        return next((u for u in self.users if u.username.lower() == username.lower()), None)

    # ---------------------- LIBROS ----------------------

    def upload_book(self, title, author, public_domain=True, file_path=None):
        existing = self.find_book(title)
        if existing:
            return f"⚠️ El libro '{title}' ya está registrado."
        book = Book(title, author, public_domain, file_path)
        self.books.append(book)
        self._save()
        return book

    def find_book(self, title):
        return next((b for b in self.books if b.title.lower() == title.lower()), None)

    def list_books(self):
        return self.books

    # ---------------------- PRÉSTAMOS ----------------------

    def borrow_book(self, username, title):
        user = self.find_user(username)
        book = self.find_book(title)

        if not user or not book:
            return "❌ Usuario o libro no encontrado."
        if not book.available:
            return f"❌ El libro '{book.title}' no está disponible actualmente."

        reservation = {
            "user": user,
            "book": book,
            "date_borrowed": datetime.now(),
            "date_due": datetime.now() + timedelta(days=14),
            "active": True
        }

        book.available = False
        self.reservations.append(reservation)
        self._save()  # 👈 persistir

        return (f"📕 {user.username} ha tomado prestado '{book.title}' "
                f"hasta el {reservation['date_due'].strftime('%d/%m/%Y')}.")

    def return_book(self, username, title):
        user = self.find_user(username)
        book = self.find_book(title)

        if not user or not book:
            return "❌ Usuario o libro no encontrado."

        for r in self.reservations:
            if r["user"].username == user.username and r["book"].title == book.title and r["active"]:
                r["active"] = False
                book.available = True
                self._save()  # 👈 persistir
                return f"✅ {user.username} ha devuelto '{book.title}'."

        return "⚠️ No se encontró una reserva activa para ese usuario y libro."

    def review_book(self, username, title, comment, rating):
        """Añade una reseña a un libro."""
        user = self.find_user(username)
        book = self.find_book(title)

        if not user or not book:
            return "❌ Usuario o libro no encontrado."
        if not (1 <= rating <= 5):
            return "⚠️ La puntuación debe estar entre 1 y 5."

        # Añadimos la reseña al libro
        book.add_review({"user": user.username, "comment": comment, "rating": rating})
        self._save()  # 👈 guardar cambios en data.json
        return f"📝 Reseña añadida por {user.username} a '{book.title}'."

    def list_active_reservations(self):
        """Devuelve una lista legible de todos los préstamos activos."""
        activos = [r for r in self.reservations if r["active"]]
        if not activos:
            return "📭 No hay préstamos activos."

        lineas = []
        for r in activos:
            user = r["user"].username if hasattr(r["user"], "username") else r["user"]
            book = r["book"].title if hasattr(r["book"], "title") else r["book"]
            due = r["date_due"].strftime("%d/%m/%Y") if hasattr(r["date_due"], "strftime") else r["date_due"]
            lineas.append(f"📚 {book} → {user} (vence el {due})")

        return "\n".join(lineas)

    def open_borrowed_book(self, username, title):
        """Permite abrir un libro solo si el usuario lo tiene en préstamo activo."""
        user = self.find_user(username)
        book = self.find_book(title)

        if not user or not book:
            return "❌ Usuario o libro no encontrado."

        # Verifica si el usuario tiene ese préstamo activo
        for r in self.reservations:
            user_name = r["user"].username if hasattr(r["user"], "username") else r["user"]
            book_title = r["book"].title if hasattr(r["book"], "title") else r["book"]

            if user_name.lower() == username.lower() and book_title.lower() == title.lower() and r["active"]:
                return book.open_book()

        return "⚠️ No puedes abrir este libro porque no lo tienes en préstamo activo."

    # ---------------------- VISTA PREVIA ----------------------

    def preview_book(self, title):
        """Muestra la vista previa del archivo asociado a un libro."""
        book = self.find_book(title)
        if not book:
            return "❌ Libro no encontrado."
        return book.preview()
