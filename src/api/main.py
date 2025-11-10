# src/api/main.py
import logging
import time
import os
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from src.auth.router import router as auth_router
from src.catalog.router import router as catalog_router
from src.loan.router import router as loans_router
from src.review.router import router as review_router


# --- Crear carpeta logs si no existe ---
os.makedirs("logs", exist_ok=True)

# --- Configuración de logs ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/alejandria.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("alejandria_api")

# --- Crear instancia principal ---
app = FastAPI(title="Alejandría API")

# --- Middleware de logs ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"➡️  {request.method} {request.url.path}")

    try:
        response = await call_next(request)
    except Exception as e:
        logger.exception(f"❌ Error en {request.url.path}: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

    duration = round(time.time() - start_time, 3)
    logger.info(f"⬅️  {request.method} {request.url.path} | status={response.status_code} | {duration}s")
    return response

# --- Directorios base ---
BASE_DIR = Path(__file__).resolve().parents[2]
STATIC_DIR = BASE_DIR / "web"

# --- RUTA RAÍZ ---
@app.get("/", include_in_schema=False)
async def root():
    """
    Redirige automáticamente al login del frontend.
    Sirve el HTML desde /static/login.html (no el endpoint /login de la API).
    """
    logger.info("🏁 Redirigiendo al login del frontend (static/login.html)")
    return RedirectResponse(url="/static/login.html", status_code=302)

# --- MONTAR CARPETA DE ARCHIVOS ESTÁTICOS ---
# html=True permite servir archivos HTML directamente
app.mount("/static", StaticFiles(directory=STATIC_DIR, html=True), name="static")

# --- INCLUIR ROUTERS ---
app.include_router(auth_router)     # /auth/signup, /auth/login
app.include_router(catalog_router)  # /catalog/search, /catalog/books/{id}
app.include_router(loans_router)    # /loans (GET, POST, DELETE)
app.include_router(review_router)

# --- DEPURACIÓN: Mostrar rutas registradas ---
print("🔍 RUTAS REGISTRADAS EN FASTAPI:")
for route in app.routes:
    if hasattr(route, "methods"):
        print(f"  {route.path:35} {route.methods}")
