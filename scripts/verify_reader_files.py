#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_DIRS = {
    "book", "frontmatter", "parts", "appendices", "assets", "build",
    "notes", "tests", "dist", "store-package", ".venv",
}
FORBIDDEN_SUFFIXES = {".epub"}
FORBIDDEN_NAMES = {"cover.png", "cover.jpg", "manuscript.md", ".env"}
SECRET_PATTERNS = (
    re.compile(r"(?:ghp_|gho_|github_pat_|sk-)[A-Za-z0-9_-]{16,}"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
)


def boundary_issues() -> list[str]:
    issues: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(ROOT)
        if relative.parts[0] in FORBIDDEN_DIRS:
            issues.append(f"forbidden publication directory: {relative}")
        if path.suffix.casefold() in FORBIDDEN_SUFFIXES:
            issues.append(f"forbidden publication artifact: {relative}")
        if path.name.casefold() in FORBIDDEN_NAMES:
            issues.append(f"forbidden file: {relative}")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            issues.append(f"possible secret material: {relative}")
    return issues


def main() -> int:
    issues = boundary_issues()
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--import-mode=importlib", "-q", "examples"],
        cwd=ROOT,
    )
    if result.returncode:
        issues.append(f"example tests failed with exit code {result.returncode}")
    if issues:
        print({"issues": issues})
        return 1
    print("PASS: reader boundary and all example tests verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
