#!/usr/bin/env python3
"""辨識命令目前位於 Windows、WSL、container 或一般 Linux。"""

from __future__ import annotations

import json
import os
import platform
from pathlib import Path
from typing import Mapping


def classify_environment(
    *,
    system: str,
    proc_version: str,
    environ: Mapping[str, str],
    docker_env_exists: bool,
    cgroup_text: str,
) -> str:
    """依可觀察訊號分類執行層；container 優先於 WSL。"""
    normalized_system = system.casefold()
    normalized_kernel = proc_version.casefold()
    normalized_cgroup = cgroup_text.casefold()

    in_container = docker_env_exists or any(
        marker in normalized_cgroup
        for marker in ("docker", "containerd", "kubepods", "podman", "libpod")
    )
    if in_container:
        return "container"

    in_wsl = bool(environ.get("WSL_DISTRO_NAME") or environ.get("WSL_INTEROP")) or any(
        marker in normalized_kernel for marker in ("microsoft", "wsl")
    )
    if normalized_system == "linux" and in_wsl:
        return "wsl"
    if normalized_system == "windows":
        return "windows"
    if normalized_system == "linux":
        return "linux"
    return "other"


def read_text_if_present(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def collect_environment() -> dict[str, object]:
    cwd = Path.cwd().resolve()
    home = Path.home().resolve()
    proc_version = read_text_if_present(Path("/proc/version"))
    cgroup = read_text_if_present(Path("/proc/1/cgroup"))
    layer = classify_environment(
        system=platform.system(),
        proc_version=proc_version,
        environ=os.environ,
        docker_env_exists=Path("/.dockerenv").exists(),
        cgroup_text=cgroup,
    )
    return {
        "layer": layer,
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
        "wsl_distribution": os.environ.get("WSL_DISTRO_NAME"),
        "cwd": str(cwd),
        "home": str(home),
        "cwd_under_windows_mount": str(cwd).startswith("/mnt/"),
    }


def main() -> int:
    print(json.dumps(collect_environment(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
