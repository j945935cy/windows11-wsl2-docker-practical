#!/usr/bin/env python3
"""Identify the current execution layer without third-party packages."""
import os
import platform
from pathlib import Path


def detect_layer() -> str:
    if Path("/.dockerenv").exists() or os.environ.get("container"):
        return "container"
    release = platform.release().lower()
    if "microsoft" in release or "wsl" in release:
        return "wsl"
    if platform.system() == "Windows":
        return "windows"
    return "linux-or-other"


if __name__ == "__main__":
    print(f"layer={detect_layer()}")
    print(f"system={platform.system()}")
    print(f"cwd={Path.cwd()}")
