import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

LAB = Path(__file__).resolve().parents[1]
VERIFY = LAB / "verify.py"


def run_verifier(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VERIFY), "--root", str(root)],
        text=True,
        capture_output=True,
        check=False,
    )


class ContractVerifierTests(unittest.TestCase):
    def test_root_initializer_only_prepares_named_volume_for_non_root_writer(self):
        compose = yaml.safe_load((LAB / "compose.yaml").read_text(encoding="utf-8"))
        init = compose["services"]["volume-init"]
        writer = compose["services"]["writer"]
        self.assertEqual(init["user"], "0:0")
        self.assertIn("chown -R", " ".join(init["command"]))
        self.assertEqual(init["volumes"], ["ch09_data:/data/volume"])
        self.assertEqual(
            writer["depends_on"]["volume-init"]["condition"],
            "service_completed_successfully",
        )

    def test_bind_demo_runs_as_numeric_non_root_user(self):
        compose = yaml.safe_load((LAB / "compose.yaml").read_text(encoding="utf-8"))
        self.assertEqual(
            compose["services"]["writer"]["user"],
            "${HOST_UID:-1000}:${HOST_GID:-1000}",
        )

    def test_repository_example_satisfies_contract(self):
        result = run_verifier(LAB)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS", result.stdout)

    def test_missing_required_fragment_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            copied = Path(tmp) / LAB.name
            shutil.copytree(LAB, copied)
            contract = json.loads((copied / "contract.json").read_text(encoding="utf-8"))
            target = copied / contract["checks"][0]["file"]
            target.write_text("intentionally broken\n", encoding="utf-8")
            result = run_verifier(copied)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FAIL", result.stdout)

    def test_integration_accepts_explicit_docker_cli(self):
        result = subprocess.run(
            [sys.executable, str(VERIFY), "--help"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--docker-cli", result.stdout)

    def test_parent_path_in_contract_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            copied = Path(tmp) / LAB.name
            shutil.copytree(LAB, copied)
            contract_path = copied / "contract.json"
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["checks"][0]["file"] = "../outside.txt"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            result = run_verifier(copied)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsafe relative path", result.stdout)


if __name__ == "__main__":
    unittest.main()
