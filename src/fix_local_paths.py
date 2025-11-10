import os
import sqlite3
from datetime import datetime

# ✅ Localiza el proyecto completo sin depender del directorio actual
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # src/
DB_PATH = os.path.join(BASE_DIR, "alejandria.db")      # ← Base dentro de src/
TEXTS_DIR = os.path.join(os.path.dirname(BASE_DIR), "data", "texts")

print(f"📘 Usando base de datos: {DB_PATH}")
print(f"📂 Carpeta de textos: {TEXTS_DIR}")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Verifica que exista el directorio de textos
if not os.path.exists(TEXTS_DIR):
    raise FileNotFoundError(f"No se encontró la carpeta de textos en: {TEXTS_DIR}")

# Lista de archivos locales (solo números)
local_ids = []
for fname in os.listdir(TEXTS_DIR):
    if fname.endswith(".txt"):
        try:
            local_ids.append(int(fname.split(".")[0]))
        except ValueError:
            pass

print(f"📚 Detectados {len(local_ids)} archivos locales en {TEXTS_DIR}")

updated = 0
for book_id in local_ids:
    local_path = os.path.join(TEXTS_DIR, f"{book_id}.txt")
    cur.execute("""
        UPDATE books
        SET text_url = ?,
            has_text = 1,
            downloaded_at = ?
        WHERE id = ?;
    """, (local_path, datetime.utcnow().isoformat(), book_id))
    if cur.rowcount:
        updated += 1

conn.commit()
conn.close()

print(f"✅ {updated} libros actualizados para usar rutas locales.")
