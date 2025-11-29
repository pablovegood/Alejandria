# src/persistance.py
"""
Módulo de persistencia general.
Solo mantiene funciones auxiliares de conexión para usos internos o globales.
Cada microservicio (auth, catalog, loan) ahora tiene su propia base de datos independiente.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
import logging

logger = logging.getLogger("alejandria_api")

# Base de datos global (opcional, si algo externo la usa)
DB_PATH = Path("alejandria.db")


# --------------------- CONEXIÓN ---------------------
def init_db():
    """
    Inicializa la base de datos general si no existe.
    En esta versión, no crea tablas (cada microservicio lo hace en su propia DB).
    """
    if not DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        conn.commit()
        conn.close()
        logger.info(f"🗄️ Base de datos general creada en {DB_PATH}")
    else:
        logger.info(f"📁 Base de datos ya existente: {DB_PATH}")


@contextmanager
def get_connection():
    """
    Context manager para abrir una conexión SQLite temporal.
    Se usa para operaciones generales o utilidades de debugging.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()
