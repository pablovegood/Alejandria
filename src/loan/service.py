import os
import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("alejandria_api")

# Carpeta donde se guardará loan.db
DATA_DIR = Path(os.getenv("ALEJANDRIA_DATA_DIR", Path(__file__).parent))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "loan.db"
MAX_LOANS_PER_USER = 4


class LoanService:
    def __init__(self, db_path: Path | str = DB_PATH) -> None:
        self.db_path = Path(db_path)
        try:
            self._init_db()
        except sqlite3.OperationalError as exc:
            # En Fly debería poder escribir sin problema; este try/except
            # es más por si ejecutas en modo solo-lectura.
            logger.warning(
                "No se pudo inicializar la base de datos de préstamos: %s", exc
            )

    # ---------- helpers internos ----------

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Crea la tabla si no existe y el índice único."""
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS loans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id   TEXT    NOT NULL,
                    guten_id  INTEGER NOT NULL,
                    title     TEXT,
                    author    TEXT,
                    created_at TEXT
                )
                """
            )

            # Un mismo usuario no puede tener el mismo libro dos veces
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_loans_user_book
                ON loans(user_id, guten_id)
                """
            )
            conn.commit()

        logger.info("📚 LoanService inicializado con DB %s", self.db_path)

    # ---------- API pública usada por los routers ----------

    def create_loan(self, username: str, guten_id: int, title: str, author: str) -> dict:
        username = username.strip()
        if not username:
            return {"ok": False, "detail": "Nombre de usuario no válido."}

        with self._get_conn() as conn:
            cur = conn.cursor()

            # 1) número de préstamos activos del usuario
            cur.execute(
                "SELECT COUNT(*) FROM loans WHERE user_id = ?",
                (username,),
            )
            active_count = cur.fetchone()[0]
            if active_count >= MAX_LOANS_PER_USER:
                logger.info(
                    "🚫 Límite de préstamos alcanzado para %s (%s/%s)",
                    username,
                    active_count,
                    MAX_LOANS_PER_USER,
                )
                return {
                    "ok": False,
                    "detail": f"Has alcanzado el máximo de {MAX_LOANS_PER_USER} préstamos activos.",
                    "active_count": active_count,
                    "max_loans": MAX_LOANS_PER_USER,
                }

            # 2) ¿ya tiene ese libro en préstamo?
            cur.execute(
                "SELECT id FROM loans WHERE user_id = ? AND guten_id = ?",
                (username, guten_id),
            )
            if cur.fetchone():
                return {
                    "ok": False,
                    "detail": "Ya tienes este libro en préstamo.",
                }

            # 3) crear el préstamo
            now = datetime.now(timezone.utc).isoformat()
            try:
                cur.execute(
                    """
                    INSERT INTO loans (user_id, guten_id, title, author, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (username, guten_id, title, author, now),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                # por si el índice único salta en una carrera rara
                return {
                    "ok": False,
                    "detail": "Este libro no está disponible: ya está prestado.",
                }

        logger.info("✅ Préstamo creado: %s → %s", username, title)
        return {
            "ok": True,
            "user": username,
            "book": {
                "guten_id": guten_id,
                "title": title,
                "author": author,
            },
            "created_at": now,
        }

    def get_user_loans(self, username: str) -> dict:
        """Devuelve todos los préstamos activos + resumen para el usuario."""
        username = username.strip()
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, user_id, guten_id, title, author, created_at
                FROM loans
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (username,),
            )
            rows = [dict(row) for row in cur.fetchall()]

        active_count = len(rows)
        return {
            "ok": True,
            "user": username,
            "active_count": active_count,
            "max_loans": MAX_LOANS_PER_USER,
            "loans": rows,
        }

    def get_all_loans(self) -> list[dict]:
        """Solo por si algún día quieres listarlos en admin."""
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, user_id, guten_id, title, author, created_at
                FROM loans
                ORDER BY created_at DESC
                """
            )
            return [dict(row) for row in cur.fetchall()]

    def delete_loan(self, username: str, guten_id: int) -> dict:
        username = username.strip()
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM loans WHERE user_id = ? AND guten_id = ?",
                (username, guten_id),
            )
            deleted = cur.rowcount
            conn.commit()

        if not deleted:
            return {
                "ok": False,
                "detail": "No se encontró un préstamo activo para este usuario y libro.",
            }

        logger.info("↩ Préstamo devuelto: %s, book %s", username, guten_id)
        return {"ok": True}
