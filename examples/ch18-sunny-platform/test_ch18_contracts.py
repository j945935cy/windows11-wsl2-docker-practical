from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

import httpx
import pytest
import yaml

ROOT = Path(__file__).resolve().parent


def load_python(relative: str, name: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeStore:
    def __init__(self, ready: bool = True) -> None:
        self.ready = ready
        self.notes: list[dict[str, object]] = []

    def ping(self) -> bool:
        return self.ready

    def create_note(self, body: str) -> dict[str, object]:
        note = {"id": len(self.notes) + 1, "body": body}
        self.notes.append(note)
        return note

    def list_notes(self) -> list[dict[str, object]]:
        return list(self.notes)


def request(app, method: str, path: str, **kwargs) -> httpx.Response:
    async def send() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            return await client.request(method, path, **kwargs)
    return asyncio.run(send())


def test_api_liveness_readiness_and_note_round_trip() -> None:
    module = load_python("app/main.py", "sunny_main")
    store = FakeStore()
    app = module.create_app(store)
    assert request(app, "GET", "/health/live").json() == {"status": "alive"}
    assert request(app, "GET", "/health/ready").json() == {"status": "ready"}
    created = request(app, "POST", "/notes", json={"body": "  sunny day  "})
    assert created.status_code == 201
    assert created.json() == {"id": 1, "body": "sunny day"}
    assert request(app, "GET", "/notes").json() == [{"id": 1, "body": "sunny day"}]


def test_api_negative_contracts() -> None:
    module = load_python("app/main.py", "sunny_main_negative")
    unavailable = module.create_app(FakeStore(ready=False))
    assert request(unavailable, "GET", "/health/ready").status_code == 503
    app = module.create_app(FakeStore())
    assert request(app, "POST", "/notes", json={"body": "   "}).status_code == 422
    assert request(app, "POST", "/notes", json={"body": "x" * 501}).status_code == 422


def test_database_config_reads_password_only_from_file(monkeypatch, tmp_path: Path) -> None:
    secret = tmp_path / "db-password"
    secret.write_text("local-test-password\n", encoding="utf-8")
    monkeypatch.setenv("DB_PASSWORD_FILE", str(secret))
    monkeypatch.setenv("PGHOST", "db")
    monkeypatch.setenv("PGPORT", "5432")
    monkeypatch.setenv("POSTGRES_USER", "sunny")
    monkeypatch.setenv("POSTGRES_DB", "sunny")
    monkeypatch.setenv("POSTGRES_PASSWORD", "must-not-be-used")
    config = load_python("app/main.py", "sunny_config").database_config()
    assert config["password"] == "local-test-password"
    assert config["host"] == "db"
    assert "must-not-be-used" not in config.values()


def test_database_config_fails_closed_for_missing_or_blank_secret(monkeypatch, tmp_path: Path) -> None:
    module = load_python("app/main.py", "sunny_config_negative")
    monkeypatch.delenv("DB_PASSWORD_FILE", raising=False)
    with pytest.raises(RuntimeError, match="DB password file"):
        module.database_config()
    blank = tmp_path / "blank"
    blank.write_text("\n", encoding="utf-8")
    monkeypatch.setenv("DB_PASSWORD_FILE", str(blank))
    with pytest.raises(RuntimeError, match="DB password file"):
        module.database_config()


def test_compose_security_health_and_database_contracts() -> None:
    compose_text = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    compose = yaml.safe_load(compose_text)
    assert compose["name"].startswith("sunny-")
    api, db = compose["services"]["api"], compose["services"]["db"]
    assert api["ports"] == ["127.0.0.1:8018:8000"]
    assert api["depends_on"]["db"]["condition"] == "service_healthy"
    assert api["healthcheck"]["test"][0] == "CMD"
    assert db["healthcheck"]["test"][0] == "CMD-SHELL"
    assert "pgdata:/var/lib/postgresql/data" in db["volumes"]
    assert db["build"]["context"] == "./db"
    assert all("docker-entrypoint-initdb.d" not in mount for mount in db["volumes"])
    assert "ports" not in db
    assert api["secrets"] == ["db_password"]
    assert db["secrets"] == ["db_password"]
    assert api["environment"]["DB_PASSWORD_FILE"] == "/run/secrets/db_password"
    assert db["environment"]["POSTGRES_PASSWORD_FILE"] == "/run/secrets/db_password"
    assert "POSTGRES_PASSWORD" not in api["environment"]
    assert "POSTGRES_PASSWORD" not in db["environment"]
    assert compose["secrets"]["db_password"]["file"] == "${SUNNY_DB_PASSWORD_FILE:-./secrets/db_password.txt}"
    assert ".example" not in compose_text


def test_image_is_non_root_and_has_healthcheck() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "USER app" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert 'CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]' in dockerfile


def test_env_example_and_ignore_contract() -> None:
    env = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "POSTGRES_PASSWORD=" not in env
    assert "DATABASE_URL=" not in env
    assert "SUNNY_DB_PASSWORD_FILE=./secrets/db_password.txt" in env
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in ignored and ".env.*" in ignored and "!.env.example" in ignored
    assert "backups/" in ignored
    assert "secrets/*" in ignored and "!secrets/*.example" in ignored


def test_backup_manifest_and_tamper_detection(tmp_path: Path) -> None:
    module = load_python("scripts/backup_manifest.py", "sunny_manifest")
    archive = tmp_path / "sunny.sql.gz"
    archive.write_bytes(b"valid backup")
    manifest = tmp_path / "manifest.json"
    module.create_manifest(archive, manifest, "sunny", "2026-01-02T03:04:05Z")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1 and len(data["sha256"]) == 64
    assert module.verify_manifest(manifest) == archive
    archive.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="checksum"):
        module.verify_manifest(manifest)


