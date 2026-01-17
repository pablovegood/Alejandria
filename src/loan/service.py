# src/loan/service.py
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import logging

logger = logging.getLogger("alejandria_api")

# ✅ CAMBIO CLAVE:
# Antes: si no había env var, guardaba loan.db junto al código (efímero en Fly)
# Ahora: por defecto usamos /data (persistente con Fly Volume mount)
DATA_DIR = Path(os.getenv("ALEJANDRIA_DATA_DIR", "/data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "loan.db"
MAX_LOANS_PER_USER = 4  # límite real de préstamos activos


class LoanService:
    def __init__(self):
        self.db = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.db.row_factory = sqlite3.Row

        # (Opcional pero recomendable para concurrencia)
        self.db.execute("PRAGMA journal_mode=WAL;")
        self.db.execute("PRAGMA busy_timeout=5000;")

        self._init_db()
        logger.info(f"📦 Base de datos de préstamos inicializada en {DB_PATH}")

    def _init_db(self):
        # Tabla de préstamos "activos" = filas existentes
        self.db.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            guten_id INTEGER NOT NULL,
            title TEXT,
            author TEXT,
            created_at TEXT,
            UNIQUE(user_id, guten_id)  -- evita duplicados usuario/libro
        );
        """)

        # Un mismo libro NO puede estar prestado por 2 usuarios a la vez
        self.db.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_guten_id
        ON loans(guten_id);
        """)

        self.db.commit()

    # -------------------------------------------------------------------------
    # AUX: contar préstamos activos por usuario
    # -------------------------------------------------------------------------
    def count_user_loans(self, username: str) -> int:
        cur = self.db.execute("""
            SELECT COUNT(*) AS total
            FROM loans
            WHERE user_id=?;
        """, (username,))
        return int(cur.fetchone()["total"])

    # -------------------------------------------------------------------------
    # LISTAR PRÉSTAMOS
    # -------------------------------------------------------------------------
    def list_loans(self, username: str):
        cur = self.db.execute("""
            SELECT user_id, guten_id, title, author, created_at
            FROM loans
            WHERE user_id=?
            ORDER BY datetime(created_at) DESC;
        """, (username,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]

    # -------------------------------------------------------------------------
    # DEVOLVER LIBRO (eliminar préstamo)
    # -------------------------------------------------------------------------
    def delete_loan(self, username: str, guten_id: int):
        cur = self.db.execute("""
            DELETE FROM loans
            WHERE user_id=? AND guten_id=?;
        """, (username, int(guten_id)))
        self.db.commit()

        if cur.rowcount == 0:
            return {"ok": False, "code": "NOT_FOUND", "detail": "Préstamo no encontrado."}

        logger.info(f"↩ Préstamo devuelto: {username} → {guten_id}")
        return {"ok": True, "detail": "Libro devuelto correctamente."}

    # -------------------------------------------------------------------------
    # CREAR PRÉSTAMO (con límite real + bloqueo)
    # -------------------------------------------------------------------------
    def create_loan(self, username: str, guten_id: int, title: str, author: str):
        guten_id = int(guten_id)

        # ✅ Bloqueo inmediato para que no se cuelen 2 préstamos a la vez
        # (evita condición de carrera si haces clicks rápidos)
        self.db.execute("BEGIN IMMEDIATE;")
        try:
            # ✅ 1) Límite de préstamos por usuario
            total_loans = self.count_user_loans(username)
            if total_loans >= MAX_LOANS_PER_USER:
                self.db.execute("ROLLBACK;")
                logger.warning(f"⚠️ {username} intentó superar el límite ({MAX_LOANS_PER_USER})")
                return {
                    "ok": False,
                    "code": "LIMIT_REACHED",
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
                self.db.execute("ROLLBACK;")
                if row["user_id"] == username:
                    return {
                        "ok": False,
                        "code": "ALREADY_BORROWED",
                        "detail": "El usuario ya tiene este libro en préstamo."
                    }

                logger.warning(f"⚠️ {username} intentó tomar un libro NO disponible (ID {guten_id})")
                return {
                    "ok": False,
                    "code": "NOT_AVAILABLE",
                    "detail": "Este libro no está disponible: ya está prestado por otro usuario."
                }

            now = datetime.now(timezone.utc).isoformat()

            # ✅ 3) Insert
            try:
                self.db.execute("""
                    INSERT INTO loans (user_id, guten_id, title, author, created_at)
                    VALUES (?, ?, ?, ?, ?);
                """, (username, guten_id, title, author, now))
                self.db.commit()

            except sqlite3.IntegrityError:
                self.db.execute("ROLLBACK;")
                return {
                    "ok": False,
                    "code": "NOT_AVAILABLE",
                    "detail": "Este libro no está disponible: ya está prestado."
                }

            logger.info(f"✅ Préstamo creado: {username} → {title}")
            return {
                "ok": True,
                "user": username,
                "book": {"guten_id": guten_id, "title": title, "author": author},
                "created_at": now
            }

        except Exception as e:
            self.db.execute("ROLLBACK;")
            logger.exception(f"❌ Error en create_loan (rollback): {e}")
            raise
