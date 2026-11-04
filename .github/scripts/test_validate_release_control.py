from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = next(parent for parent in Path(__file__).resolve().parents
            if (parent / ".github/workflows/ci.yml").is_file())
SCRIPTS = ROOT / ("scripts" if (ROOT / "scripts/release_metadata_control.py").is_file()
                  else ".github/scripts")


class ValidateReleaseControlTests(unittest.TestCase):
    def test_workflow_preserves_channel_tag_state_modes(self) -> None:
        contract = json.loads((SCRIPTS / "release-control.json").read_text())
        workflow = (ROOT / ".github/workflows/ci.yml").read_text()
        step = re.search(
            r"(?ms)^      - name: 校验版本控制状态拓扑\n.*?(?=^      - name: )",
            workflow,
        ).group()
        self.assertIn("validate_release_control.py", step)
        self.assertIn('--repository "$GITHUB_REPOSITORY"', step)
        self.assertIn('--validation-mode "$VALIDATION_MODE"', step)
        self.assertIn(f"--channel {contract['channel']}", step)
        expected = {"general": ["tag", "formal"], "ys": ["formal_release"],
                    "ys-splash": ["formal_release"], "yt": [], "youku": []}
        self.assertEqual(re.findall(r"--tag-state-mode ([a-z_]+)", step),
                         expected[contract["channel"]])

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.scripts = self.root / "control"
        self.scripts.mkdir()
        for name in ("validate_release_control.py", "release_metadata_control.py",
                     "github_http_retry.py"):
            shutil.copyfile(SCRIPTS / name, self.scripts / name)
        self.contract = {
            "schemaVersion": 1, "state": "CANDIDATE", "channel": "general",
            "repository": "fixture/distribution", "closedVersion": "6.4.3",
            "targetVersion": "6.4.4",
        }
        self.write_contract()
        self.git("init", "-q")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.write_state("FROZEN")
        self.git("add", "release-state.json")
        self.git("commit", "-qm", "Frozen fixture")
        self.git("tag", "-a", "6.4.4", "-m", "Frozen fixture")
        self.write_state("CLOSED")
        self.git("add", "release-state.json")
        self.git("commit", "-qm", "Closed fixture")

    def git(self, *arguments: str) -> None:
        subprocess.run(["git", *arguments], cwd=self.root, check=True,
                       capture_output=True, text=True)

    def write_contract(self) -> None:
        (self.scripts / "release-control.json").write_text(
            json.dumps(self.contract), encoding="utf-8")

    def write_state(self, phase: str) -> None:
        (self.root / "release-state.json").write_text(json.dumps({
            "repository": "fixture/distribution", "channel": "general",
            "phase": phase, "version": "6.4.4",
        }), encoding="utf-8")

    def run_check(self, mode: str, *tag_modes: str, tag: str = "6.4.4"):
        arguments = [sys.executable, "-B", str(self.scripts / "validate_release_control.py"),
                     "--repository", "fixture/distribution", "--channel", "general",
                     "--validation-mode", mode]
        for tag_mode in tag_modes:
            arguments.extend(["--tag-state-mode", tag_mode])
        environment = dict(os.environ, RUNNER_TEMP=str(self.root), RELEASE_TAG=tag,
                           PYTHONDONTWRITEBYTECODE="1")
        return subprocess.run(arguments, cwd=self.root, env=environment,
                              capture_output=True, text=True)

    def test_local_closed_state_does_not_read_tag(self) -> None:
        result = self.run_check("local", "tag", "formal", tag="missing")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "release-control 版本契约校验通过\n")
        self.assertFalse((self.root / "release-control-state.json").exists())

    def test_configured_formal_modes_read_frozen_tag(self) -> None:
        for mode in ("tag", "formal", "formal_release"):
            with self.subTest(mode=mode):
                result = self.run_check(mode, mode)
                self.assertEqual(result.returncode, 0, result.stderr)
                state = json.loads((self.root / "release-control-state.json").read_text())
                self.assertEqual(state["phase"], "FROZEN")
                self.assertEqual(json.loads((self.root / "release-state.json").read_text())
                                 ["phase"], "CLOSED")

    def test_unconfigured_formal_mode_preserves_checkout_state(self) -> None:
        result = self.run_check("formal_release")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FROZEN", result.stderr)
        self.write_state("FROZEN")
        result = self.run_check("formal_release", tag="missing")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_tag_fails_without_checkout_fallback(self) -> None:
        self.write_state("FROZEN")
        result = self.run_check("formal", "formal", tag="missing")
        self.assertNotEqual(result.returncode, 0)

    def test_contract_identity_mismatch_fails(self) -> None:
        self.contract["repository"] = "other/distribution"
        self.write_contract()
        result = self.run_check("local")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("repository 漂移", result.stderr)

    def test_bootstrap_contract_still_rejects_formal_consumption(self) -> None:
        self.contract.update(state="BOOTSTRAP_CLOSED", closedVersion="6.4.4")
        self.write_contract()
        self.assertEqual(self.run_check("repository").returncode, 0)
        result = self.run_check("formal", "formal")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("只接受 repository/local", result.stderr)


if __name__ == "__main__":
    unittest.main()
