# src/admin/router.py
import os
import sqlite3
import secrets
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.security import HTTPBasic, HTTPBasicCredentials


# ============================================================
# Admin credentials (ONLY env vars, NO hardcode)
# ============================================================
security = HTTPBasic()


def _get_admin_creds():
    admin_user = os.getenv("ADMIN_USER")
    admin_pass = os.getenv("ADMIN_PASS")

    if not admin_user or not admin_pass:
        raise HTTPException(
            status_code=503,
            detail="Admin disabled: set ADMIN_USER and ADMIN_PASS environment variables.",
        )
    return admin_user, admin_pass


def require_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    admin_user, admin_pass = _get_admin_creds()

    user_ok = secrets.compare_digest(credentials.username, admin_user)
    pass_ok = secrets.compare_digest(credentials.password, admin_pass)

    if not (user_ok and pass_ok):
        raise HTTPException(status_code=401, detail="Credenciales admin incorrectas.")
    return credentials.username


# ============================================================
# Persistent storage (/data)
# ============================================================
DATA_DIR = Path(os.getenv("ALEJANDRIA_DATA_DIR", "/data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

ADMIN_DB = DATA_DIR / "admin.db"
BOOKS_DIR = DATA_DIR / "custom_books"
BOOKS_DIR.mkdir(parents=True, exist_ok=True)


def get_db(db_path: Path):
    db = sqlite3.connect(db_path, check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL;")
    db.execute("PRAGMA busy_timeout=5000;")
    return db


def _ensure_column(db: sqlite3.Connection, table: str, col: str, ddl: str):
    cur = db.execute(f"PRAGMA table_info({table});")
    cols = {r["name"] for r in cur.fetchall()}
    if col not in cols:
        db.execute(ddl)
        db.commit()


def init_admin_db():
    db = get_db(ADMIN_DB)
    db.execute(
        """
    CREATE TABLE IF NOT EXISTS custom_books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT DEFAULT '',
        language TEXT DEFAULT '',
        created_at TEXT NOT NULL
    );
    """
    )
    db.commit()

    _ensure_column(db, "custom_books", "pdf_path", "ALTER TABLE custom_books ADD COLUMN pdf_path TEXT DEFAULT ''")
    _ensure_column(db, "custom_books", "txt_path", "ALTER TABLE custom_books ADD COLUMN txt_path TEXT DEFAULT ''")

    db.close()


init_admin_db()


# ============================================================
# Helpers: detect DB tables/columns safely
# ============================================================
def _find_existing_db(candidates: list[Path]) -> Path | None:
    return next((p for p in candidates if p.exists()), None)


def _list_tables(db: sqlite3.Connection) -> list[str]:
    cur = db.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [r[0] for r in cur.fetchall()]


def _table_columns(db: sqlite3.Connection, table: str) -> set[str]:
    cur = db.execute(f"PRAGMA table_info({table});")
    return {r[1] for r in cur.fetchall()}  # (cid, name, type...)


def _pick_table(db: sqlite3.Connection, table_candidates: list[str], required_cols: set[str]) -> str | None:
    tables = set(_list_tables(db))
    for t in table_candidates:
        if t in tables:
            cols = _table_columns(db, t)
            if required_cols.issubset(cols):
                return t
    # fallback: try any table that has the required cols
    for t in tables:
        cols = _table_columns(db, t)
        if required_cols.issubset(cols):
            return t
    return None


# ============================================================
# PDF -> TXT conversion
# ============================================================
def pdf_to_txt(pdf_path: Path, txt_path: Path) -> int:
    text = ""

    try:
        import pdfplumber  # type: ignore

        with pdfplumber.open(str(pdf_path)) as pdf:
            pages = []
            for p in pdf.pages:
                pages.append(p.extract_text() or "")
            text = "\n\n".join(pages).strip()
    except Exception:
        text = ""

    if not text:
        try:
            from PyPDF2 import PdfReader  # type: ignore

            reader = PdfReader(str(pdf_path))
            pages = []
            for p in reader.pages:
                pages.append(p.extract_text() or "")
            text = "\n\n".join(pages).strip()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"No se pudo extraer texto del PDF: {e}")

    if not text:
        raise HTTPException(status_code=422, detail="El PDF no contiene texto extraíble (puede ser escaneado).")

    txt_path.write_text(text, encoding="utf-8")
    return len(text)


# ============================================================
# Router
# ============================================================
router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/ping")
def ping_admin(admin: str = Depends(require_admin)):
    return {"ok": True, "admin": admin}


# ============================================================
# ✅ CUSTOM BOOKS: upload PDF -> save pdf + txt
# ============================================================
@router.post("/books/upload")
async def admin_upload_book(
    title: str = Form(...),
    author: str = Form(""),
    language: str = Form(""),
    pdf: UploadFile = File(...),
    admin: str = Depends(require_admin),
):
    if not pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF.")

    now = datetime.now(timezone.utc).isoformat()

    db = get_db(ADMIN_DB)
    cur = db.execute(
        """
        INSERT INTO custom_books (title, author, language, created_at, pdf_path, txt_path)
        VALUES (?, ?, ?, ?, '', '');
        """,
        (title.strip(), author.strip(), language.strip(), now),
    )
    db.commit()
    book_id = int(cur.lastrowid)

    pdf_path = BOOKS_DIR / f"{book_id}.pdf"
    txt_path = BOOKS_DIR / f"{book_id}.txt"

    content = await pdf.read()
    pdf_path.write_bytes(content)

    extracted_chars = pdf_to_txt(pdf_path, txt_path)

    db.execute(
        "UPDATE custom_books SET pdf_path=?, txt_path=? WHERE id=?;",
        (str(pdf_path), str(txt_path), book_id),
    )
    db.commit()
    db.close()

    return {
        "ok": True,
        "id": book_id,
        "created_at": now,
        "extracted_chars": extracted_chars,
    }


@router.get("/books")
def admin_list_books(admin: str = Depends(require_admin)):
    db = get_db(ADMIN_DB)
    cur = db.execute(
        """
        SELECT id, title, author, language, created_at, pdf_path, txt_path
        FROM custom_books
        ORDER BY datetime(created_at) DESC;
        """
    )
    rows = cur.fetchall()
    db.close()
    return [
        {
            **dict(r),
            "has_pdf": bool(r["pdf_path"]),
            "has_txt": bool(r["txt_path"]),
        }
        for r in rows
    ]


@router.delete("/books/{book_id}")
def admin_delete_book(book_id: int, admin: str = Depends(require_admin)):
    db = get_db(ADMIN_DB)
    cur = db.execute("SELECT pdf_path, txt_path FROM custom_books WHERE id=?;", (book_id,))
    row = cur.fetchone()

    if not row:
        db.close()
        raise HTTPException(status_code=404, detail="Libro no encontrado.")

    db.execute("DELETE FROM custom_books WHERE id=?;", (book_id,))
    db.commit()
    db.close()

    for p in [row["pdf_path"], row["txt_path"]]:
        if p:
            try:
                Path(p).unlink(missing_ok=True)
            except Exception:
                pass

    return {"ok": True, "detail": "Libro eliminado."}


# ============================================================
# ✅ USERS: list + search
# ============================================================
@router.get("/users")
def admin_list_users(
    q: str = Query("", description="Buscar por username"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: str = Depends(require_admin),
):
    candidates = [
        DATA_DIR / "users.db",
        DATA_DIR / "auth.db",
        DATA_DIR / "app.db",
        DATA_DIR / "alejandria.db",
    ]
    db_path = _find_existing_db(candidates)
    if not db_path:
        raise HTTPException(status_code=500, detail="No encuentro la base de datos de usuarios en /data.")

    db = get_db(db_path)

    # detectar tabla usuarios
    table = _pick_table(db, ["users", "usuario", "usuarios", "user"], {"username"})
    if not table:
        db.close()
        raise HTTPException(status_code=500, detail="No encuentro tabla de usuarios compatible (username).")

    like = f"%{q.strip()}%"
    if q.strip():
        cur = db.execute(
            f"""
            SELECT username
            FROM {table}
            WHERE username LIKE ?
            ORDER BY username ASC
            LIMIT ? OFFSET ?;
            """,
            (like, limit, offset),
        )
    else:
        cur = db.execute(
            f"""
            SELECT username
            FROM {table}
            ORDER BY username ASC
            LIMIT ? OFFSET ?;
            """,
            (limit, offset),
        )

    rows = cur.fetchall()

    # total count
    if q.strip():
        tcur = db.execute(f"SELECT COUNT(*) AS total FROM {table} WHERE username LIKE ?;", (like,))
    else:
        tcur = db.execute(f"SELECT COUNT(*) AS total FROM {table};")

    total = int(tcur.fetchone()["total"])
    db.close()

    return {
        "items": [dict(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ============================================================
# ✅ REVIEWS: list + search
# ============================================================
@router.get("/reviews")
def admin_list_reviews(
    q: str = Query("", description="Buscar texto de reseña / username"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: str = Depends(require_admin),
):
    candidates = [
        DATA_DIR / "reviews.db",
        DATA_DIR / "review.db",
        DATA_DIR / "app.db",
        DATA_DIR / "alejandria.db",
    ]
    db_path = _find_existing_db(candidates)
    if not db_path:
        raise HTTPException(status_code=500, detail="No encuentro la base de datos de reseñas en /data.")

    db = get_db(db_path)

    # detectar tabla reviews
    table = _pick_table(db, ["reviews", "review"], {"id", "username", "text"})
    if not table:
        db.close()
        raise HTTPException(status_code=500, detail="No encuentro tabla de reseñas compatible (id, username, text).")

    cols = _table_columns(db, table)
    has_guten = "guten_id" in cols
    has_rating = "rating" in cols
    has_created = "created_at" in cols

    # construir select compatible
    fields = ["id", "username", "text"]
    if has_guten:
        fields.append("guten_id")
    if has_rating:
        fields.append("rating")
    if has_created:
        fields.append("created_at")

    select = ", ".join(fields)

    like = f"%{q.strip()}%"
    if q.strip():
        cur = db.execute(
            f"""
            SELECT {select}
            FROM {table}
            WHERE text LIKE ? OR username LIKE ?
            ORDER BY id DESC
            LIMIT ? OFFSET ?;
            """,
            (like, like, limit, offset),
        )
        tcur = db.execute(
            f"""
            SELECT COUNT(*) AS total
            FROM {table}
            WHERE text LIKE ? OR username LIKE ?;
            """,
            (like, like),
        )
    else:
        cur = db.execute(
            f"""
            SELECT {select}
            FROM {table}
            ORDER BY id DESC
            LIMIT ? OFFSET ?;
            """,
            (limit, offset),
        )
        tcur = db.execute(f"SELECT COUNT(*) AS total FROM {table};")

    rows = cur.fetchall()
    total = int(tcur.fetchone()["total"])
    db.close()

    return {
        "items": [dict(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ============================================================
# ✅ REVIEWS delete
# ============================================================
@router.delete("/reviews/{review_id}")
def admin_delete_review(review_id: int, admin: str = Depends(require_admin)):
    candidates = [
        DATA_DIR / "reviews.db",
        DATA_DIR / "review.db",
        DATA_DIR / "app.db",
        DATA_DIR / "alejandria.db",
    ]
    db_path = _find_existing_db(candidates)
    if not db_path:
        raise HTTPException(status_code=500, detail="No encuentro la base de datos de reseñas en /data.")

    db = get_db(db_path)

    table = _pick_table(db, ["reviews", "review"], {"id"})
    if not table:
        db.close()
        raise HTTPException(status_code=500, detail="No encuentro tabla de reseñas compatible (id).")

    cur = db.execute(f"DELETE FROM {table} WHERE id=?;", (int(review_id),))
    db.commit()
    db.close()

    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Reseña no encontrada.")
    return {"ok": True, "detail": "Reseña eliminada."}


def _delete_reviews_for_user(username: str) -> int:
    candidates = [
        DATA_DIR / "reviews.db",
        DATA_DIR / "review.db",
        DATA_DIR / "app.db",
        DATA_DIR / "alejandria.db",
    ]
    db_path = _find_existing_db(candidates)
    if not db_path:
        return 0

    db = get_db(db_path)
    table = _pick_table(db, ["reviews", "review"], {"username"})
    if not table:
        db.close()
        return 0

    cur = db.execute(f"DELETE FROM {table} WHERE username=?;", (username,))
    db.commit()
    deleted = cur.rowcount
    db.close()
    return deleted


# ============================================================
# ✅ USERS delete: deletes user + reviews + returns loans
# ============================================================
def _delete_user_from_users_db(username: str) -> int:
    candidates = [
        DATA_DIR / "users.db",
        DATA_DIR / "auth.db",
        DATA_DIR / "app.db",
        DATA_DIR / "alejandria.db",
    ]
    db_path = _find_existing_db(candidates)
    if not db_path:
        raise HTTPException(status_code=500, detail="No encuentro la base de datos de usuarios en /data.")

    db = get_db(db_path)
    table = _pick_table(db, ["users", "usuario", "usuarios", "user"], {"username"})
    if not table:
        db.close()
        raise HTTPException(status_code=500, detail="No encuentro tabla usuarios compatible (username).")

    cur = db.execute(f"DELETE FROM {table} WHERE username=?;", (username,))
    db.commit()
    deleted = cur.rowcount
    db.close()
    return deleted


def _return_loans_for_user(username: str) -> int:
    loan_db = DATA_DIR / "loan.db"
    if not loan_db.exists():
        return 0

    db = get_db(loan_db)
    table = _pick_table(db, ["loans", "loan"], {"user_id"})
    if not table:
        db.close()
        return 0

    cur = db.execute(f"DELETE FROM {table} WHERE user_id=?;", (username,))
    db.commit()
    returned = cur.rowcount
    db.close()
    return returned


@router.delete("/users/{username}")
def admin_delete_user(username: str, admin: str = Depends(require_admin)):
    username = username.strip()

    returned = _return_loans_for_user(username)
    deleted_reviews = _delete_reviews_for_user(username)

    deleted_users = _delete_user_from_users_db(username)
    if deleted_users == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    return {
        "ok": True,
        "detail": "Usuario eliminado. Préstamos devueltos y reseñas eliminadas.",
        "returned_loans": returned,
        "deleted_reviews": deleted_reviews,
    }
