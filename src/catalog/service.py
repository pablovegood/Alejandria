# src/catalog/service.py
import sqlite3
from datetime import datetime
from pathlib import Path
import logging
from src.catalog.schemas import BookDTO

logger = logging.getLogger("alejandria_api")

DB_PATH = Path(__file__).parent / "book.db"


class CatalogService:

    def __init__(self):
        self.db = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self._init_db()
        logger.info(f"📘 Base de datos de catálogo inicializada en {DB_PATH}")

    # -------------------------------------------------------------------------
    # Inicialización
    # -------------------------------------------------------------------------
    def _init_db(self):
        self.db.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY,
            title TEXT,
            author TEXT,
            language TEXT,
            text_url TEXT,
            has_text INTEGER DEFAULT 0,
            downloaded_at TEXT
        );
        """)
        self.db.commit()

    # -------------------------------------------------------------------------
    # Inserción
    # -------------------------------------------------------------------------
    def add_book(self, book_id: int, title: str, author: str,
                 language: str = "es", text_url: str = None, has_text: int = 1):
        now = datetime.utcnow().isoformat()
        self.db.execute("""
            INSERT OR IGNORE INTO books
            (id, title, author, language, text_url, has_text, downloaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (book_id, title, author, language, text_url, has_text, now))
        self.db.commit()
        logger.info(f"✅ Libro añadido: {title} ({author})")

    # -------------------------------------------------------------------------
    # Búsqueda
    # -------------------------------------------------------------------------
    def search_books(self, query: str = "", limit: int = 20):
        q = f"%{query.strip()}%" if query else "%"
        cur = self.db.execute("""
            SELECT id AS guten_id, title, author, language, text_url, has_text, downloaded_at
            FROM books
            WHERE LOWER(title) LIKE LOWER(?) OR LOWER(author) LIKE LOWER(?)
            LIMIT ?;
        """, (q, q, limit))
        rows = cur.fetchall()
        results = [BookDTO(**dict(r)) for r in rows]
        logger.info(f"🔎 Búsqueda '{query}' → {len(results)} resultados")
        return results

    # -------------------------------------------------------------------------
    # Lectura individual
    # -------------------------------------------------------------------------
    def get_book(self, guten_id: int):
        cur = self.db.execute("""
            SELECT id AS guten_id, title, author, language, text_url, has_text, downloaded_at
            FROM books WHERE id=?;
        """, (guten_id,))
        row = cur.fetchone()
        if not row:
            logger.warning(f"⚠️ Libro con ID {guten_id} no encontrado.")
            return None
        return BookDTO(**dict(row))

    # -------------------------------------------------------------------------
    # Actualización
    # -------------------------------------------------------------------------
    def update_book(self, guten_id: int, **fields):
        if not fields:
            return None
        set_clause = ", ".join(f"{k}=?" for k in fields.keys())
        values = list(fields.values()) + [guten_id]
        self.db.execute(f"UPDATE books SET {set_clause} WHERE id=?", values)
        self.db.commit()
        logger.info(f"📝 Libro {guten_id} actualizado con {fields}")
        return self.get_book(guten_id)

    # -------------------------------------------------------------------------
    # Eliminación
    # -------------------------------------------------------------------------
    def delete_book(self, guten_id: int):
        self.db.execute("DELETE FROM books WHERE id=?", (guten_id,))
        self.db.commit()
        logger.info(f"❌ Libro {guten_id} eliminado del catálogo.")

    # -------------------------------------------------------------------------
    # Cierre
    # -------------------------------------------------------------------------
    def close(self):
        self.db.close()
