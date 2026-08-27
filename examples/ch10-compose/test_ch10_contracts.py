from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent


def load_compose() -> dict:
    return yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))


def docker_command() -> str | None:
    for command in ("docker", "docker.exe"):
        if shutil.which(command) and subprocess.run(
            [command, "info"], capture_output=True, text=True, timeout=15
        ).returncode == 0:
            return command
    return None


def test_compose_combines_web_and_checker_with_health_dependency() -> None:
    compose = load_compose()
    services = compose["services"]
    assert set(services) == {"web", "checker"}
    assert services["checker"]["profiles"] == ["verify"]
    assert services["checker"]["depends_on"]["web"]["condition"] == "service_healthy"
    assert services["web"]["healthcheck"]["test"][0] == "CMD"
    assert services["web"]["ports"] == ["127.0.0.1:8000:8000"]
    assert "http://web:8000/" in " ".join(services["checker"]["command"])


def test_readme_documents_root_commands_and_four_workflows() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for heading in ("## 從專案根目錄執行", "## 正常流程", "## 負向測試", "## 驗證", "## Reset"):
        assert heading in text
    assert "-p book-ch10" in text
    assert "-f examples/ch10-compose/compose.yaml" in text


def test_site_has_published_expected_text() -> None:
    text = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
    assert "Compose is ready" in text


def test_dockerfile_uses_exec_form_command() -> None:
    text = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert 'CMD ["python", "-m", "http.server", "8000", "--directory", "/site"]' in text


def test_compose_is_accepted_by_live_docker() -> None:
    command = docker_command()
    if command is None:
        pytest.skip("Docker CLI 或 daemon 不可用；略過 integration，靜態測試仍會執行")
    result = subprocess.run(
        [command, "compose", "-f", str(ROOT / "compose.yaml"), "config", "--quiet"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
