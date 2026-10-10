#!/usr/bin/env python3
"""正式 Release 身份来源与版本两态契约的离线测试。"""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "release_metadata_control_under_test",
    ROOT / ".github/scripts/release_metadata_control.py",
)
assert SPEC is not None and SPEC.loader is not None
CONTROL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTROL)

REPOSITORY = "LJMcarryu/YTIFLYADLib_iOS"
CHANNEL = "yt"
VERSION = "6.4.0"
NEXT_VERSION = "6.5.0"
RELEASE_ID = "123"


def formal_release() -> dict[str, object]:
    return {
        "id": int(RELEASE_ID),
        "tag_name": VERSION,
        "draft": False,
        "prerelease": False,
        "published_at": "2026-10-09T00:00:00Z",
        "assets": [],
    }


class ReleaseMetadataSourceTests(unittest.TestCase):
    def test_release_event_uses_payload_without_api_request(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            event = Path(directory) / "event.json"
            event.write_text(json.dumps({
                "action": "published",
                "repository": {"full_name": REPOSITORY},
                "release": formal_release(),
            }), encoding="utf-8")
            called = False

            def forbidden_request(_url, _headers):
                nonlocal called
                called = True
                raise AssertionError("release event 不得查询 metadata API")

            actual = CONTROL.formal_release_metadata(
                repository=REPOSITORY,
                tag=VERSION,
                release_id=RELEASE_ID,
                event_name="release",
                event_path=event,
                token="",
                request_json=forbidden_request,
            )
            self.assertEqual(actual["id"], int(RELEASE_ID))
            self.assertFalse(called)

    def test_dispatch_uses_exact_id_and_authenticated_control_api(self) -> None:
        captured = {}
        calls = []

        def request(url, headers):
            calls.append(url)
            captured.update(url=url, headers=dict(headers))
            return formal_release()

        CONTROL.formal_release_metadata(
            repository=REPOSITORY,
            tag=VERSION,
            release_id=RELEASE_ID,
            event_name="workflow_dispatch",
            event_path=None,
            token="control-token",
            request_json=request,
        )
        self.assertTrue(captured["url"].endswith(f"/releases/{RELEASE_ID}"))
        self.assertNotIn("/releases/tags/", captured["url"])
        self.assertEqual(captured["headers"]["Authorization"], "Bearer control-token")
        self.assertEqual(calls, [captured["url"]])

    def test_missing_or_drifted_identity_fails_closed(self) -> None:
        for release_id, event_name, token in (
            ("", "workflow_dispatch", "control-token"),
            (RELEASE_ID, "workflow_dispatch", ""),
            (RELEASE_ID, "push", "control-token"),
        ):
            with self.subTest(release_id=release_id, event_name=event_name):
                with self.assertRaises(CONTROL.ReleaseControlError):
                    CONTROL.formal_release_metadata(
                        repository=REPOSITORY,
                        tag=VERSION,
                        release_id=release_id,
                        event_name=event_name,
                        event_path=None,
                        token=token,
                    )


class ReleaseVersionContractTests(unittest.TestCase):
    def test_checked_in_bootstrap_contract(self) -> None:
        state = json.loads((ROOT / "release-state.json").read_text(encoding="utf-8"))
        value = CONTROL.read_release_control(
            ROOT / ".github/scripts/release-control.json",
            repository=REPOSITORY,
            channel=CHANNEL,
            release_state_path=ROOT / "release-state.json",
            validation_mode="repository",
        )
        self.assertEqual(value["state"], "BOOTSTRAP_CLOSED")
        self.assertEqual(value["targetVersion"], state["version"])

    def test_control_state_validation_mode_phase_topology(self) -> None:
        candidate = {
            "schemaVersion": 1,
            "state": "CANDIDATE",
            "channel": CHANNEL,
            "repository": REPOSITORY,
            "closedVersion": VERSION,
            "targetVersion": NEXT_VERSION,
        }
        modes = ("local", "repository", "candidate", "draft_candidate",
                 "tag", "formal", "formal_release", "unexpected")
        phases = ("CLOSED", "FROZEN", "PREPARING")
        versions = (VERSION, NEXT_VERSION, "7.0.0")
        for control_state in ("BOOTSTRAP_CLOSED", "CANDIDATE"):
            candidate["state"] = control_state
            candidate["targetVersion"] = (
                VERSION if control_state == "BOOTSTRAP_CLOSED" else NEXT_VERSION
            )
            for mode in modes:
                for phase in phases:
                    for release_version in versions:
                        accepted = (
                            control_state == "BOOTSTRAP_CLOSED"
                            and mode in {"local", "repository"}
                            and phase == "CLOSED" and release_version == VERSION
                        ) or (
                            control_state == "CANDIDATE"
                            and mode in {"local", "repository"}
                            and phase == "CLOSED"
                            and release_version in {VERSION, NEXT_VERSION}
                        ) or (
                            control_state == "CANDIDATE"
                            and mode in {"candidate", "draft_candidate", "tag",
                                         "formal", "formal_release"}
                            and phase == "FROZEN"
                            and release_version == NEXT_VERSION
                        )
                        with self.subTest(control_state=control_state, mode=mode,
                                          phase=phase,
                                          release_version=release_version):
                            with tempfile.TemporaryDirectory() as directory:
                                control_path = Path(directory) / "control.json"
                                state_path = Path(directory) / "state.json"
                                control_path.write_text(
                                    json.dumps(candidate), encoding="utf-8"
                                )
                                state_path.write_text(json.dumps({
                                    "repository": REPOSITORY, "channel": CHANNEL,
                                    "phase": phase, "version": release_version,
                                }), encoding="utf-8")
                                call = lambda: CONTROL.read_release_control(
                                    control_path, repository=REPOSITORY,
                                    channel=CHANNEL, release_state_path=state_path,
                                    validation_mode=mode,
                                )
                                if accepted:
                                    self.assertEqual(call(), candidate)
                                else:
                                    with self.assertRaises(CONTROL.ReleaseControlError):
                                        call()

    def test_control_state_version_relationships_fail_closed(self) -> None:
        for state, target in (("BOOTSTRAP_CLOSED", NEXT_VERSION),
                              ("CANDIDATE", VERSION)):
            with self.subTest(state=state, target=target):
                with self.assertRaises(CONTROL.ReleaseControlError):
                    CONTROL.validate_release_control({
                        "schemaVersion": 1, "state": state,
                        "channel": CHANNEL, "repository": REPOSITORY,
                        "closedVersion": VERSION, "targetVersion": target,
                    }, repository=REPOSITORY, channel=CHANNEL,
                        release_phase="CLOSED", release_version=VERSION,
                        validation_mode="repository")


if __name__ == "__main__":
    unittest.main()
