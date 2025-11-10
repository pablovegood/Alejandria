# server.py
from fastapi import FastAPI
from src.persistance import init_db
from src.api.main import app as alejandria_app

# Inicializa la base de datos si no existe
init_db()

app = alejandria_app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5030)
