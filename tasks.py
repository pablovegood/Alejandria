# pytest: skip-file
from invoke import task

@task
def install(c):
    """Instala dependencias."""
    c.run("pip install -r requirements.txt")

@task
def lint(c):
    """Linter básico (opcional si usas flake8)."""
    c.run("flake8 src/ tests/", warn=True)

@task(name="test")
def run_tests(c):
    """Ejecuta pytest."""
    c.run("pytest -v --maxfail=1 --disable-warnings")
