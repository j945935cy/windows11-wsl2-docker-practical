#!/usr/bin/env python3
"""Standard-library static contract verifier for one companion lab."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


def safe_file(root: Path, raw: str) -> Path:
    relative = Path(raw)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe relative path: {raw}")
    candidate = (root / relative).resolve()
    if root.resolve() not in (candidate, *candidate.parents):
        raise ValueError(f"unsafe relative path: {raw}")
    return candidate


def load_contract(root: Path) -> dict[str, Any]:
    path = root / "contract.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data.get("checks"), list) or not data["checks"]:
        raise ValueError("contract checks must be a non-empty list")
    return data


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    try:
        contract = load_contract(root)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [str(exc)]
    for index, check in enumerate(contract["checks"], 1):
        try:
            path = safe_file(root, check["file"])
            text = path.read_text(encoding="utf-8")
        except (KeyError, OSError, UnicodeError, ValueError) as exc:
            errors.append(f"check {index}: {exc}")
            continue
        for fragment in check.get("contains", []):
            if fragment not in text:
                errors.append(f"{check['file']}: missing required fragment {fragment!r}")
        for fragment in check.get("not_contains", []):
            if fragment in text:
                errors.append(f"{check['file']}: forbidden fragment {fragment!r}")
    return errors


def run_integration(root: Path, contract: dict[str, Any], docker_cli: str) -> int:
    commands = contract.get("integration", [])
    if not commands:
        print("SKIP integration: this lab has no Docker integration command")
        return 0
    if shutil.which(docker_cli) is None:
        print(f"SKIP integration: {docker_cli} CLI is unavailable")
        return 0
    ready = subprocess.run([docker_cli, "info"], capture_output=True, text=True, check=False)
    if ready.returncode != 0:
        print("SKIP integration: Docker daemon is unavailable")
        return 0
    cleanup = contract.get("cleanup", [])
    try:
        for command in commands:
            actual = [docker_cli, *command[1:]] if command and command[0] == "docker" else command
            result = subprocess.run(actual, cwd=root, text=True, check=False, timeout=120)
            if result.returncode != 0:
                print(f"FAIL integration: {command!r}")
                return 1
    finally:
        for command in cleanup:
            actual = [docker_cli, *command[1:]] if command and command[0] == "docker" else command
            subprocess.run(actual, cwd=root, capture_output=True, text=True, check=False, timeout=120)
    print("PASS integration")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--integration", action="store_true")
    parser.add_argument("--docker-cli", choices=("docker", "docker.exe"), default="docker")
    args = parser.parse_args()
    root = args.root.resolve()
    errors = validate(root)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print(f"PASS static contract: {root.name}")
    if args.integration:
        return run_integration(root, load_contract(root), args.docker_cli)
    return 0


if __name__ == "__main__":
    sys.exit(main())
