# src/auth/service.py
import os
import sqlite3
from pathlib import Path
import bcrypt
from fastapi import HTTPException
from src.auth.schemas import SignupReq, LoginReq
import logging

logger = logging.getLogger("alejandria_api")

# ✅ Persistencia: si existe ALEJANDRIA_DATA_DIR (p.ej. /data en Fly), usamos esa carpeta
DATA_DIR = Path(os.getenv("ALEJANDRIA_DATA_DIR", Path(__file__).parent))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "auth.db"


class AuthService:
    def __init__(self):
        self.db = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self._init_db()
        logger.info(f"🔐 Base de datos de usuarios inicializada en {DB_PATH}")

    # -------------------------------------------------------------------------
    # Inicialización
    # -------------------------------------------------------------------------
    def _init_db(self):
        self.db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        );
        """)
        self.db.commit()

    # -------------------------------------------------------------------------
    # Registro (Signup)
    # -------------------------------------------------------------------------
    def signup(self, req: SignupReq):
        username = req.username.strip()
        password = req.password.strip()

        if not username or not password:
            raise HTTPException(status_code=400, detail="Usuario y contraseña requeridos")

        cur = self.db.execute("SELECT username FROM users WHERE username=?", (username,))
        if cur.fetchone():
            raise HTTPException(status_code=409, detail="El usuario ya existe")

        # Cifrar la contraseña antes de almacenarla
        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        self.db.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed_pw)
        )
        self.db.commit()

        logger.info(f"✅ Usuario '{username}' creado correctamente.")
        return {"ok": True, "username": username}

    # -------------------------------------------------------------------------
    # Inicio de sesión (Login)
    # -------------------------------------------------------------------------
    def login(self, req: LoginReq):
        username = req.username.strip()
        password = req.password.strip()

        cur = self.db.execute("SELECT username, password FROM users WHERE username=?", (username,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

        stored_hash = row["password"]
        if not bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
            raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

        logger.info(f"🔓 Login correcto para '{username}'")
        return {"ok": True, "username": username}

    # -------------------------------------------------------------------------
    # Cierre
    # -------------------------------------------------------------------------
    def close(self):
        self.db.close()
