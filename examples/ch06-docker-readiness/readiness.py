#!/usr/bin/env python3
"""Distinguish missing Docker CLI from an unreachable daemon."""
import shutil
import subprocess


def status() -> tuple[str, str]:
    if shutil.which("docker") is None:
        return "cli-missing", "Install or enable Docker Desktop WSL integration."
    result = subprocess.run(["docker", "info"], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return "daemon-unavailable", "Start Docker Desktop and check WSL integration."
    return "ready", "Docker CLI and daemon are ready."


if __name__ == "__main__":
    state, guidance = status()
    print(f"status={state}")
    print(guidance)
