from __future__ import annotations

import importlib.util
import json
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
    assert module.verify_manifest(manifest_path) == archive


def test_manifest_verification_rejects_tampering(tmp_path: Path) -> None:
    archive = tmp_path / "dump.sql.gz"
    archive.write_bytes(b"original")
    manifest = tmp_path / "manifest.json"
    module = load_manifest_module()
    module.create_manifest(archive, manifest, "bookdb", "2026-01-02T03:04:05Z")
    archive.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="checksum"):
        module.verify_manifest(manifest)


def test_scripts_are_valid_shell_and_reset_requires_explicit_confirmation() -> None:
    for name in ("backup.sh", "restore.sh", "reset.sh"):
        result = subprocess.run(["bash", "-n", str(ROOT / "scripts" / name)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
    reset = (ROOT / "scripts" / "reset.sh").read_text(encoding="utf-8")
    assert "--yes-delete-book-ch17-data" in reset
    assert "down --volumes" in reset


def test_compose_has_named_postgres_volume() -> None:
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))
    assert compose["name"] == "book-ch17"
    db = compose["services"]["db"]
    assert "pgdata:/var/lib/postgresql/data" in db["volumes"]
    assert "healthcheck" in db


def test_readme_contract() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for heading in ("## 從專案根目錄執行", "## 正常流程", "## 負向測試", "## 驗證", "## Reset"):
        assert heading in text
    assert "restore.sh" in text and "manifest.json" in text
