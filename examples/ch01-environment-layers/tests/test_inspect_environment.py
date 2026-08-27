from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("inspect_environment", HERE / "inspect_environment.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class EnvironmentLayerTests(unittest.TestCase):
    def classify(self, **overrides: object) -> str:
        values: dict[str, object] = {
            "system": "Linux",
            "proc_version": "Linux version 6.8.0-generic",
            "environ": {},
            "docker_env_exists": False,
            "cgroup_text": "0::/",
        }
        values.update(overrides)
        return MODULE.classify_environment(**values)

    def test_windows_is_detected(self) -> None:
        self.assertEqual(self.classify(system="Windows"), "windows")

    def test_wsl_is_detected_from_distribution_environment(self) -> None:
        self.assertEqual(self.classify(environ={"WSL_DISTRO_NAME": "Ubuntu"}), "wsl")

    def test_wsl_is_detected_from_microsoft_kernel(self) -> None:
        self.assertEqual(
            self.classify(proc_version="Linux version 6.6.87.2-microsoft-standard-WSL2"),
            "wsl",
        )

    def test_container_has_priority_over_wsl(self) -> None:
        self.assertEqual(
            self.classify(
                environ={"WSL_DISTRO_NAME": "Ubuntu"},
                docker_env_exists=True,
            ),
            "container",
        )

    def test_container_is_detected_from_cgroup(self) -> None:
        self.assertEqual(self.classify(cgroup_text="0::/docker/abc123"), "container")

    def test_plain_linux_is_detected(self) -> None:
        self.assertEqual(self.classify(), "linux")

    def test_cli_outputs_json_with_known_layer(self) -> None:
        result = subprocess.run(
            [sys.executable, str(HERE / "inspect_environment.py")],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        self.assertIn(payload["layer"], {"windows", "wsl", "container", "linux", "other"})
        self.assertIn("cwd", payload)
        self.assertIn("python_version", payload)


if __name__ == "__main__":
    unittest.main()
