import asyncio
import aiohttp
import aiosqlite
import os, json, time
from pathlib import Path
from tqdm.asyncio import tqdm
from tenacity import retry, stop_after_attempt, wait_fixed

# =========================
# CONFIGURACIÓN
# =========================
BASE_URL = "https://gutendex.com/books"
DB_PATH = Path(__file__).resolve().parents[1] / "alejandria_pequeña.db"
DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "texts"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CONCURRENCY = 10  # número de descargas simultáneas
RETRIES = 3       # reintentos por error

# =========================
# BASE DE DATOS
# =========================
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY,
    title TEXT,
    author TEXT,
    language TEXT,
    text_url TEXT,
    has_text INTEGER DEFAULT 0,
    downloaded_at TEXT
);
"""

INSERT_BOOK_SQL = """
INSERT OR IGNORE INTO books (id, title, author, language, text_url)
VALUES (?, ?, ?, ?, ?);
"""

UPDATE_BOOK_SQL = """
UPDATE books SET has_text=1, downloaded_at=datetime('now') WHERE id=?;
"""

# =========================
# FUNCIONES PRINCIPALES
# =========================
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_TABLE_SQL)
        await db.commit()

@retry(stop=stop_after_attempt(RETRIES), wait=wait_fixed(2))
async def fetch_json(session, url):
    async with session.get(url) as resp:
        resp.raise_for_status()
        return await resp.json()

@retry(stop=stop_after_attempt(RETRIES), wait=wait_fixed(2))
async def fetch_text(session, url):
    async with session.get(url) as resp:
        resp.raise_for_status()
        return await resp.text()

async def download_text(session, book_id, text_url):
    dest = DATA_DIR / f"{book_id}.txt"
    if dest.exists():
        return  # ya descargado

    try:
        text = await fetch_text(session, text_url)
        dest.write_text(text, encoding="utf-8", errors="ignore")
        return True
    except Exception as e:
        print(f"⚠️ Error descargando {book_id}: {e}")
        return False

async def process_book(session, db, book):
    book_id = book["id"]
    title = book["title"]
    author = ", ".join([a["name"] for a in book.get("authors", [])]) or "Desconocido"
    lang = ", ".join(book.get("languages", [])) or "?"
    formats = book.get("formats", {})

    # Buscar URL de texto
    text_url = formats.get("text/plain; charset=utf-8") \
               or formats.get("text/plain; charset=us-ascii") \
               or next((v for v in formats.values() if v.endswith(".txt")), None)

    await db.execute(INSERT_BOOK_SQL, (book_id, title, author, lang, text_url))

    if text_url:
        ok = await download_text(session, book_id, text_url)
        if ok:
            await db.execute(UPDATE_BOOK_SQL, (book_id,))
    await db.commit()

async def download_all():
    await init_db()

    connector = aiohttp.TCPConnector(limit=CONCURRENCY)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with aiosqlite.connect(DB_PATH) as db:
            page = 1
            total_books = 0
            print("🚀 Iniciando descarga completa de Gutendex...")

            while True:
                url = f"{BASE_URL}?page={page}"
                try:
                    data = await fetch_json(session, url)
                except Exception as e:
                    print(f"❌ Error página {page}: {e}")
                    break

                results = data.get("results", [])
                if not results:
                    break

                for book in tqdm(results, desc=f"Página {page}", unit="libro"):
                    await process_book(session, db, book)
                    total_books += 1

                next_page = data.get("next")
                if not next_page:
                    break
                page += 1

            print(f"\n✅ Descarga completada. Total libros procesados: {total_books}")

if __name__ == "__main__":
    asyncio.run(download_all())
