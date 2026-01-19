# src/catalog/service.py
import os
import sqlite3
from datetime import datetime
from pathlib import Path
import logging
from src.catalog.schemas import BookDTO

logger = logging.getLogger("alejandria_api")

# DB normal del catálogo (Gutenberg/lo que ya tenías)
DB_PATH = Path(__file__).parent / "book.db"

# DB/dir de los custom books subidos desde admin (en Fly volumen /data)
DATA_DIR = Path(os.getenv("ALEJANDRIA_DATA_DIR", "/data"))
ADMIN_DB_PATH = DATA_DIR / "admin.db"

# Offset para evitar colisiones con IDs Gutenberg
CUSTOM_ID_OFFSET = int(os.getenv("CUSTOM_ID_OFFSET", "1000000000"))


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
    # Helpers custom books
    # -------------------------------------------------------------------------
    def _is_custom_id(self, guten_id: int) -> bool:
        return guten_id >= CUSTOM_ID_OFFSET

    def _custom_real_id(self, guten_id: int) -> int:
        return guten_id - CUSTOM_ID_OFFSET

    def _fetch_custom_books(self, query: str = "", limit: int = 20):
        if not ADMIN_DB_PATH.exists():
            return []

        db = sqlite3.connect(ADMIN_DB_PATH, check_same_thread=False)
        db.row_factory = sqlite3.Row

        q = f"%{query.strip()}%" if query else "%"
        cur = db.execute("""
            SELECT id, title, author, language, created_at
            FROM custom_books
            WHERE LOWER(title) LIKE LOWER(?) OR LOWER(author) LIKE LOWER(?)
            ORDER BY datetime(created_at) DESC
            LIMIT ?;
        """, (q, q, limit))

        rows = cur.fetchall()
        db.close()

        out = []
        for r in rows:
            real_id = int(r["id"])
            guten_id = CUSTOM_ID_OFFSET + real_id

            out.append(BookDTO(
                guten_id=guten_id,
                title=r["title"],
                author=r["author"],
                language=r["language"] or "es",
                has_text=True,
                text_url=f"/catalog/read/{guten_id}",
                downloaded_at=r["created_at"],
            ))

        return out

    def _fetch_custom_book(self, guten_id: int):
        if not ADMIN_DB_PATH.exists():
            return None

        real_id = self._custom_real_id(guten_id)

        db = sqlite3.connect(ADMIN_DB_PATH, check_same_thread=False)
        db.row_factory = sqlite3.Row

        cur = db.execute("""
            SELECT id, title, author, language, created_at
            FROM custom_books
            WHERE id=?;
        """, (real_id,))

        row = cur.fetchone()
        db.close()

        if not row:
            return None

        return BookDTO(
            guten_id=guten_id,
            title=row["title"],
            author=row["author"],
            language=row["language"] or "es",
            has_text=True,
            text_url=f"/catalog/read/{guten_id}",
            downloaded_at=row["created_at"],
        )

    # -------------------------------------------------------------------------
    # Inserción normal
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
    # Búsqueda (normal + custom)
    # -------------------------------------------------------------------------
    def search_books(self, query: str = "", limit: int = 20):
        # 1) normales (tu DB antigua)
        q = f"%{query.strip()}%" if query else "%"
        cur = self.db.execute("""
            SELECT id AS guten_id, title, author, language, text_url, has_text, downloaded_at
            FROM books
            WHERE LOWER(title) LIKE LOWER(?) OR LOWER(author) LIKE LOWER(?)
            LIMIT ?;
        """, (q, q, limit))
        rows = cur.fetchall()
        normal_results = [BookDTO(**dict(r)) for r in rows]

        # 2) custom (admin.db)
        custom_results = self._fetch_custom_books(query=query, limit=limit)

        # 3) merge: primero custom (para que “se vean”)
        results = custom_results + normal_results

        logger.info(f"🔎 Búsqueda '{query}' → {len(results)} resultados (custom={len(custom_results)} / normal={len(normal_results)})")
        return results

    # -------------------------------------------------------------------------
    # Lectura individual (normal o custom)
    # -------------------------------------------------------------------------
    def get_book(self, guten_id: int):
        if self._is_custom_id(guten_id):
            book = self._fetch_custom_book(guten_id)
            if not book:
                logger.warning(f"⚠️ Custom book con ID {guten_id} no encontrado.")
            return book

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
    # Actualización (solo normal)
    # -------------------------------------------------------------------------
    def update_book(self, guten_id: int, **fields):
        if self._is_custom_id(guten_id):
            # si quieres permitir update custom, lo hacemos aparte
            return None

        if not fields:
            return None
        set_clause = ", ".join(f"{k}=?" for k in fields.keys())
        values = list(fields.values()) + [guten_id]
        self.db.execute(f"UPDATE books SET {set_clause} WHERE id=?", values)
        self.db.commit()
        logger.info(f"📝 Libro {guten_id} actualizado con {fields}")
        return self.get_book(guten_id)

    # -------------------------------------------------------------------------
    # Eliminación (solo normal)
    # -------------------------------------------------------------------------
    def delete_book(self, guten_id: int):
        if self._is_custom_id(guten_id):
            return

        self.db.execute("DELETE FROM books WHERE id=?", (guten_id,))
        self.db.commit()
        logger.info(f"❌ Libro {guten_id} eliminado del catálogo.")

    # -------------------------------------------------------------------------
    # Cierre
    # -------------------------------------------------------------------------
    def close(self):
        self.db.close()
