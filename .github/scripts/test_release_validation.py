#!/usr/bin/env python3
"""Release 下载器、资产指纹和 CI 结构的离线回归测试。"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import download_draft_release as draft
import download_release_anonymously as anonymous
import release_asset_identity as identity


ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = "LJMcarryu/YTIFLYADLib_iOS"
TAG = "6.2.3"
CANDIDATE_ID = "a" * 64
DISPATCH_NONCE = "d" * 32
RELEASE_ID = 99
EXPECTED_COMMIT = "b" * 40
BINARY_COMMIT = "1" * 40
METADATA_COMMIT = "2" * 40
CANDIDATE_BRANCH = f"release-candidate/{TAG}-{CANDIDATE_ID}"
DRAFT_SELECTOR = "untagged-" + "e" * 16


def release_assets(selector: str = DRAFT_SELECTOR) -> list[dict[str, object]]:
    result = []
    for asset_id, name in enumerate(sorted(anonymous.expected_asset_names(TAG)), 101):
        result.append(
            {
                "id": asset_id,
                "name": name,
                "size": asset_id,
                "digest": f"sha256:{asset_id:064x}",
                "state": "uploaded",
                "url": (
                    f"https://api.github.com/repos/{REPOSITORY}/"
                    f"releases/assets/{asset_id}"
                ),
                "browser_download_url": (
                    f"https://github.com/{REPOSITORY}/releases/download/"
                    f"{selector}/{name}"
                ),
            }
        )
    return result


def draft_release() -> dict[str, object]:
    return {
        "id": RELEASE_ID,
        "tag_name": TAG,
        "draft": True,
        "prerelease": False,
        "published_at": None,
        "target_commitish": CANDIDATE_BRANCH,
        "html_url": (
            f"https://github.com/{REPOSITORY}/releases/tag/{DRAFT_SELECTOR}"
        ),
        "body": (
            f"# {TAG}\n\n"
            f"- `binarySourceCommit`（SDK 二进制源码提交）：`{BINARY_COMMIT}`\n"
            "- `releaseMetadataCommit`（仅回填 checksum、扫描汇总和发布验收事实，"
            f"不是 SDK 二进制源码提交）：`{METADATA_COMMIT}`\n"
            f"- `candidateId`：`{CANDIDATE_ID}`\n"
            f"- `uploadInventorySha256`：`{'c' * 64}`\n"
        ),
        "assets": release_assets(),
    }


def formal_release() -> dict[str, object]:
    value = draft_release()
    value.update(
        {
            "draft": False,
            "published_at": "2026-08-11T00:00:00Z",
            "body": "正式发布说明",
            "html_url": f"https://github.com/{REPOSITORY}/releases/tag/{TAG}",
            "assets": release_assets(TAG),
        }
    )
    return value


class FakeResponse:
    def __init__(self, payload: bytes, url: str, status: int = 200) -> None:
        self.payload = payload
        self.url = url
        self.status = status
        self.offset = 0

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            result = self.payload[self.offset :]
            self.offset = len(self.payload)
            return result
        result = self.payload[self.offset : self.offset + size]
        self.offset += len(result)
        return result

    def geturl(self) -> str:
        return self.url


class FakeDraftOpener:
    def __init__(
        self,
        initial_release: dict[str, object],
        contents: dict[str, bytes],
        final_release: dict[str, object] | None = None,
    ) -> None:
        self.initial_release = initial_release
        self.final_release = final_release or initial_release
        self.contents = contents
        self.metadata_calls = 0

    def open(self, request: object, timeout: int) -> FakeResponse:
        del timeout
        url = request.full_url
        if "/git/ref/heads/" in url:
            return FakeResponse(
                json.dumps({"object": {"sha": EXPECTED_COMMIT}}).encode("utf-8"),
                url,
            )
        if url.endswith(f"/releases/{RELEASE_ID}"):
            release = (
                self.initial_release
                if self.metadata_calls == 0
                else self.final_release
            )
            self.metadata_calls += 1
            return FakeResponse(json.dumps(release).encode("utf-8"), url)
        asset = next(
            item for item in self.initial_release["assets"] if item["url"] == url
        )
        return FakeResponse(
            self.contents[asset["name"]],
            f"https://release-assets.githubusercontent.com/{asset['id']}",
        )


def draft_release_with_contents() -> tuple[dict[str, object], dict[str, bytes]]:
    release = draft_release()
    contents = {
        name: f"downloaded-{index}-{name}".encode("utf-8")
        for index, name in enumerate(sorted(anonymous.expected_asset_names(TAG)))
    }
    for asset in release["assets"]:
        content = contents[asset["name"]]
        asset["size"] = len(content)
        asset["digest"] = f"sha256:{hashlib.sha256(content).hexdigest()}"
    return release, contents


class ReleaseMetadataTests(unittest.TestCase):
    def test_anonymous_metadata_accepts_only_published_release(self) -> None:
        assets = anonymous.validate_release_metadata(formal_release(), REPOSITORY, TAG)
        self.assertEqual(set(assets), anonymous.expected_asset_names(TAG))
        with self.assertRaises(anonymous.VerificationError):
            anonymous.validate_release_metadata(draft_release(), REPOSITORY, TAG)

    def test_anonymous_metadata_rejects_noncanonical_formal_html_url(self) -> None:
        mutations = (
            (
                "untagged selector",
                lambda value: value.update(
                    {"html_url": value["html_url"].replace(TAG, DRAFT_SELECTOR)}
                ),
            ),
            (
                "wrong host",
                lambda value: value.update(
                    {"html_url": value["html_url"].replace("github.com", "example.com")}
                ),
            ),
            (
                "wrong repository",
                lambda value: value.update(
                    {"html_url": value["html_url"].replace(REPOSITORY, "attacker/repo")}
                ),
            ),
            (
                "non-https scheme",
                lambda value: value.update(
                    {"html_url": value["html_url"].replace("https://", "http://", 1)}
                ),
            ),
            (
                "query suffix",
                lambda value: value.update({"html_url": value["html_url"] + "?x=1"}),
            ),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                release = formal_release()
                mutate(release)
                with self.assertRaises(anonymous.VerificationError):
                    anonymous.validate_release_metadata(release, REPOSITORY, TAG)

    def test_shared_inventory_rejects_extra_duplicate_and_bad_digest(self) -> None:
        for mutate in (
            lambda value: value["assets"].append(copy.deepcopy(value["assets"][0])),
            lambda value: value["assets"].append(
                {**copy.deepcopy(value["assets"][0]), "name": "unexpected.zip"}
            ),
            lambda value: value["assets"][0].update({"digest": "sha256:bad"}),
            lambda value: value["assets"].__setitem__(0, None),
        ):
            release = draft_release()
            mutate(release)
            with self.assertRaises(anonymous.VerificationError):
                anonymous.validate_asset_inventory(release, TAG)

    def test_draft_metadata_accepts_valid_untagged_urls_and_binds_candidate(self) -> None:
        assets = draft.validate_draft_release_metadata(
            draft_release(),
            REPOSITORY,
            TAG,
            CANDIDATE_ID,
            RELEASE_ID,
            CANDIDATE_BRANCH,
            EXPECTED_COMMIT,
            EXPECTED_COMMIT,
        )
        self.assertEqual(set(assets), anonymous.expected_asset_names(TAG))
        exact_commit_release = draft_release()
        exact_commit_release["target_commitish"] = EXPECTED_COMMIT
        exact_assets = draft.validate_draft_release_metadata(
            exact_commit_release,
            REPOSITORY,
            TAG,
            CANDIDATE_ID,
            RELEASE_ID,
            CANDIDATE_BRANCH,
            EXPECTED_COMMIT,
        )
        self.assertEqual(set(exact_assets), anonymous.expected_asset_names(TAG))

        mutations = (
            lambda value: value.update({"id": RELEASE_ID + 1}),
            lambda value: value.update({"draft": False}),
            lambda value: value.update({"prerelease": True}),
            lambda value: value.update({"published_at": "2026-08-11T00:00:00Z"}),
            lambda value: value.update({"target_commitish": "d" * 40}),
            lambda value: value.update(
                {"body": value["body"].replace(CANDIDATE_ID, "e" * 64)}
            ),
            lambda value: value.update(
                {"body": value["body"].replace(BINARY_COMMIT, "PENDING")}
            ),
            lambda value: value.update(
                {"body": value["body"].replace(METADATA_COMMIT, BINARY_COMMIT)}
            ),
            lambda value: value["assets"][0].update(
                {
                    "url": "https://api.github.com/repos/attacker/repo/"
                    "releases/assets/101"
                }
            ),
            lambda value: value["assets"].pop(),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                release = draft_release()
                mutate(release)
                with self.assertRaises(anonymous.VerificationError):
                    draft.validate_draft_release_metadata(
                        release,
                        REPOSITORY,
                        TAG,
                        CANDIDATE_ID,
                        RELEASE_ID,
                        CANDIDATE_BRANCH,
                        EXPECTED_COMMIT,
                        EXPECTED_COMMIT,
                    )

    def test_draft_untagged_urls_reject_wrong_boundaries(self) -> None:
        mutations = (
            (
                "html host",
                lambda value: value.update(
                    {"html_url": value["html_url"].replace("github.com", "example.com")}
                ),
            ),
            (
                "html repository",
                lambda value: value.update(
                    {"html_url": value["html_url"].replace(REPOSITORY, "attacker/repo")}
                ),
            ),
            (
                "html scheme",
                lambda value: value.update(
                    {"html_url": value["html_url"].replace("https://", "http://", 1)}
                ),
            ),
            (
                "html selector",
                lambda value: value.update(
                    {"html_url": value["html_url"].replace(DRAFT_SELECTOR, TAG)}
                ),
            ),
            (
                "browser host",
                lambda value: value["assets"][0].update(
                    {
                        "browser_download_url": value["assets"][0][
                            "browser_download_url"
                        ].replace("github.com", "example.com")
                    }
                ),
            ),
            (
                "browser repository",
                lambda value: value["assets"][0].update(
                    {
                        "browser_download_url": value["assets"][0][
                            "browser_download_url"
                        ].replace(REPOSITORY, "attacker/repo")
                    }
                ),
            ),
            (
                "browser scheme",
                lambda value: value["assets"][0].update(
                    {
                        "browser_download_url": value["assets"][0][
                            "browser_download_url"
                        ].replace("https://", "http://", 1)
                    }
                ),
            ),
            (
                "browser selector",
                lambda value: value["assets"][0].update(
                    {
                        "browser_download_url": value["assets"][0][
                            "browser_download_url"
                        ].replace(DRAFT_SELECTOR, "untagged-" + "f" * 16)
                    }
                ),
            ),
            (
                "browser filename",
                lambda value: value["assets"][0].update(
                    {
                        "browser_download_url": value["assets"][0][
                            "browser_download_url"
                        ].rsplit("/", 1)[0]
                        + "/unexpected.zip"
                    }
                ),
            ),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                release = draft_release()
                mutate(release)
                with self.assertRaises(anonymous.VerificationError):
                    draft.validate_draft_release_metadata(
                        release,
                        REPOSITORY,
                        TAG,
                        CANDIDATE_ID,
                        RELEASE_ID,
                        CANDIDATE_BRANCH,
                        EXPECTED_COMMIT,
                        EXPECTED_COMMIT,
                    )

    def test_draft_candidate_line_must_be_unique(self) -> None:
        release = draft_release()
        release["body"] += f"- `candidateId`：`{CANDIDATE_ID}`\n"
        with self.assertRaises(anonymous.VerificationError):
            draft.validate_draft_release_metadata(
                release,
                REPOSITORY,
                TAG,
                CANDIDATE_ID,
                RELEASE_ID,
                CANDIDATE_BRANCH,
                EXPECTED_COMMIT,
                EXPECTED_COMMIT,
            )

    def test_stable_snapshot_ignores_download_count_but_detects_digest_drift(self) -> None:
        before = draft_release()
        after = copy.deepcopy(before)
        after["assets"][0]["download_count"] = 12
        self.assertEqual(
            draft.stable_release_snapshot(before), draft.stable_release_snapshot(after)
        )
        after["assets"][0]["digest"] = f"sha256:{'f' * 64}"
        self.assertNotEqual(
            draft.stable_release_snapshot(before), draft.stable_release_snapshot(after)
        )

        after = copy.deepcopy(before)
        after["html_url"] = after["html_url"].replace(DRAFT_SELECTOR, "untagged-f")
        self.assertNotEqual(
            draft.stable_release_snapshot(before), draft.stable_release_snapshot(after)
        )

        for index in range(len(before["assets"])):
            with self.subTest(browser_url_asset=index):
                after = copy.deepcopy(before)
                after["assets"][index]["browser_download_url"] += "?drift=1"
                self.assertNotEqual(
                    draft.stable_release_snapshot(before),
                    draft.stable_release_snapshot(after),
                )


class RequestBoundaryTests(unittest.TestCase):
    def test_anonymous_request_never_has_authorization(self) -> None:
        request = anonymous.build_anonymous_request(
            "https://api.github.com/repos/owner/repo/releases/tags/6.2.3",
            "application/vnd.github+json",
        )
        self.assertNotIn(
            "authorization", {name.lower() for name, _ in request.header_items()}
        )

    def test_authenticated_request_only_accepts_github_api(self) -> None:
        request = draft.build_authenticated_request(
            "https://api.github.com/repos/owner/repo/releases/assets/1",
            "application/octet-stream",
            "token",
        )
        self.assertEqual(request.get_header("Authorization"), "Bearer token")
        with self.assertRaises(anonymous.VerificationError):
            draft.build_authenticated_request(
                "https://example.com/steal", "application/octet-stream", "token"
            )

    def test_redirect_strips_token_and_rejects_non_github_host(self) -> None:
        request = draft.build_authenticated_request(
            "https://api.github.com/repos/owner/repo/releases/assets/1",
            "application/octet-stream",
            "token",
        )
        handler = draft.SafeGitHubAssetRedirectHandler()
        redirected = handler.redirect_request(
            request,
            None,
            302,
            "Found",
            {},
            "https://release-assets.githubusercontent.com/signed",
        )
        self.assertIsNotNone(redirected)
        self.assertNotIn(
            "authorization", {name.lower() for name, _ in redirected.header_items()}
        )
        with self.assertRaises(anonymous.VerificationError):
            handler.redirect_request(
                request, None, 302, "Found", {}, "https://example.com/steal"
            )

    def test_draft_download_requires_only_expected_token_and_never_clobbers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with mock.patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(anonymous.VerificationError):
                    draft.download_release(
                        REPOSITORY,
                        TAG,
                        CANDIDATE_ID,
                        RELEASE_ID,
                        CANDIDATE_BRANCH,
                        EXPECTED_COMMIT,
                        root / "assets",
                        root / "metadata.json",
                    )
            (root / "metadata.json").write_text("existing\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "token"}, clear=True):
                with self.assertRaises(anonymous.VerificationError):
                    draft.download_release(
                        REPOSITORY,
                        TAG,
                        CANDIDATE_ID,
                        RELEASE_ID,
                        CANDIDATE_BRANCH,
                        EXPECTED_COMMIT,
                        root / "assets",
                        root / "metadata.json",
                    )

    def test_draft_download_verifies_bytes_and_refetches_metadata(self) -> None:
        release, contents = draft_release_with_contents()
        opener = FakeDraftOpener(release, contents)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (
                mock.patch.dict(os.environ, {"GITHUB_TOKEN": "token"}, clear=True),
                mock.patch.object(draft, "build_opener", return_value=opener),
            ):
                draft.download_release(
                    REPOSITORY,
                    TAG,
                    CANDIDATE_ID,
                    RELEASE_ID,
                    CANDIDATE_BRANCH,
                    EXPECTED_COMMIT,
                    root / "assets",
                    root / "metadata.json",
                )
            self.assertEqual(opener.metadata_calls, 2)
            self.assertEqual(
                {path.name for path in (root / "assets").iterdir()},
                anonymous.expected_asset_names(TAG),
            )
            for name, content in contents.items():
                self.assertEqual((root / "assets" / name).read_bytes(), content)
            self.assertEqual(json.loads((root / "metadata.json").read_text()), release)

    def test_draft_download_rejects_inventory_change_during_download(self) -> None:
        release, contents = draft_release_with_contents()
        final_release = copy.deepcopy(release)
        final_release["assets"][0]["digest"] = f"sha256:{'f' * 64}"
        opener = FakeDraftOpener(release, contents, final_release)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (
                mock.patch.dict(os.environ, {"GITHUB_TOKEN": "token"}, clear=True),
                mock.patch.object(draft, "build_opener", return_value=opener),
                self.assertRaises(anonymous.VerificationError),
            ):
                draft.download_release(
                    REPOSITORY,
                    TAG,
                    CANDIDATE_ID,
                    RELEASE_ID,
                    CANDIDATE_BRANCH,
                    EXPECTED_COMMIT,
                    root / "assets",
                    root / "metadata.json",
                )
            self.assertFalse((root / "metadata.json").exists())


class AssetIdentityTests(unittest.TestCase):
    def test_identity_is_stable_and_rejects_inventory_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, name in enumerate(sorted(anonymous.expected_asset_names(TAG))):
                (root / name).write_bytes(f"asset-{index}".encode("ascii"))
            first = identity.asset_identity(root, TAG)
            self.assertRegex(first, r"^[0-9a-f]{64}$")
            self.assertEqual(first, identity.asset_identity(root, TAG))
            (root / "checksums.txt").write_text("changed", encoding="utf-8")
            self.assertNotEqual(first, identity.asset_identity(root, TAG))
            (root / "extra").write_text("extra", encoding="utf-8")
            with self.assertRaises(anonymous.VerificationError):
                identity.asset_identity(root, TAG)


class WorkflowStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        script = (
            'data = YAML.safe_load(File.read(ARGV.fetch(0)), aliases: true); '
            "STDOUT.write(JSON.generate(data))"
        )
        result = subprocess.run(
            [
                "ruby",
                "-ryaml",
                "-rjson",
                "-e",
                script,
                str(ROOT / ".github/workflows/ci.yml"),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        cls.workflow = json.loads(result.stdout)

    def test_yaml_modes_permissions_and_job_graph(self) -> None:
        self.assertEqual(self.workflow["permissions"], {"contents": "read"})
        inputs = self.workflow["on"]["workflow_dispatch"]["inputs"]
        self.assertEqual(
            inputs["validation_mode"]["options"],
            ["repository", "draft_candidate", "formal_release"],
        )
        jobs = self.workflow["jobs"]
        self.assertEqual(jobs["verify-release-assets"]["needs"], ["verify-repository"])
        self.assertEqual(
            jobs["verify-cocoapods-consumer"]["needs"], ["verify-release-assets"]
        )
        self.assertEqual(
            jobs["verify-swiftpm-consumer"]["needs"], ["verify-release-assets"]
        )
        self.assertNotIn("verify-swiftpm-consumer", jobs["verify-cocoapods-consumer"]["needs"])

    def test_candidate_gate_order_and_checkout_credentials(self) -> None:
        repository_steps = self.workflow["jobs"]["verify-repository"]["steps"]
        names = [step.get("name", "") for step in repository_steps]
        checkout_index = next(
            index
            for index, step in enumerate(repository_steps)
            if step.get("uses") == "actions/checkout@v4"
        )
        self.assertLess(names.index("校验手动验证模式与触发分支"), checkout_index)
        self.assertLess(
            names.index("读取仓库当前版本"),
            names.index("Draft candidate 明确要求最终 FORMAL A/B"),
        )
        self.assertLess(
            names.index("Draft candidate 明确要求最终 FORMAL A/B"),
            names.index("校验 draft candidate 身份与候选分支触发 SHA"),
        )
        self.assertLess(
            names.index("校验 draft candidate 身份与候选分支触发 SHA"),
            names.index("固定 draft candidate 本地分发清单"),
        )
        for job in self.workflow["jobs"].values():
            for step in job["steps"]:
                if step.get("uses") == "actions/checkout@v4":
                    self.assertIs(step["with"]["persist-credentials"], False)

    def test_legacy_release_tag_dispatch_remains_formal_and_anonymous(self) -> None:
        jobs = self.workflow["jobs"]
        repository_steps = jobs["verify-repository"]["steps"]
        guard = next(
            step for step in repository_steps if step.get("name") == "校验手动验证模式与触发分支"
        )
        selection = next(
            step for step in repository_steps if step.get("name") == "固定 Release 验证选择"
        )
        checkout = next(
            step
            for step in repository_steps
            if step.get("uses") == "actions/checkout@v4"
        )
        self.assertIn("兼容改造前只填写 release_tag", guard["run"])
        self.assertIn("'repository' && -n \"${FORMAL_TAG}\"", selection["run"])
        self.assertIn("inputs.validation_mode == 'repository'", checkout["with"]["ref"])
        self.assertIn("inputs.release_tag != ''", checkout["with"]["ref"])
        formal_downloads = [
            step
            for job in jobs.values()
            for step in job["steps"]
            if "正式 Release 资产" in step.get("name", "")
            or step.get("name") == "匿名下载本次 Release 的精确资产集"
        ]
        self.assertEqual(len(formal_downloads), 3)
        for step in formal_downloads:
            self.assertNotIn("GITHUB_TOKEN", step.get("env", {}))
            self.assertIn("inputs.validation_mode == 'repository'", step["if"])
            self.assertIn("inputs.release_tag != ''", step["if"])

    def test_token_is_only_in_defensively_guarded_draft_download_steps(self) -> None:
        token_steps = []
        for job_id, job in self.workflow["jobs"].items():
            for step in job["steps"]:
                if "GITHUB_TOKEN" in step.get("env", {}):
                    token_steps.append((job_id, step))
        self.assertEqual(len(token_steps), 3)
        self.assertNotIn(
            "${{ github.token }}",
            (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"),
        )
        for _, step in token_steps:
            self.assertIn("draft", step["name"])
            self.assertEqual(
                step["env"]["GITHUB_TOKEN"],
                "${{ secrets.DRAFT_RELEASE_READ_TOKEN }}",
            )
            condition = step.get("if", "")
            for required in (
                "github.event_name == 'workflow_dispatch'",
                "inputs.validation_mode == 'draft_candidate'",
                "github.ref == format('refs/heads/release-candidate/{0}-{1}'",
                "release_kind == 'draft'",
                "checkout_commit != ''",
            ):
                if required == "checkout_commit != ''" and "verify-repository" in condition:
                    required = "candidate_commit != ''"
                self.assertIn(required, condition)

    def test_candidate_inputs_branch_and_exact_run_names_are_bound(self) -> None:
        inputs = self.workflow["on"]["workflow_dispatch"]["inputs"]
        for name in ("candidate_id", "candidate_release_id", "dispatch_nonce"):
            self.assertIn(name, inputs)
        self.assertIn("draft-candidate:{0}:{1}:{2}", self.workflow["run-name"])
        self.assertIn("formal-release:{0}:{1}", self.workflow["run-name"])
        source = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn('candidate_branch="release-candidate/${CANDIDATE_TAG}-${CANDIDATE_ID}"', source)
        self.assertIn('test "${head_commit}" = "${GITHUB_SHA}"', source)
        self.assertIn('[[ "${CANDIDATE_RELEASE_ID}" =~ ^[1-9][0-9]*$ ]]', source)
        self.assertIn('[[ "${DISPATCH_NONCE}" =~ ^[0-9a-f]{32}$ ]]', source)

    def test_local_python_validation_cannot_dirty_candidate_worktree(self) -> None:
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertRegex(ignore, r"(?m)^__pycache__/$")
        self.assertRegex(ignore, r"(?m)^\*\.py\[cod\]$")

    def test_release_concurrency_timeouts_and_summary_are_fail_closed(self) -> None:
        concurrency = self.workflow["concurrency"]
        self.assertIs(concurrency["cancel-in-progress"], False)
        self.assertIn("candidate:{1}:{2}", concurrency["group"])
        self.assertIn("inputs.candidate_id", concurrency["group"])
        self.assertIn("formal:{1}", concurrency["group"])

        jobs = self.workflow["jobs"]
        expected_timeouts = {
            "verify-repository": 30,
            "verify-release-assets": 55,
            "verify-cocoapods-consumer": 55,
            "verify-swiftpm-consumer": 55,
            "release-summary": 5,
        }
        for job_name, timeout in expected_timeouts.items():
            with self.subTest(job=job_name):
                self.assertEqual(jobs[job_name]["timeout-minutes"], timeout)

        summary = jobs["release-summary"]
        self.assertEqual(summary["if"], "${{ always() }}")
        self.assertEqual(
            set(summary["needs"]),
            {
                "verify-repository",
                "verify-release-assets",
                "verify-cocoapods-consumer",
                "verify-swiftpm-consumer",
            },
        )
        self.assertEqual(summary["permissions"], {})
        self.assertEqual(len(summary["steps"]), 1)
        script = summary["steps"][0]["run"]
        self.assertIn("GITHUB_STEP_SUMMARY", script)
        self.assertIn("ASSET_IDENTITY", script)
        self.assertIn("failure|cancelled|timed_out|action_required", script)
        self.assertNotIn("GITHUB_TOKEN", json.dumps(summary))

    def test_releasing_declares_private_orchestrator_as_only_entry(self) -> None:
        releasing = (ROOT / "RELEASING.md").read_text(encoding="utf-8")
        self.assertIn("## 正式发布唯一入口", releasing)
        self.assertIn("scripts/release-orchestrator.py", releasing)
        self.assertIn("底层门禁或故障诊断入口", releasing)

    def test_demo_disabled_format_gate_does_not_reject_splash_slot(self) -> None:
        source = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        match = re.search(
            r"grep -R -n -E --exclude-dir=build '([^']+)' YTIFLYADLibSimple",
            source,
        )
        self.assertIsNotNone(match)
        pattern = re.compile(match.group(1))

        self.assertIsNone(pattern.search("__SPLASH_NATIVE_AD_UNIT_ID__"))
        for forbidden in (
            "YTIFLYBannerAd",
            "YTIFLYRewardVideo",
            "YTIFLYNativeFeedAd",
            "__BANNER_AD_UNIT_ID__",
            "__REWARD_VIDEO_AD_UNIT_ID__",
            "__TYPED_ONE_NATIVE_AD_UNIT_ID__",
            "__TYPED_MORE_NATIVE_AD_UNIT_ID__",
            "__FEED_VIDEO_AD_UNIT_ID__",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertIsNotNone(pattern.search(forbidden))

    def test_candidate_uses_final_formal_manifest_and_provenance(self) -> None:
        jobs = self.workflow["jobs"]
        repository_steps = jobs["verify-repository"]["steps"]
        formal_guard = next(
            step
            for step in repository_steps
            if step.get("name") == "Draft candidate 明确要求最终 FORMAL A/B"
        )
        self.assertIn("state != 'FORMAL'", formal_guard["if"])

        compare = next(
            step
            for step in repository_steps
            if step.get("name")
            == "Candidate/正式 tag/Release 校验 FORMAL A/B provenance（私有仓 compare）"
        )
        self.assertIn("inputs.validation_mode == 'draft_candidate'", compare["if"])

        manifest = next(
            step
            for step in repository_steps
            if step.get("name") == "固定 draft candidate 本地分发清单"
        )
        self.assertIn('re.fullmatch(r"[0-9a-f]{64}", checksum)', manifest["run"])
        self.assertIn('`releaseState`：`FORMAL`', manifest["run"])
        self.assertNotIn("CHECKSUM_PENDING", manifest["run"])

        asset_provenance = next(
            step
            for step in jobs["verify-release-assets"]["steps"]
            if step.get("name") == "校验下载资产与私有源码 A/B provenance"
        )
        self.assertNotIn("if", asset_provenance)

    def test_formal_documents_distinguish_frozen_and_published_semantics(self) -> None:
        repository_steps = self.workflow["jobs"]["verify-repository"]["steps"]
        validation = next(
            step
            for step in repository_steps
            if step.get("name") == "校验版本、清单与 SwiftPM 资源"
        )
        script = validation["run"]
        self.assertEqual(
            validation["env"]["RELEASE_VALIDATION_KIND"],
            "${{ steps.release-selection.outputs.kind }}",
        )
        for marker in (
            "`releaseState=FORMAL` 表示正式签名资产、checksum 和 A/B ",
            "元数据已经冻结",
            "公开可用性以同版本 GitHub Release 和发布后 CI 为准",
            "本提交是 `{pod_version}` 的不可变发布目标",
        ):
            self.assertIn(marker, script)
        for frozen_claim_marker in (
            "volatile_publication_claims",
            "(?:当前最新公开正式版|`?{re.escape(pod_version)}`?)",
            "(?:匿名下载|匿名消费|匿名验证|匿名终验)",
            "(?:Actions|Run\\s+[0-9]+|published CI|发布后 CI)",
            "for volatile_publication_claim in volatile_publication_claims",
            "not re.search(",
        ):
            self.assertIn(frozen_claim_marker, script)
        self.assertIn("if frozen_document_context:", script)
        self.assertIn("if not frozen_document_context:", script)
        for published_evidence in (
            "https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/",
            "https://github\\.com/LJMcarryu/YTIFLYADLib_iOS/actions/runs/",
            "当前版本文档 Actions Run 不一致",
        ):
            self.assertIn(published_evidence, script)
        self.assertNotIn('assert f"当前版本：`{pod_version}`" in readme', script)
        self.assertNotIn(
            'assert f"`{pod_version}` 正式分发资产" in release_state', script
        )
        pending_title = 'assert "## 6.2.3 准备状态" in releasing'
        self.assertIn(pending_title, script)
        self.assertGreater(script.index(pending_title), script.index("if checksum == pending_checksum:"))
        self.assertLess(script.index(pending_title), script.index("else:"))

    def test_real_repository_documents_follow_embedded_validation_for_state(self) -> None:
        repository_steps = self.workflow["jobs"]["verify-repository"]["steps"]
        validation = next(
            step
            for step in repository_steps
            if step.get("name") == "校验版本、清单与 SwiftPM 资源"
        )
        match = re.search(
            r"(?ms)^python3 - <<'PY'\n(?P<script>.*?)^PY\s*$",
            validation["run"],
        )
        self.assertIsNotNone(match, "未提取到 workflow 的内嵌 FORMAL Python 门禁")

        package = (ROOT / "Package.swift").read_text(encoding="utf-8")
        pending_checksum = "__YTIFLYADLIB_6_2_3_SWIFTPM_CHECKSUM_PENDING__"
        if pending_checksum in package:
            self.skipTest("仓库仍为 PENDING；FORMAL 内嵌门禁留待候选态执行")

        with tempfile.TemporaryDirectory() as directory:
            podspec = subprocess.run(
                ["pod", "ipc", "spec", str(ROOT / "YTIFLYADLib.podspec")],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, podspec.returncode, podspec.stdout + podspec.stderr)
            podspec_json = Path(directory) / "yt-podspec.json"
            podspec_json.write_text(podspec.stdout, encoding="utf-8")

            script = match.group("script").replace(
                json.dumps("/tmp/yt-podspec.json"),
                json.dumps(str(podspec_json)),
            )
            environment = os.environ.copy()
            environment.update(
                {
                    "GITHUB_REF_TYPE": "branch",
                    "GITHUB_REF_NAME": "main",
                    "RELEASE_VALIDATION_KIND": "none",
                }
            )
            result = subprocess.run(
                ["python3", "-c", script],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

            for label, frozen_environment in (
                (
                    "draft candidate",
                    {
                        "GITHUB_REF_TYPE": "branch",
                        "GITHUB_REF_NAME": "release-candidate/6.2.3-test",
                        "RELEASE_VALIDATION_KIND": "draft",
                    },
                ),
                (
                    "annotated tag",
                    {
                        "GITHUB_REF_TYPE": "tag",
                        "GITHUB_REF_NAME": "6.2.3",
                        "RELEASE_VALIDATION_KIND": "none",
                    },
                ),
            ):
                with self.subTest(context=label):
                    environment = os.environ.copy()
                    environment.update(frozen_environment)
                    frozen_result = subprocess.run(
                        ["python3", "-c", script],
                        cwd=ROOT,
                        env=environment,
                        capture_output=True,
                        text=True,
                    )
                    self.assertNotEqual(0, frozen_result.returncode)
                    self.assertIn(
                        "冻结提交提前声明发布后事实",
                        frozen_result.stdout + frozen_result.stderr,
                    )

    def test_formal_mode_keeps_post_publish_anonymous_and_tag_gates(self) -> None:
        jobs = self.workflow["jobs"]
        self.assertEqual(self.workflow["on"]["release"]["types"], ["published"])
        repository_steps = jobs["verify-repository"]["steps"]
        tag_gate = next(
            step
            for step in repository_steps
            if step.get("name") == "Tag push 校验 annotated tag 与 checkout 绑定"
        )["run"]
        for marker in (
            'git cat-file -t "refs/tags/${GITHUB_REF_NAME}"',
            'git rev-parse "${GITHUB_REF_NAME}^{commit}"',
            "git describe --tags --exact-match HEAD",
        ):
            self.assertIn(marker, tag_gate)

        formal_downloads = [
            step
            for job in jobs.values()
            for step in job["steps"]
            if "正式 Release 资产" in step.get("name", "")
            or step.get("name") == "匿名下载本次 Release 的精确资产集"
        ]
        self.assertEqual(len(formal_downloads), 3)
        for step in formal_downloads:
            self.assertIn("release_kind == 'formal'", step["if"])
            self.assertNotIn("GITHUB_TOKEN", step.get("env", {}))
            self.assertIn("download_release_anonymously.py", step["run"])
            for token_name in (
                "GH_TOKEN",
                "GITHUB_TOKEN",
                "GITHUB_AUTH_TOKEN",
                "IFLY_PRIVATE_SOURCE_TOKEN",
            ):
                self.assertIn(f"-u {token_name}", step["run"])

    def test_no_cache_or_plaintext_artifact_transfer(self) -> None:
        text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertNotIn("actions/cache", text)
        self.assertNotIn("upload-artifact", text)
        self.assertNotIn("download-artifact", text)
        self.assertNotIn("runner.temp", text)
        self.assertNotIn("/tmp/yt-release-anonymous", text)
        self.assertIn("CP_HOME_DIR", text)
        self.assertIn("-clonedSourcePackagesDirPath", text)
        self.assertIn("-packageCachePath", text)
        self.assertIn("-disablePackageRepositoryCache", text)


if __name__ == "__main__":
    unittest.main()
