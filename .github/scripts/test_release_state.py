from __future__ import annotations

import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import release_state  # noqa: E402


ARTIFACTS = [
    {"name": "checksums.txt", "contentSha256": "712bd4440cd269206f9b7a0125be6bea12eb2fa9287b6d1d79a8b062051153eb"},
    {"name": "delivery-manifest.json", "contentSha256": "f929834729b0af44bcf0569007193b6363021847196124d02b56c8bd84daa64b"},
    {"name": "YTIFLYADLib-6.2.3.zip", "contentSha256": "64e168120aac5f412ab96bdef78fff14e7ba75aae234a08d737fa5ad21c3e537"},
    {"name": "YTIFLYADLib.xcframework.zip", "contentSha256": "303e185b70d5396f9438c8e6a96239fbb1e1ef93166f8487ac4e6ebfb58d3b09"},
]

FROZEN_ARTIFACTS = [
    {"name": "checksums.txt", "contentSha256": "6d025d9b3abcf75ee411b445bc0a3af21d1a5ddd8fc60f6ae26d3458789eb244"},
    {"name": "delivery-manifest.json", "contentSha256": "15cbc25f0f67cb1e2c4857bf9ba05defee39ad375d9178f4c60054c189761573"},
    {"name": "YTIFLYADLib-6.2.4.zip", "contentSha256": "5207fbc790d055af81f6c33d8558ce3d1e834875e3cd283cb4ccb8dc34d35de9"},
    {"name": "YTIFLYADLib.xcframework.zip", "contentSha256": "5f3df44ec856f9e38c584311512ede168cf2c0ec45e3d09378052e1b0196e263"},
]

CLOSED_STATE = {
    "schemaVersion": 1,
    "channel": "yt",
    "repository": "LJMcarryu/YTIFLYADLib_iOS",
    "version": "6.2.3",
    "phase": "CLOSED",
    "binarySourceCommit": "ea0240e620b57d7275e486199099c648f51de257",
    "releaseMetadataCommit": "0f26b7647e6c1aadb32eca68b24f6845639a59c2",
    "artifactInventory": {
        "count": 4,
        "sha256": "023610d4c8d338a2705f04752c0ca99f55bf3fc23c4c06af933e9b24cd399cdd",
    },
    "appleReview": {
        "requiredForRelease": False,
        "statusAtFreeze": "not-run",
        "evidenceIncluded": False,
    },
    "publication": {
        "releaseId": 370465034,
        "tagName": "6.2.3",
        "tagObjectSha": "219d6e359f848360c06d1f529d450d66f23b550f",
        "tagCommitSha": "09148ce3c651b3dfc35cae3c873baab6d8105950",
        "releaseUrl": "https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/6.2.3",
        "publishedAt": "2026-08-16T10:24:53Z",
        "formalConsumerRunId": 31941599341,
        "formalConsumerRunUrl": "https://github.com/LJMcarryu/YTIFLYADLib_iOS/actions/runs/31941599341",
        "conclusion": "success",
        "verifiedAt": "2026-08-16T10:26:18Z",
    },
}


