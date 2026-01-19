# src/catalog/router.py
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import PlainTextResponse
from pathlib import Path
import logging
from src.catalog.service import CatalogService

logger = logging.getLogger("alejandria_api")

router = APIRouter(prefix="/catalog", tags=["catalog"])
service = CatalogService()

TEXT_DIR = Path(__file__).resolve().parents[2] / "data" / "texts"


# -------------------------------------------------------------------------
# Búsqueda de libros
# -------------------------------------------------------------------------
@router.get("/search")
def search_books(q: str = Query("", alias="q")):
    try:
        results = service.search_books(query=q)
        return {"results": [r.model_dump() for r in results]}
    except Exception as e:
        logger.exception(f"❌ Error en búsqueda: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------------------------------
# Obtener un libro
# -------------------------------------------------------------------------
@router.get("/{guten_id}")
def get_book(guten_id: int):
    book = service.get_book(guten_id)
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return book.dict()


# -------------------------------------------------------------------------
# Leer texto de libro
# -------------------------------------------------------------------------
@router.get("/read/{guten_id}")
def read_book(guten_id: int):
    import os

    DATA_DIR = Path(os.getenv("ALEJANDRIA_DATA_DIR", "/data"))
    CUSTOM_BOOKS_DIR = DATA_DIR / "custom_books"
    CUSTOM_ID_OFFSET = int(os.getenv("CUSTOM_ID_OFFSET", "1000000000"))

    # Si es custom -> leer /data/custom_books/{real_id}.txt
    if guten_id >= CUSTOM_ID_OFFSET:
        real_id = guten_id - CUSTOM_ID_OFFSET
        book_path = CUSTOM_BOOKS_DIR / f"{real_id}.txt"
    else:
        # normal -> leer data/texts/{guten_id}.txt
        base_path = Path(__file__).resolve().parents[2] / "data" / "texts"
        book_path = base_path / f"{guten_id}.txt"

    if not book_path.exists():
        raise HTTPException(status_code=404, detail="Texto no disponible")

    try:
        with open(book_path, "r", encoding="utf-8") as f:
            content = f.read()
        return PlainTextResponse(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer archivo: {str(e)}")

# -------------------------------------------------------------------------
# Actualizar libro
# -------------------------------------------------------------------------
@router.put("/{guten_id}")
def update_book(guten_id: int, title: str = None, author: str = None, language: str = None):
    updated = service.update_book(guten_id, **{k: v for k, v in locals().items() if v})
    if not updated:
        raise HTTPException(status_code=404, detail="Libro no encontrado o sin cambios.")
    return updated.dict()


# -------------------------------------------------------------------------
# Eliminar libro
# -------------------------------------------------------------------------
@router.delete("/{guten_id}")
def delete_book(guten_id: int):
    service.delete_book(guten_id)
    return {"message": f"Libro {guten_id} eliminado correctamente."}
