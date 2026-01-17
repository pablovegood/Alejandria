# src/loan/service.py
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import logging

logger = logging.getLogger("alejandria_api")

# ✅ Persistencia: si existe ALEJANDRIA_DATA_DIR (p.ej. /data en Fly), usamos esa carpeta
DATA_DIR = Path(os.getenv("ALEJANDRIA_DATA_DIR", Path(__file__).parent))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "loan.db"
MAX_LOANS_PER_USER = 4   # límite de préstamos


class LoanService:

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

        # ✅ Refuerzo: un libro SOLO puede estar prestado una vez (por cualquier usuario)
        self.db.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_guten_id
        ON loans(guten_id);
        """)

        self.db.commit()

    # -------------------------------------------------------------------------
    # CREAR PRÉSTAMO
    # -------------------------------------------------------------------------
    def create_loan(self, username: str, guten_id: int, title: str, author: str):

        # ✅ 1) No permitir más de 4 préstamos por usuario
        cur = self.db.execute("""
            SELECT COUNT(*) AS total
            FROM loans
            WHERE user_id=?;
        """, (username,))
        total_loans = cur.fetchone()["total"]

        if total_loans >= MAX_LOANS_PER_USER:
            logger.warning(f"⚠️ {username} intentó superar el límite de {MAX_LOANS_PER_USER} préstamos")
            return {
                "ok": False,
                "detail": f"No puedes tener más de {MAX_LOANS_PER_USER} libros en préstamo."
            }

        # ✅ 2) Si el libro ya está prestado por cualquiera, no está disponible
        cur = self.db.execute("""
            SELECT user_id
            FROM loans
            WHERE guten_id=?;
        """, (guten_id,))
        row = cur.fetchone()

        if row:
            if row["user_id"] == username:
                return {"ok": False, "detail": "El usuario ya tiene este libro en préstamo."}

            logger.warning(f"⚠️ {username} intentó tomar un libro NO disponible (ID {guten_id})")
            return {
                "ok": False,
                "detail": "Este libro no está disponible: ya está prestado por otro usuario."
            }

        now = datetime.now(timezone.utc).isoformat()

        try:
            self.db.execute("""
                INSERT INTO loans (user_id, guten_id, title, author, created_at)
                VALUES (?, ?, ?, ?, ?);
            """, (username, guten_id, title, author, now))
            self.db.commit()

        except sqlite3.IntegrityError:
            return {
                "ok": False,
                "detail": "Este libro no está disponible: ya está prestado."
            }

        logger.info(f"✅ Préstamo creado: {username} → {title}")
        return {
            "ok": True,
            "user": username,
            "book": {"guten_id": guten_id, "title": title, "author": author},
            "created_at": now
        }
