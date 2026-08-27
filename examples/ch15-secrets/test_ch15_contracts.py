from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent


def load_module():
    path = ROOT / "app" / "main.py"
    spec = importlib.util.spec_from_file_location("ch15_main", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_secret_is_read_from_file_and_trimmed(tmp_path: Path) -> None:
    secret = tmp_path / "token"
    secret.write_text("a-strong-example-token\n", encoding="utf-8")
    assert load_module().load_secret(secret) == "a-strong-example-token"


def test_missing_or_short_secret_fails_closed(tmp_path: Path) -> None:
    module = load_module()
    with pytest.raises(RuntimeError, match="secret file"):
        module.load_secret(tmp_path / "missing")
    short = tmp_path / "short"
    short.write_text("tiny", encoding="utf-8")
    with pytest.raises(RuntimeError, match="at least 16"):
        module.load_secret(short)


def test_compose_uses_explicit_secret_mount_not_plain_environment() -> None:
    compose_text = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    compose = yaml.safe_load(compose_text)
    app = compose["services"]["app"]
    assert app["secrets"] == ["api_token"]
    assert "API_TOKEN" not in app.get("environment", {})
    assert compose["secrets"]["api_token"]["file"].startswith("${API_TOKEN_FILE:?")
    assert ":-./secrets/api_token.txt.example" not in compose_text


def test_real_secret_paths_are_ignored_and_only_example_is_tracked() -> None:
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "secrets/*" in ignored
    assert "!secrets/*.example" in ignored
    assert (ROOT / "secrets" / "api_token.txt.example").read_text(encoding="utf-8").strip()


def test_readme_contract() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for heading in ("## 從專案根目錄執行", "## 正常流程", "## 負向測試", "## 驗證", "## Reset"):
        assert heading in text
