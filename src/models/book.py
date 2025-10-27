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
        self.file_path = None

        if file_path:
            self.attach_file(file_path)

    def attach_file(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"El archivo '{file_path}' no existe.")
        if not file_path.lower().endswith(self.VALID_FORMATS):
            raise ValueError("Solo se permiten archivos PDF o EPUB.")
        self.file_path = file_path
        return f"Archivo '{os.path.basename(file_path)}' asociado correctamente a '{self.title}'."

    def preview(self, lines=10):
        """Muestra una vista previa del archivo asociado intentando varias decodificaciones."""
        if not self.file_path:
            return "Este libro no tiene archivo asociado."
        if self.file_path.lower().endswith('.epub'):
            return f"Vista previa no disponible para EPUB: {os.path.basename(self.file_path)}"

        try:
            # Lee solo una porción (p.ej., 64 KB) para la vista previa
            with open(self.file_path, 'rb') as f:
                chunk = f.read(64 * 1024)

            # Intenta varias codificaciones comunes en Windows
            for enc in ('utf-8', 'utf-8-sig', 'cp1252', 'latin-1'):
                try:
                    text = chunk.decode(enc)
                    break
                except UnicodeDecodeError:
                    text = None

            if text is None:
                return "No se pudo leer el archivo: codificación no reconocida."

            # Toma las primeras N líneas “reales”
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
        """Abre el archivo del libro con el visor por defecto del sistema."""
        if not self.file_path or not os.path.exists(self.file_path):
            return "❌ Este libro no tiene un archivo válido para abrir."

        ext = os.path.splitext(self.file_path)[1].lower()
        if ext not in self.VALID_FORMATS:
            return f"⚠️ Formato '{ext}' no soportado para apertura."

        try:
            if sys.platform.startswith('darwin'):  # macOS
                subprocess.run(['open', self.file_path])
            elif os.name == 'nt':  # Windows
                os.startfile(self.file_path)
            elif os.name == 'posix':  # Linux
                subprocess.run(['xdg-open', self.file_path])
            else:
                return "⚠️ No se pudo determinar el sistema operativo."

            return f"📖 Abriendo '{os.path.basename(self.file_path)}'..."
        except Exception as e:
            return f"❌ Error al intentar abrir el archivo: {e}"
