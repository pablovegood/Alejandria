import os
import subprocess
import sys

class Book:
    VALID_FORMATS = ('.pdf', '.epub')

    def __init__(self, title, author, public_domain=True, file_path=None):
        self.title = title
        self.author = author
        self.public_domain = public_domain
        self.available = True
        self.reviews = []
        self.file_path = file_path
        if file_path and os.path.exists(file_path):
            self.file_path = file_path

    def attach_file(self, file_path):
        """Asocia un archivo PDF o EPUB al libro, buscando también en la carpeta /data si no se encuentra."""
        # Normaliza separadores y elimina espacios accidentales
        file_path = file_path.strip().replace("\\", "/")

        # Si la ruta no es absoluta, conviértela en absoluta relativa al proyecto
        abs_path = os.path.abspath(file_path)

        # Si el archivo no existe, intenta buscarlo en /data
        if not os.path.exists(abs_path):
            # Ruta alternativa dentro de /data (carpeta del proyecto)
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
            alt_path = os.path.join(base_dir, os.path.basename(file_path))
            if os.path.exists(alt_path):
                abs_path = alt_path
            else:
                raise FileNotFoundError(
                    f"❌ El archivo '{file_path}' no existe ni en la carpeta 'data/'."
                )

        # Validar formato
        if not abs_path.lower().endswith(self.VALID_FORMATS):
            raise ValueError("⚠️ Solo se permiten archivos PDF o EPUB.")

        self.file_path = abs_path
        return f"📎 Archivo '{os.path.basename(abs_path)}' asociado correctamente a '{self.title}'."

    def preview(self, lines=10):
        if not self.file_path:
            return "Este libro no tiene archivo asociado."
        if self.file_path.lower().endswith('.epub'):
            return f"Vista previa no disponible para EPUB: {os.path.basename(self.file_path)}"

        try:
            with open(self.file_path, 'rb') as f:
                chunk = f.read(64 * 1024)
            for enc in ('utf-8', 'utf-8-sig', 'cp1252', 'latin-1'):
                try:
                    text = chunk.decode(enc)
                    break
                except UnicodeDecodeError:
                    text = None
            if text is None:
                return "No se pudo leer el archivo: codificación no reconocida."
            preview_lines = text.splitlines()[:max(1, int(lines))]
            content = "\n".join(preview_lines)
            return f"--- Vista previa de '{self.title}' ---\n{content}\n--- Fin de vista previa ---"
        except Exception as e:
            return f"No se pudo leer el archivo: {e}"

    def add_review(self, review):
        self.reviews.append(review)

    def average_rating(self):
        if not self.reviews:
            return 0
        ratings = [r["rating"] for r in self.reviews]
        return round(sum(ratings) / len(ratings), 2)

    def open_book(self):
        if not self.file_path or not os.path.exists(self.file_path):
            return "❌ Este libro no tiene un archivo válido para abrir."
        ext = os.path.splitext(self.file_path)[1].lower()
        if ext not in self.VALID_FORMATS:
            return f"⚠️ Formato '{ext}' no soportado para apertura."
        try:
            if sys.platform.startswith('darwin'):
                subprocess.run(['open', self.file_path])
            elif os.name == 'nt':
                os.startfile(self.file_path)
            elif os.name == 'posix':
                subprocess.run(['xdg-open', self.file_path])
            else:
                return "⚠️ No se pudo determinar el sistema operativo."
            return f"📖 Abriendo '{os.path.basename(self.file_path)}'..."
        except Exception as e:
            return f"❌ Error al intentar abrir el archivo: {e}"

    # ---------------- SERIALIZACIÓN ----------------
    def to_dict(self):
        """Convierte el libro a un dict serializable en JSON."""
        return {
            "title": self.title,
            "author": self.author,
            "public_domain": self.public_domain,
            "available": self.available,
            "reviews": self.reviews,
            "file_path": self.file_path,
        }

    @classmethod
    def from_dict(cls, data):
        """Crea un objeto Book desde un dict (recuperado del JSON)."""
        book = cls(
            data["title"],
            data["author"],
            data.get("public_domain", True),
            data.get("file_path")
        )
        book.available = data.get("available", True)
        book.reviews = data.get("reviews", [])
        return book

    def __repr__(self):
        return f"Book({self.title}, {self.author})"
