from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent


def load_app_module():
    path = ROOT / "app" / "main.py"
    spec = importlib.util.spec_from_file_location("ch12_main", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def request(path: str) -> httpx.Response:
    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=load_app_module().app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(path)

    return asyncio.run(send())


def test_root_and_health_endpoints() -> None:
    assert request("/").json() == {"message": "Hello from FastAPI in Docker"}
    assert request("/health").json() == {"status": "ok"}


def test_unknown_route_is_a_real_negative_case() -> None:
    assert request("/missing").status_code == 404


def test_container_runs_as_non_root_and_binds_all_container_interfaces() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "USER app" in dockerfile
    assert 'CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]' in dockerfile


def test_readme_has_root_normal_negative_verify_and_reset() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for heading in ("## 從專案根目錄執行", "## 正常流程", "## 負向測試", "## 驗證", "## Reset"):
        assert heading in text
    assert "examples/ch12-fastapi-container" in text
