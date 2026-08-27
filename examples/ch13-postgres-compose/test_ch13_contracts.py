from __future__ import annotations

import os
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


def test_api_and_postgres_share_private_service_network_contract() -> None:
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))
    assert set(compose["services"]) == {"api", "db", "migrate"}
    db = compose["services"]["db"]
    api = compose["services"]["api"]
    migrate = compose["services"]["migrate"]
    assert db["image"] == "book-ch13-db:16.4"
    assert db["build"]["dockerfile"] == "examples/ch13-postgres-compose/db/Dockerfile"
    assert "ports" not in db
    assert db["environment"]["POSTGRES_PASSWORD_FILE"] == "/run/secrets/db_password"
    assert "POSTGRES_PASSWORD" not in db["environment"]
    assert db["volumes"] == ["pgdata:/var/lib/postgresql/data"]
    assert "healthcheck" in db
    assert api["ports"] == ["127.0.0.1:8013:8000"]
    assert api["environment"]["PGHOST"] == "db"
    assert api["environment"]["PGPASSWORD_FILE"] == "/run/secrets/db_password"
    assert api["depends_on"]["db"]["condition"] == "service_healthy"
    assert api["secrets"] == db["secrets"] == ["db_password"]
    assert migrate["profiles"] == ["migrate"]
    assert migrate["build"] == {
        "context": "../..",
        "dockerfile": "examples/ch13-postgres-compose/migrations/Dockerfile",
    }
    assert migrate["depends_on"]["db"]["condition"] == "service_healthy"
    migrate_command = " ".join(migrate["command"])
    assert migrate["environment"]["MIGRATION_FILE"] == "${MIGRATION_FILE:-0002_add_source.sql}"
    assert "-f /migrations/0002_add_source.sql" not in migrate_command
    assert "MIGRATION_PATH=/migrations/$$MIGRATION_FILE" in migrate_command
    assert 'psql --set ON_ERROR_STOP=1 -f "$$MIGRATION_PATH"' in migrate_command
    assert "grep -Eq" in migrate_command
    assert "^[0-9]{4}_[a-z0-9_]+\\.sql$" in migrate_command
    assert '-f "$$MIGRATION_PATH"' in migrate_command
    assert "eval" not in migrate_command
    assert "export PGPASSWORD=" not in migrate_command
    assert "umask 077" in migrate_command
    assert "mktemp" in migrate_command
    assert "chmod 600" in migrate_command
    assert "PGPASSFILE" in migrate_command
    assert "trap" in migrate_command and "rm -f" in migrate_command
    assert "printf '%s:%s:%s:%s:%s\\n'" in migrate_command
    assert migrate["secrets"] == ["db_password"]
    assert "CH13_DB_SECRET_FILE:?" in (ROOT / "compose.yaml").read_text(encoding="utf-8")


def test_committed_priority_migration_has_bounded_non_null_default() -> None:
    sql = (ROOT / "migrations" / "0003_add_priority.sql").read_text(encoding="utf-8")
    normalized = " ".join(sql.lower().split())
    assert "alter table notes" in normalized
    assert "add column if not exists priority smallint not null default 0" in normalized
    assert "check(prioritybetween0and5)" in normalized.replace(" ", "")


def test_migration_readme_rebuilds_and_runs_0003() -> None:
    expected_run = (
        "--profile migrate run --build --rm "
        "-e MIGRATION_FILE=0003_add_priority.sql migrate"
    )
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert expected_run in " ".join(readme.split())
    assert "information_schema.columns" in readme
    assert "column_name='priority'" in readme


def test_image_uses_root_lock_non_root_user_and_healthcheck() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY requirements-lock.txt" in dockerfile
    assert "USER app" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "/health/live" in dockerfile
    ignore = (ROOT.parents[1] / ".dockerignore").read_text(encoding="utf-8")
    for pattern in (".git", ".venv", "build", "**/.env.*", "**/secrets", "**/backups", "**/*.key"):
        assert pattern in ignore


def test_application_has_live_ready_and_notes_contract() -> None:
    source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    assert '@app.get("/health/live")' in source
    assert '@app.get("/health/ready")' in source
    assert '@app.post("/notes", status_code=201)' in source
    assert 'os.environ["PGHOST"]' in source
    assert "PGPASSWORD_FILE" in source
    assert "DATABASE_URL" not in source


def test_init_script_creates_notes_table_with_nonblank_constraint() -> None:
    sql = (ROOT / "init.sql").read_text(encoding="utf-8").lower()
    assert "create table if not exists notes" in sql
    assert "check (length(trim(body)) > 0)" in sql


def test_readme_contract() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for heading in ("## 從專案根目錄執行", "## 正常流程", "## 負向測試", "## 驗證", "## Reset"):
        assert heading in text
    assert "127.0.0.1:8013" in text
    assert "db 不發布" in text


def test_live_compose_config_when_docker_is_available(tmp_path: Path) -> None:
    command = docker_command()
    if command is None:
        pytest.skip("docker/docker.exe daemon 不可用，略過 compose config")
    secret = tmp_path / "db-password.txt"
    secret.write_text("synthetic-ch13-test-password\n", encoding="utf-8")
    env = os.environ | {"CH13_DB_SECRET_FILE": str(secret)}
    if command.endswith(".exe"):
        inherited = env.get("WSLENV", "")
        env["WSLENV"] = ":".join(filter(None, (inherited, "CH13_DB_SECRET_FILE/p")))
    result = subprocess.run(
        [command, "compose", "-f", str(ROOT / "compose.yaml"), "config", "--quiet"],
        env=env, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
