#!/usr/bin/env python3
"""Resolve a repository-relative path and reject escapes."""
import argparse
from pathlib import Path


def resolve_inside(root: Path, value: str) -> Path:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("path must stay relative to the lab")
    return (root / relative).resolve()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="sample/data.txt")
    args = parser.parse_args()
    print(resolve_inside(Path.cwd(), args.path))
