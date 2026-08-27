from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

import httpx
import yaml

ROOT = Path(__file__).resolve().parent


def load_module():
    path = ROOT / "app" / "main.py"
    spec = importlib.util.spec_from_file_location("ch16_main", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get(app, path: str) -> httpx.Response:
    async def send() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            return await client.get(path)
    return asyncio.run(send())


def test_liveness_is_independent_of_dependency() -> None:
    app = load_module().create_app(lambda: False)
    assert get(app, "/health/live").json() == {"status": "alive"}


def test_readiness_returns_503_when_dependency_fails() -> None:
    app = load_module().create_app(lambda: False)
    response = get(app, "/health/ready")
    assert response.status_code == 503
    assert response.json()["detail"] == "dependency unavailable"


def test_readiness_returns_ok_when_dependency_works() -> None:
    response = get(load_module().create_app(lambda: True), "/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_docker_and_compose_expose_diagnostic_contracts() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "HEALTHCHECK" in dockerfile
    assert "http://127.0.0.1:8000/health/live" in dockerfile
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))
    service = compose["services"]["app"]
    assert service["ports"] == ["127.0.0.1:8016:8000"]
    assert service["logging"]["options"]["max-size"] == "10m"
    assert service["logging"]["options"]["max-file"] == "3"


def test_readme_contract() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for heading in ("## 從專案根目錄執行", "## 正常流程", "## 負向測試", "## 驗證", "## Reset"):
        assert heading in text
    assert "docker compose logs" in text
