from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent


def docker_command() -> str | None:
    for command in ("docker", "docker.exe"):
        if shutil.which(command) and subprocess.run(
            [command, "info"], capture_output=True, text=True, timeout=15
        ).returncode == 0:
            return command
    return None


def test_postgres_is_healthy_persistent_and_loopback_only() -> None:
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))
    db = compose["services"]["db"]
    assert db["image"].startswith("postgres:16")
    assert db["ports"] == ["127.0.0.1:5433:5432"]
    assert db["healthcheck"]["test"][0:2] == ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
    assert "pgdata:/var/lib/postgresql/data" in db["volumes"]
    assert "./init.sql:/docker-entrypoint-initdb.d/10-init.sql:ro" in db["volumes"]


def test_env_example_contains_no_production_secret() -> None:
    values = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "POSTGRES_USER=bookuser" in values
    assert "POSTGRES_DB=bookdb" in values
    assert "change-me" in values


def test_init_script_creates_notes_table() -> None:
    sql = (ROOT / "init.sql").read_text(encoding="utf-8").lower()
    assert "create table if not exists notes" in sql
    assert "created_at" in sql


def test_readme_contract() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for heading in ("## 從專案根目錄執行", "## 正常流程", "## 負向測試", "## 驗證", "## Reset"):
        assert heading in text


def test_live_compose_config_when_docker_is_available() -> None:
    command = docker_command()
    if command is None:
        pytest.skip("docker/docker.exe daemon 不可用，略過 integration")
    result = subprocess.run(
        [command, "compose", "-f", str(ROOT / "compose.yaml"), "config", "--quiet"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