def test_restore_replacement_is_one_database_transaction() -> None:
    text = (ROOT / "scripts" / "restore.sh").read_text(encoding="utf-8")
    assert text.count('"$DOCKER_CMD" compose') == 1
    assert "--single-transaction" in text
    assert text.index("TRUNCATE notes RESTART IDENTITY") < text.index("gzip -cd") < text.index('"$DOCKER_CMD" compose')


def test_reset_is_sunny_scoped_and_requires_confirmation() -> None:
    reset = (ROOT / "scripts" / "reset.sh").read_text(encoding="utf-8")
    assert "--yes-delete-sunny-platform-data" in reset
    assert '[[ "$PROJECT_NAME" != sunny-* ]]' in reset
    assert "down --volumes" in reset
    for name in ("backup.sh", "restore.sh", "reset.sh"):
        result = subprocess.run(["bash", "-n", str(ROOT / "scripts" / name)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr


def test_e2e_script_is_scoped_and_covers_failure_recovery_restore() -> None:
    script = ROOT / "scripts" / "e2e.sh"
    assert script.is_file()
    text = script.read_text(encoding="utf-8")
    assert "sunny-*" in text
    assert "down --volumes --remove-orphans" in text
    assert "/health/live" in text and "/health/ready" in text
    assert "stop db" in text and "start db" in text
    assert "backup.sh" in text and "restore.sh" in text
    assert "negative_status" in text and "after_restore" in text
    assert "bad_restore_status" in text and "after_bad_restore" in text
    assert "token_urlsafe" in text
    assert "db_password.txt" in text
    assert "powershell.exe" in text
    assert "WSLENV=WINDOWS_SECRET/w" in text
    assert "COMPOSE_ENV_FILE" in text
    for name in ("backup.sh", "restore.sh", "reset.sh"):
        script_text = (ROOT / "scripts" / name).read_text(encoding="utf-8")
        assert "COMPOSE_ENV_FILE" in script_text


def test_readme_has_root_normal_negative_verify_reset_and_wsl_case() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for heading in ("## 從專案根目錄執行", "## 正常流程", "## 負向測試", "## 驗證", "## Reset"):
        assert heading in text
    assert "WSL Integration" in text
    assert "docker.exe" in text
    assert "manifest.json" in text


def live_docker_command() -> str | None:
    for command in ("docker", "docker.exe"):
        if shutil.which(command) and subprocess.run(
            [command, "info"], capture_output=True, timeout=15
        ).returncode == 0:
            return command
    return None


def test_live_compose_config_with_available_daemon(tmp_path: Path) -> None:
    command = live_docker_command()
    if command is None:
        pytest.skip("docker/docker.exe daemon 不可用，略過 integration")
    secret = tmp_path / "db-password"
    secret.write_text("integration-only-password\n", encoding="utf-8")
    env = os.environ.copy()
    env["SUNNY_DB_PASSWORD_FILE"] = str(secret)
    result = subprocess.run(
        [command, "compose", "-f", str(ROOT / "compose.yaml"), "config", "--quiet"],
        capture_output=True, text=True, timeout=30, env=env,
    )
    assert result.returncode == 0, result.stderr
