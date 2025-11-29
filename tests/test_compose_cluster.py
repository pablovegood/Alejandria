import os
import subprocess
import time

import pytest
import requests

HERE = os.path.dirname(__file__)
COMPOSE_FILE = os.path.join(HERE, "..", "compose.yaml")

# 👇 Solo ejecutamos este test en CI (GitHub Actions)
if os.environ.get("CI") != "true":
    pytest.skip(
        "Test de integración con Docker Compose: solo se ejecuta en CI (entorno CI=true)",
        allow_module_level=True,
    )


def wait_for(url: str, timeout: int = 40):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                return
        except Exception:
            time.sleep(1)
    raise RuntimeError(f"Service {url} did not become ready")


def test_compose_cluster_serves_catalog():
    subprocess.run(
        ["docker", "compose", "-f", COMPOSE_FILE, "up", "-d", "--build"],
        check=True,
    )

    try:
        wait_for("http://localhost:8000/openapi.json")

        r = requests.get("http://localhost:8000/catalog/search?q=", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert "results" in data
    finally:
        subprocess.run(
            ["docker", "compose", "-f", COMPOSE_FILE, "down", "-v"],
            check=True,
        )
