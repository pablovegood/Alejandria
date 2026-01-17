# src/api/main.py
import logging
import os
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.auth.router import router as auth_router
from src.catalog.router import router as catalog_router
from src.loan.router import router as loans_router
from src.review.router import router as review_router
from src.admin.router import router as admin_router

# ============================================================
# Runtime config
# ============================================================
ENV = os.getenv("ENV", "dev").lower()  # dev | prod
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# In cloud it's best practice to log to stdout. We'll only log to file in dev unless forced.
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "0") == "1"
ENABLE_FILE_LOGS = (ENV != "prod") or LOG_TO_FILE


# ============================================================
# Logging
# ============================================================
handlers = [logging.StreamHandler()]

if ENABLE_FILE_LOGS:
    os.makedirs("logs", exist_ok=True)
    handlers.insert(0, logging.FileHandler("logs/alejandria.log", encoding="utf-8"))

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=handlers,
)

logger = logging.getLogger("alejandria_api")


# ============================================================
# App
# ============================================================
app = FastAPI(title="Alejandría API")


# ============================================================
# Observability helpers (optional deps)
#   - prometheus-fastapi-instrumentator  (metrics)
#   - opentelemetry-*                    (traces)
# ============================================================
def _parse_otlp_headers(raw: str | None) -> dict[str, str]:
    """
    OTEL_EXPORTER_OTLP_HEADERS often comes like:
      "Authorization=Basic abcdef...,X-Scope-OrgID=my-org"
    """
    if not raw:
        return {}
    out: dict[str, str] = {}
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def setup_metrics(app_: FastAPI) -> None:
    try:
        from prometheus_fastapi_instrumentator import Instrumentator  # type: ignore

        Instrumentator().instrument(app_).expose(
            app_,
            endpoint="/metrics",
            include_in_schema=False,
        )
        logger.info("✅ Metrics enabled at /metrics (Prometheus format)")
    except Exception as e:
        logger.warning("ℹ️ Metrics not enabled (missing dependency?): %s", e)


def setup_tracing(app_: FastAPI) -> None:
    """
    Enable OpenTelemetry tracing if OTEL_EXPORTER_OTLP_ENDPOINT is set.

    Typical env vars you can set in cloud:
      - OTEL_EXPORTER_OTLP_ENDPOINT="https://.../otlp"
      - OTEL_EXPORTER_OTLP_HEADERS="Authorization=Basic ...."
      - OTEL_SERVICE_NAME="alejandria-api"
    """
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not otlp_endpoint:
        logger.info("ℹ️ Tracing disabled (OTEL_EXPORTER_OTLP_ENDPOINT not set)")
        return

    try:
        from opentelemetry import trace  # type: ignore
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (  # type: ignore
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import (  # type: ignore
            FastAPIInstrumentor,
        )
        from opentelemetry.sdk.resources import Resource  # type: ignore
        from opentelemetry.sdk.trace import TracerProvider  # type: ignore
        from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore

        service_name = os.getenv("OTEL_SERVICE_NAME", "alejandria-api")
        headers = _parse_otlp_headers(os.getenv("OTEL_EXPORTER_OTLP_HEADERS"))

        resource = Resource.create(
            {
                "service.name": service_name,
                "deployment.environment": ENV,
            }
        )

        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, headers=headers)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        FastAPIInstrumentor.instrument_app(app_)
        logger.info("✅ Tracing enabled (OTLP HTTP -> %s)", otlp_endpoint)
    except Exception as e:
        logger.warning("ℹ️ Tracing not enabled (missing dependency/config?): %s", e)


# Enable observability (safe even if deps are missing)
setup_metrics(app)
setup_tracing(app)


# ============================================================
# CORS
# ============================================================
# En despliegue puedes restringirlo a tu dominio. Para el hito, lo dejo abierto.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Request logging middleware
# ============================================================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info("➡️  %s %s", request.method, request.url.path)

    try:
        response = await call_next(request)
    except Exception as e:
        logger.exception("❌ Error en %s: %s", request.url.path, str(e))
        content = {"error": "internal_error"} if ENV == "prod" else {"error": str(e)}
        return JSONResponse(status_code=500, content=content)

    duration = round(time.time() - start_time, 3)
    logger.info("⬅️  %s %s | status=%s | %ss", request.method, request.url.path, response.status_code, duration)
    return response


# ============================================================
# Health endpoint (for cloud checks)
# ============================================================
@app.get("/healthz", include_in_schema=False)
async def healthz():
    return {"status": "ok", "env": ENV}


# ============================================================
# Static frontend
# ============================================================
BASE_DIR = Path(__file__).resolve().parents[2]

# ✅ En despliegue, el frontend debe vivir en la carpeta "web" del repo
# (Dockerfile.api hace COPY web ./web). Si necesitas cambiarlo, usa FRONTEND_DIR.
STATIC_DIR = Path(os.getenv("FRONTEND_DIR", str(BASE_DIR / "web"))).resolve()

if not STATIC_DIR.exists():
    logger.warning("⚠️ STATIC_DIR no existe: %s", STATIC_DIR)

@app.get("/", include_in_schema=False)
async def root():
    logger.info("🏁 Redirigiendo al login del frontend (static/login.html)")
    return RedirectResponse(url="/static/login.html", status_code=302)

# ✅ Página principal del catálogo (post-login)
@app.get("/app", include_in_schema=False)
async def app_home():
    return RedirectResponse(url="/static/index.html", status_code=302)

app.mount("/static", StaticFiles(directory=STATIC_DIR, html=True), name="static")


# ============================================================
# Routers
# ============================================================
app.include_router(auth_router)
app.include_router(catalog_router)
app.include_router(loans_router)
app.include_router(review_router)
app.include_router(admin_router)

# ============================================================
# Debug: list routes (only in dev)
# ============================================================
if ENV != "prod":
    logger.info("🔍 RUTAS REGISTRADAS EN FASTAPI:")
    for route in app.routes:
        if hasattr(route, "methods"):
            logger.info("  %-35s %s", route.path, route.methods)
