# src/admin/router.py
import os
import sqlite3
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field


# ============================================================
# Admin credentials (env override)
# ============================================================
ADMIN_USER = os.getenv("ADMIN_USER", "pablogalvarado")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin")

security = HTTPBasic()


def require_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    user_ok = secrets.compare_digest(credentials.username, ADMIN_USER)
    pass_ok = secrets.compare_digest(credentials.password, ADMIN_PASS)
    if not (user_ok and pass_ok):
        raise HTTPException(status_code=401, detail="Credenciales admin incorrectas.")
    return credentials.username


# ============================================================
# DB (persistente en /data)
# ============================================================
DATA_DIR = Path(os.getenv("ALEJANDRIA_DATA_DIR", "/data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

ADMIN_DB = DATA_DIR / "admin.db"


def get_db():
    db = sqlite3.connect(ADMIN_DB, check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL;")
    db.execute("PRAGMA busy_timeout=5000;")
    return db


def init_admin_db():
    db = get_db()

    # Libros locales añadidos por admin
    db.execute("""
    CREATE TABLE IF NOT EXISTS custom_books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT DEFAULT '',
        language TEXT DEFAULT '',
        text_url TEXT DEFAULT '',
        cover_url TEXT DEFAULT '',
        created_at TEXT NOT NULL
    );
    """)

    db.commit()
    db.close()


init_admin_db()


# ============================================================
# Schemas
# ============================================================
class AdminBookCreate(BaseModel):
    title: str = Field(..., min_length=1)
    author: str = ""
    language: str = ""
    text_url: str = ""     # opcional (url o path del visor)
    cover_url: str = ""    # opcional


# ============================================================
# Router
# ============================================================
router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------------------
# Health check admin (opcional)
# ---------------------------
@router.get("/ping")
def ping_admin(admin: str = Depends(require_admin)):
    return {"ok": True, "admin": admin}


# ============================================================
# ✅ BOOKS (custom)
# ============================================================
@router.post("/books")
def admin_add_book(payload: AdminBookCreate, admin: str = Depends(require_admin)):
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    cur = db.execute("""
        INSERT INTO custom_books (title, author, language, text_url, cover_url, created_at)
        VALUES (?, ?, ?, ?, ?, ?);
    """, (payload.title, payload.author, payload.language, payload.text_url, payload.cover_url, now))
    db.commit()

    book_id = cur.lastrowid
    db.close()

    return {
        "ok": True,
        "id": book_id,
        "created_at": now
    }


@router.get("/books")
def admin_list_books(admin: str = Depends(require_admin)):
    db = get_db()
    cur = db.execute("""
        SELECT id, title, author, language, text_url, cover_url, created_at
        FROM custom_books
        ORDER BY datetime(created_at) DESC;
    """)
    rows = cur.fetchall()
    db.close()
    return [dict(r) for r in rows]


@router.delete("/books/{book_id}")
def admin_delete_book(book_id: int, admin: str = Depends(require_admin)):
    db = get_db()
    cur = db.execute("DELETE FROM custom_books WHERE id=?;", (book_id,))
    db.commit()
    db.close()

    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Libro no encontrado.")
    return {"ok": True, "detail": "Libro eliminado."}


# ============================================================
# ✅ REVIEWS (delete)
# ============================================================
@router.delete("/reviews/{review_id}")
def admin_delete_review(review_id: int, admin: str = Depends(require_admin)):
    """
    ⚠️ IMPORTANTE:
    Esto asume que tu tabla de reseñas se llama 'reviews'
    y que tiene un campo 'id' (INTEGER PRIMARY KEY).
    Si tu review service usa otro nombre, te adapto el query.
    """
    # Intento borrar en /data/reviews.db o donde lo tengas.
    # Como no me has pasado review.service.py, lo hacemos "portable":
    # buscamos una DB common por nombre dentro de /data:
    candidates = [
        DATA_DIR / "reviews.db",
        DATA_DIR / "review.db",
        DATA_DIR / "app.db",
        DATA_DIR / "alejandria.db",
    ]

    db_path = next((p for p in candidates if p.exists()), None)
    if not db_path:
        raise HTTPException(status_code=500, detail="No encuentro la base de datos de reseñas en /data.")

    db = sqlite3.connect(db_path, check_same_thread=False)
    db.row_factory = sqlite3.Row

    # Probamos borrar por id en tabla reviews
    try:
        cur = db.execute("DELETE FROM reviews WHERE id=?;", (review_id,))
        db.commit()
    except sqlite3.Error as e:
        db.close()
        raise HTTPException(status_code=500, detail=f"No se pudo borrar reseña: {e}")

    db.close()

    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Reseña no encontrada.")
    return {"ok": True, "detail": "Reseña eliminada."}


@router.delete("/reviews/book/{guten_id}")
def admin_delete_reviews_by_book(guten_id: int, admin: str = Depends(require_admin)):
    """
    Borra todas las reseñas de un libro por guten_id
    """
    candidates = [
        DATA_DIR / "reviews.db",
        DATA_DIR / "review.db",
        DATA_DIR / "app.db",
        DATA_DIR / "alejandria.db",
    ]

    db_path = next((p for p in candidates if p.exists()), None)
    if not db_path:
        raise HTTPException(status_code=500, detail="No encuentro la base de datos de reseñas en /data.")

    db = sqlite3.connect(db_path, check_same_thread=False)
    db.row_factory = sqlite3.Row

    try:
        cur = db.execute("DELETE FROM reviews WHERE guten_id=?;", (int(guten_id),))
        db.commit()
    except sqlite3.Error as e:
        db.close()
        raise HTTPException(status_code=500, detail=f"No se pudieron borrar reseñas: {e}")

    deleted = cur.rowcount
    db.close()

    return {"ok": True, "deleted": deleted}


# ============================================================
# ✅ USERS (delete)
# ============================================================
@router.delete("/users/{username}")
def admin_delete_user(username: str, admin: str = Depends(require_admin)):
    """
    Elimina usuario + (opcional) sus reseñas.
    Igual que antes: buscamos DB compatible en /data.
    """
    candidates = [
        DATA_DIR / "users.db",
        DATA_DIR / "auth.db",
        DATA_DIR / "app.db",
        DATA_DIR / "alejandria.db",
    ]

    db_path = next((p for p in candidates if p.exists()), None)
    if not db_path:
        raise HTTPException(status_code=500, detail="No encuentro la base de datos de usuarios en /data.")

    db = sqlite3.connect(db_path, check_same_thread=False)
    db.row_factory = sqlite3.Row

    # Intento: tabla 'users' con campo 'username'
    try:
        cur = db.execute("DELETE FROM users WHERE username=?;", (username,))
        db.commit()
    except sqlite3.Error as e:
        db.close()
        raise HTTPException(status_code=500, detail=f"No se pudo borrar el usuario: {e}")

    deleted = cur.rowcount
    db.close()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    reviews_candidates = [
        DATA_DIR / "reviews.db",
        DATA_DIR / "review.db",
        DATA_DIR / "app.db",
        DATA_DIR / "alejandria.db",
    ]
    rdb_path = next((p for p in reviews_candidates if p.exists()), None)
    if rdb_path:
        rdb = sqlite3.connect(rdb_path, check_same_thread=False)
        try:
            rdb.execute("DELETE FROM reviews WHERE username=?;", (username,))
            rdb.commit()
        except Exception:
            pass
        finally:
            rdb.close()

    return {"ok": True, "detail": "Usuario eliminado."}
