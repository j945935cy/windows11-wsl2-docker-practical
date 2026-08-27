#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_DIRS = {"book", "frontmatter", "appendices", "build", "manuscript"}
FORBIDDEN_SUFFIXES = {".epub"}
FORBIDDEN_NAMES = {"cover.png", "cover.jpg", ".env"}


def main() -> int:
    issues: list[str] = []
    for path in ROOT.rglob("*"):
        if ".git" in path.parts or not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if relative.parts[0] in FORBIDDEN_DIRS:
            issues.append(f"forbidden publication directory: {relative}")
        if path.suffix.casefold() in FORBIDDEN_SUFFIXES:
            issues.append(f"forbidden publication artifact: {relative}")
        if path.name.casefold() in FORBIDDEN_NAMES:
            issues.append(f"forbidden file: {relative}")

    test_dir = ROOT / "examples" / "ch01-environment-layers" / "tests"
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(test_dir), "-v"],
        cwd=ROOT,
    )
    if result.returncode:
        issues.append(f"unit tests failed with exit code {result.returncode}")

    print({"tests": 7, "issues": issues})
    if issues:
        return 1
    print("PASS: reader files verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
