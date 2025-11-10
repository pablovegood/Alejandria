# src/loan/service.py
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import logging

logger = logging.getLogger("alejandria_api")

DB_PATH = Path(__file__).parent / "loan.db"


class LoanService:
    """Gestiona los préstamos locales en su propia base de datos."""

    def __init__(self):
        self.db = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self._init_db()
        logger.info(f"📦 Base de datos de préstamos inicializada en {DB_PATH}")

    def _init_db(self):
        self.db.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            guten_id INTEGER NOT NULL,
            title TEXT,
            author TEXT,
            created_at TEXT,
            UNIQUE(user_id, guten_id)  -- evita duplicados por usuario/libro
        );
        """)
        self.db.commit()

    # -------------------------------------------------------------------------
    # 🆕 CREAR PRÉSTAMO
    # -------------------------------------------------------------------------
    def create_loan(self, username: str, guten_id: int, title: str, author: str):
        """Registra un préstamo nuevo en la base de datos."""
        # Verificar si el usuario ya tiene ese libro
        cur = self.db.execute("""
            SELECT 1 FROM loans WHERE user_id=? AND guten_id=?;
        """, (username, guten_id))
        if cur.fetchone():
            logger.warning(f"⚠️ {username} intentó tomar un libro ya prestado (ID {guten_id})")
            return {
                "ok": False,
                "detail": "El usuario ya tiene este libro en préstamo."
            }

        now = datetime.now(timezone.utc).isoformat()
        self.db.execute("""
            INSERT INTO loans (user_id, guten_id, title, author, created_at)
            VALUES (?, ?, ?, ?, ?);
        """, (username, guten_id, title, author, now))
        self.db.commit()

        logger.info(f"✅ Préstamo creado: {username} → {title}")
        return {
            "ok": True,
            "user": username,
            "book": {"guten_id": guten_id, "title": title, "author": author},
            "created_at": now
        }

    # -------------------------------------------------------------------------
    # 📚 LISTAR PRÉSTAMOS
    # -------------------------------------------------------------------------
    def list_loans(self, username: str):
        """Devuelve todos los préstamos de un usuario."""
        cur = self.db.execute("""
            SELECT * FROM loans
            WHERE user_id=?
            ORDER BY created_at DESC;
        """, (username,))
        loans = [dict(row) for row in cur.fetchall()]
        logger.info(f"📚 {len(loans)} préstamos encontrados para {username}")
        return loans

    # -------------------------------------------------------------------------
    # ↩️ DEVOLVER LIBRO
    # -------------------------------------------------------------------------
    def delete_loan(self, username: str, guten_id: int):
        """Elimina un préstamo por usuario e ID del libro."""
        cur = self.db.execute("""
            SELECT * FROM loans
            WHERE user_id=? AND guten_id=?;
        """, (username, guten_id))
        row = cur.fetchone()
        if not row:
            logger.warning(f"⚠️ {username} intentó devolver un libro no prestado (ID {guten_id})")
            return {"ok": False, "detail": "Este libro no estaba en préstamo."}

        self.db.execute("""
            DELETE FROM loans
            WHERE user_id=? AND guten_id=?;
        """, (username, guten_id))
        self.db.commit()

        logger.info(f"↩️ Préstamo devuelto: {username} ← {guten_id}")
        return {"ok": True, "message": "Libro devuelto correctamente."}
