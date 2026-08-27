from __future__ import annotations

import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent


def load_manifest_module():
    path = ROOT / "scripts" / "backup_manifest.py"
    spec = importlib.util.spec_from_file_location("ch17_manifest", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_manifest_records_archive_hash_database_and_schema(tmp_path: Path) -> None:
    archive = tmp_path / "bookdb.sql.gz"
    archive.write_bytes(b"example backup")
    manifest_path = tmp_path / "manifest.json"
    module = load_manifest_module()
    module.create_manifest(archive, manifest_path, "bookdb", "2026-01-02T03:04:05Z")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert data["database"] == "bookdb"
    assert data["archive"] == "bookdb.sql.gz"
    assert len(data["sha256"]) == 64
    assert module.verify_manifest(manifest_path, expected_database="bookdb") == archive
    with pytest.raises(ValueError, match="database"):
        module.verify_manifest(manifest_path, expected_database="otherdb")


def test_manifest_verification_rejects_tampering(tmp_path: Path) -> None:
    archive = tmp_path / "dump.sql.gz"
    archive.write_bytes(b"original")
    manifest = tmp_path / "manifest.json"
    module = load_manifest_module()
    module.create_manifest(archive, manifest, "bookdb", "2026-01-02T03:04:05Z")
    archive.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="checksum"):
        module.verify_manifest(manifest)


def test_readme_uses_build_wait_and_nonexistent_safe_backup_path() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "up --build -d --wait" in readme
    assert "realpath -m ../book-ch17-backups" in readme
    assert "Windows-native" in readme


def test_scripts_are_valid_shell_and_reset_requires_explicit_confirmation() -> None:
    for name in ("backup.sh", "restore.sh", "reset.sh"):
        result = subprocess.run(["bash", "-n", str(ROOT / "scripts" / name)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
    backup = (ROOT / "scripts" / "backup.sh").read_text(encoding="utf-8")
    restore = (ROOT / "scripts" / "restore.sh").read_text(encoding="utf-8")
    assert "umask 077" in backup
    assert "pg_dump" in backup and "-Fc" in backup
    assert "${1:?" in backup
    assert "$ROOT/backups" not in backup
    assert "book_restore" in restore
    assert "pg_restore" in restore
    assert "--single-transaction" in restore
    assert "--exit-on-error" in restore
    assert "-d \"${POSTGRES_DB:-bookdb}\"" not in restore
    assert "--expected-database" in restore
    assert "book-ch17-*" in backup
    assert "book-ch17-*" in restore
    assert '-p "$PROJECT_NAME"' in backup
    assert '-p "$PROJECT_NAME"' in restore
    reset = (ROOT / "scripts" / "reset.sh").read_text(encoding="utf-8")
    assert "--yes-delete-book-ch17-data" in reset
    assert "down --volumes" in reset


def test_restore_rejects_source_equal_to_target_before_manifest_or_docker(tmp_path: Path) -> None:
    docker_log = tmp_path / "docker-called"
    fake_docker = tmp_path / "docker"
    fake_docker.write_text(f"#!/usr/bin/env bash\ntouch {docker_log}\n", encoding="utf-8")
    fake_docker.chmod(0o755)
    missing_manifest = tmp_path / "must-not-be-read.json"
    env = os.environ | {"POSTGRES_DB": "book_restore", "DOCKER_CMD": str(fake_docker)}

    result = subprocess.run(
        ["bash", str(ROOT / "scripts" / "restore.sh"), str(missing_manifest)],
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode != 0
    assert "source database must differ from restore target" in result.stderr
    assert "manifest" not in result.stderr.lower()
    assert not docker_log.exists()


def test_compose_has_named_postgres_volume() -> None:
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))
    assert compose["name"] == "book-ch17"
    db = compose["services"]["db"]
    assert db["image"] == "book-ch17-db:16.4"
    assert db["build"]["dockerfile"] == "examples/ch17-backup-restore/db/Dockerfile"
    assert db["volumes"] == ["pgdata:/var/lib/postgresql/data"]
    assert "healthcheck" in db
    assert "POSTGRES_PASSWORD" not in db["environment"]
    assert db["environment"]["POSTGRES_PASSWORD_FILE"] == "/run/secrets/db_password"
    assert db["secrets"] == ["db_password"]
    assert "CH17_DB_SECRET_FILE:?" in (ROOT / "compose.yaml").read_text(encoding="utf-8")


def test_readme_contract() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for heading in ("## 從專案根目錄執行", "## 正常流程", "## 負向測試", "## 驗證", "## Reset"):
        assert heading in text
    assert "restore.sh" in text and "manifest.json" in text
