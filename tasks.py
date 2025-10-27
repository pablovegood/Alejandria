import os
from invoke import task

def _run_pytest(c, cov=False):
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    cmd = "pytest -v --maxfail=1 --disable-warnings"
    if cov:
        cmd += " --cov=src --cov-report=term-missing"
    c.run(cmd, env=env)

@task
def install(c):
    c.run("pip install -r requirements.txt")

@task
def lint(c):
    c.run("flake8 src/ tests/", warn=True)

@task(name="test")
def run_tests(c):
    _run_pytest(c, cov=False)

@task(pre=[install, lint])
def all(c):
    _run_pytest(c, cov=True)
