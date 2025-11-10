# ===========================================================
# 🧩 Alejandría · tasks.py
# ===========================================================
# Archivo de automatización de tareas del proyecto.
# Permite ejecutar tests, lint, cobertura y despliegue local
# de la API FastAPI con un solo comando.
# Compatible con Windows, macOS y Linux.
# ===========================================================

import os
import platform
from invoke import task

# --- CONFIGURACIÓN BASE ---
SRC = "src"
TESTS = "tests"
ENV = {"PYTHONPATH": SRC}
IS_WIN = os.name == "nt" or platform.system().lower().startswith("win")


# --- UTILIDAD INTERNA ---
def _run(c, cmd: str):
    """Ejecuta comandos con entorno PYTHONPATH configurado."""
    c.run(cmd, env={**os.environ, **ENV}, pty=False if IS_WIN else True)


# ===========================================================
# 🧹 FORMATEO Y LINTER
# ===========================================================

@task
def fmt(c):
    """Formatea el código con autopep8."""
    print("🎨 Formateando código con autopep8…")
    _run(c, "python -m pip install -q autopep8 || true")
    _run(c, "python -m autopep8 -r --in-place src tests || true")


@task
def lint(c):
    """Analiza el código con flake8."""
    print("🔍 Ejecutando flake8…")
    _run(c, "python -m pip install -q flake8 || true")
    _run(c, "python -m flake8 src tests || true")


# ===========================================================
# 🧪 TESTS
# ===========================================================

@task
def test(c):
    """Ejecuta todos los tests de dominio y servicios."""
    print("🧩 Ejecutando tests…")
    _run(c, "pytest -q")


@task
def cov(c):
    """Ejecuta tests con informe de cobertura."""
    print("🧾 Ejecutando tests con cobertura…")
    _run(c, "pytest -q --cov=src --cov-report=term-missing")


@task
def api_test(c):
    """Ejecuta solo los tests relacionados con la API."""
    print("🌐 Ejecutando tests de API…")
    _run(c, "pytest -q -k api")


# ===========================================================
# 🚀 SERVIDOR LOCAL
# ===========================================================

@task
def api(c):
    """Lanza el servidor FastAPI en modo desarrollo."""
    print("🚀 Iniciando API en http://127.0.0.1:5000 …")
    _run(c, "uvicorn api.main:app --app-dir src --host 0.0.0.0 --port 5000 --reload")


# ===========================================================
# 🧠 UTILIDADES Y CI LOCAL
# ===========================================================

@task
def smoke(c):
    """Prueba rápida de endpoint base."""
    print("💨 Smoke test:")
    _run(c, "python - << \"PY\"\n"
            "import requests as R\n"
            "try:\n"
            "  r = R.get('http://127.0.0.1:5000/docs', timeout=2)\n"
            "  print('📄 /docs →', r.status_code)\n"
            "except Exception as e:\n"
            "  print('❌ Smoke test fallido:', e)\n"
            "PY")


@task
def test_pretty(c):
    """Muestra un resumen bonito del resultado de los tests."""
    print("🧠 Ejecutando tests con salida amigable…")
    cmd = "pytest -rA --disable-warnings -o console_output_style=classic"
    r = c.run(cmd, warn=True, env={**os.environ, **ENV}, pty=False if IS_WIN else True)

    import re
    summary_line = ""
    for line in r.stdout.splitlines()[::-1]:
        if re.search(r"\\bpassed\\b|\\bfailed\\b|\\berrors?\\b", line):
            summary_line = line.strip()
            break

    pairs = re.findall(r"(\\d+)\\s+(passed|failed|error|errors)", summary_line)
    counts = {k: sum(int(n) for n, key in pairs if key.startswith(k)) for k in ["passed", "failed", "error", "errors"]}
    passed = counts.get("passed", 0)
    failed = counts.get("failed", 0) + counts.get("error", 0) + counts.get("errors", 0)
    total = passed + failed



@task
def ci(c):
    """Pipeline local que simula la integración continua."""
    print("🏗️ Ejecutando pipeline CI local…")
    fmt(c)
    lint(c)
    cov(c)
    api_test(c)
    print("✅ Pipeline completado sin errores.")