class ReleaseStateTests(unittest.TestCase):
    def setUp(self) -> None:
        # CLOSED 生成与迁移单测使用不可变夹具；候选分支可合法把实时状态
        # 改为 6.2.4/FROZEN，不能反向污染历史 CLOSED 预期。
        self.state = copy.deepcopy(CLOSED_STATE)
        self.facts = {
            key: copy.deepcopy(value)
            for key, value in self.state.items()
            if key != "artifactInventory"
        }
        self.facts["artifacts"] = copy.deepcopy(ARTIFACTS)

    def write_facts(self, directory: Path) -> Path:
        path = directory / "facts.json"
        path.write_text(json.dumps(self.facts), encoding="utf-8")
        return path

    def test_closed_fixture_is_rebuilt_exactly_from_content_digests(self) -> None:
        generated = release_state.build_closed_state(self.facts)
        self.assertEqual(generated, self.state)
        self.assertEqual(release_state.canonical_json(generated),
                         release_state.canonical_json(self.state))
        self.assertEqual(generated["artifactInventory"], {
            "count": 4,
            "sha256": "023610d4c8d338a2705f04752c0ca99f55bf3fc23c4c06af933e9b24cd399cdd",
        })

    def test_current_repository_state_is_independently_valid(self) -> None:
        current = json.loads(
            (ROOT / "release-state.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            release_state.validate_state(
                current,
                expected_channel="yt",
                expected_repository="LJMcarryu/YTIFLYADLib_iOS",
            ),
            current,
        )

    def test_624_frozen_candidate_is_built_from_frozen_asset_facts(self) -> None:
        facts = {
            "schemaVersion": 1,
            "channel": "yt",
            "repository": "LJMcarryu/YTIFLYADLib_iOS",
            "version": "6.2.4",
            "phase": "FROZEN",
            "binarySourceCommit": "b0f745d582ce2bed5110702cff972be4153e5038",
            "releaseMetadataCommit": "7b08118b43a0c4441de4c76a64f34fa54b3fe889",
            "artifacts": copy.deepcopy(FROZEN_ARTIFACTS),
            "appleReview": copy.deepcopy(self.state["appleReview"]),
        }
        frozen = release_state.build_frozen_state(facts)
        self.assertEqual(frozen["version"], "6.2.4")
        self.assertEqual(frozen["phase"], "FROZEN")
        self.assertIsNone(frozen["publication"])
        self.assertEqual(frozen["artifactInventory"], {
            "count": 4,
            "sha256": "0c0fe6068bdc9b1732bd0fcd8a07552bfb0eeb6444729afc3dd684c373b9cdc6",
        })
        release_state.validate_state_transition(self.state, frozen)

    def test_dry_run_prints_state_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "release-state.json"
            target.write_text("原内容\n", encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = release_state.main([str(target), "--facts", str(self.write_facts(root))])
            self.assertEqual(result, 0)
            self.assertEqual(target.read_text(encoding="utf-8"), "原内容\n")
            self.assertEqual(json.loads(output.getvalue()), self.state)

    def test_write_atomically_generates_closed_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "release-state.json"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = release_state.main([
                    str(target), "--facts", str(self.write_facts(root)), "--write",
                    "--expected-channel", "yt",
                    "--expected-repository", "LJMcarryu/YTIFLYADLib_iOS",
                    "--expected-version", "6.2.3",
                ])
            self.assertEqual(result, 0)
            self.assertEqual(target.read_text(encoding="utf-8"),
                             release_state.canonical_json(self.state))

    def test_rejects_extra_facts_fields(self) -> None:
        for mutate in (
            lambda value: value.update({"unexpected": True}),
            lambda value: value["artifacts"][0].update({"size": 1}),
        ):
            value = copy.deepcopy(self.facts)
            mutate(value)
            with self.assertRaises(release_state.ReleaseStateError):
                release_state.build_closed_state(value)

    def test_rejects_non_closed_failure_and_fake_apple_success(self) -> None:
        for mutate in (
            lambda value: value.update({"phase": "VERIFIED"}),
            lambda value: value["publication"].update({"conclusion": "failure"}),
            lambda value: value["appleReview"].update({"statusAtFreeze": "success"}),
            lambda value: value["publication"].update({"releaseId": "370465034"}),
        ):
            value = copy.deepcopy(self.facts)
            mutate(value)
            with self.assertRaises(release_state.ReleaseStateError):
                release_state.build_closed_state(value)

    def test_failed_replace_preserves_original_and_removes_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "release-state.json"
            target.write_text("不可破坏的原状态\n", encoding="utf-8")
            with mock.patch.object(release_state.os, "replace", side_effect=OSError("失败")):
                with self.assertRaises(OSError):
                    release_state.atomic_write_state(target, self.state)
            self.assertEqual(target.read_text(encoding="utf-8"), "不可破坏的原状态\n")
            self.assertEqual(list(root.glob(".release-state.json.*.tmp")), [])

    def test_freeze_facts_generate_frozen_state_with_null_publication(self) -> None:
        facts = copy.deepcopy(self.facts)
        facts.pop("publication")
        facts["phase"] = "FROZEN"
        frozen = release_state.build_state_from_facts(facts)
        self.assertEqual(frozen["phase"], "FROZEN")
        self.assertIsNone(frozen["publication"])
        self.assertEqual(frozen["artifactInventory"], self.state["artifactInventory"])

        facts["publication"] = None
        with self.assertRaises(release_state.ReleaseStateError):
            release_state.build_frozen_state(facts)

    def test_phase_specific_publication_and_transition_contract(self) -> None:
        frozen = copy.deepcopy(self.state)
        frozen["phase"] = "FROZEN"
        frozen["publication"] = None
        preparing = copy.deepcopy(frozen)
        preparing["phase"] = "PREPARING"
        release_state.validate_state_transition(preparing, frozen)
        release_state.validate_state_transition(frozen, self.state)

        invalid_publication = copy.deepcopy(frozen)
        invalid_publication["publication"] = {}
        with self.assertRaises(release_state.ReleaseStateError):
            release_state.validate_state(invalid_publication)

        next_frozen = copy.deepcopy(frozen)
        next_frozen["version"] = "6.2.4"
        release_state.validate_state_transition(self.state, next_frozen)
        with self.assertRaises(release_state.ReleaseStateError):
            release_state.validate_state_transition(self.state, frozen)

        cross_version_closed = copy.deepcopy(self.state)
        cross_version_closed["version"] = "6.2.4"
        cross_version_closed["publication"]["tagName"] = "6.2.4"
        cross_version_closed["publication"]["releaseUrl"] = (
            "https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/6.2.4"
        )
        with self.assertRaises(release_state.ReleaseStateError):
            release_state.validate_state_transition(self.state, cross_version_closed)


if __name__ == "__main__":
    unittest.main()
