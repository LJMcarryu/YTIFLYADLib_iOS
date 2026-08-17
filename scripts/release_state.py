#!/usr/bin/env python3
"""校验或从严格 freeze/closeout facts 原子生成公开仓发布状态。"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


PHASES = ("PREPARING", "FROZEN", "PUBLISHED", "VERIFIED", "CLOSED")
CHANNELS = ("general", "ys", "youku", "yt")
SHA40 = re.compile(r"[0-9a-f]{40}")
SHA64 = re.compile(r"[0-9a-f]{64}")
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")
TIMESTAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")


class ReleaseStateError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReleaseStateError(message)


def exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    require(set(value) == expected, f"{label} 字段漂移: {sorted(set(value) ^ expected)}")


def require_sha(value: Any, pattern: re.Pattern[str], label: str) -> None:
    require(isinstance(value, str) and pattern.fullmatch(value) is not None,
            f"{label} 格式非法")


def validate_apple_review(value: Any) -> dict[str, Any]:
    require(isinstance(value, dict), "appleReview 必须是对象")
    exact_keys(value, {"requiredForRelease", "statusAtFreeze", "evidenceIncluded"},
               "appleReview")
    require(value == {
        "requiredForRelease": False,
        "statusAtFreeze": "not-run",
        "evidenceIncluded": False,
    }, "当前正式状态不得把未执行 Apple Review 扫描写成通过")
    return value


def validate_publication(value: Any, repository: str, version: str) -> dict[str, Any]:
    require(isinstance(value, dict), "publication 必须是对象")
    exact_keys(
        value,
        {
            "releaseId", "tagName", "tagObjectSha", "tagCommitSha", "releaseUrl",
            "publishedAt", "formalConsumerRunId", "formalConsumerRunUrl",
            "conclusion", "verifiedAt",
        },
        "publication",
    )
    release_id = value["releaseId"]
    run_id = value["formalConsumerRunId"]
    require(isinstance(release_id, int) and not isinstance(release_id, bool)
            and release_id > 0, "CLOSED 缺少 releaseId")
    require(isinstance(run_id, int) and not isinstance(run_id, bool) and run_id > 0,
            "CLOSED 缺少 consumer runId")
    require(value["tagName"] == version, "tagName 与 version 不一致")
    require_sha(value["tagObjectSha"], SHA40, "annotated tag object SHA")
    require_sha(value["tagCommitSha"], SHA40, "tag commit SHA")
    require(value["tagObjectSha"] != value["tagCommitSha"],
            "tagObjectSha 必须是 annotated tag 对象而非解引用提交")
    require(value["releaseUrl"] ==
            f"https://github.com/{repository}/releases/tag/{version}",
            "releaseUrl 与仓库、版本不一致")
    require(value["formalConsumerRunUrl"] ==
            f"https://github.com/{repository}/actions/runs/{run_id}",
            "formalConsumerRunUrl 与仓库、runId 不一致")
    require(value["conclusion"] == "success", "CLOSED consumer 必须 success")
    for key in ("publishedAt", "verifiedAt"):
        require(isinstance(value[key], str) and TIMESTAMP.fullmatch(value[key]) is not None,
                f"{key} 必须为 UTC 秒精度时间")
    require(value["verifiedAt"] >= value["publishedAt"],
            "verifiedAt 不得早于 publishedAt")
    return value


def require_non_closed_publication(value: Any) -> None:
    require(value is None, "非 CLOSED 状态的 publication 必须为 null")


def artifact_inventory_sha256(artifacts: Any) -> tuple[int, str]:
    """复用正式下载链的稳定算法：name + NUL + contentSha256 + LF。"""
    require(isinstance(artifacts, list) and artifacts, "artifacts 必须是非空数组")
    normalized: list[tuple[str, str]] = []
    for index, artifact in enumerate(artifacts):
        require(isinstance(artifact, dict), f"artifacts[{index}] 必须是对象")
        exact_keys(artifact, {"name", "contentSha256"}, f"artifacts[{index}]")
        name = artifact["name"]
        digest = artifact["contentSha256"]
        require(isinstance(name, str) and name != "" and Path(name).name == name
                and "\0" not in name and "\n" not in name and "\r" not in name,
                f"artifacts[{index}].name 非法")
        require_sha(digest, SHA64, f"artifacts[{index}].contentSha256")
        normalized.append((name, digest))
    names = [name for name, _ in normalized]
    require(len(set(names)) == len(names), "artifacts.name 不得重复")

    import hashlib

    digest = hashlib.sha256()
    for name, content_sha256 in sorted(normalized):
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(content_sha256.encode("ascii"))
        digest.update(b"\n")
    return len(normalized), digest.hexdigest()


def validate_state(
    value: Any,
    *,
    expected_channel: str | None = None,
    expected_repository: str | None = None,
    expected_version: str | None = None,
) -> dict[str, Any]:
    require(isinstance(value, dict), "release-state 根必须是对象")
    exact_keys(
        value,
        {
            "schemaVersion", "channel", "repository", "version", "phase",
            "binarySourceCommit", "releaseMetadataCommit", "artifactInventory",
            "appleReview", "publication",
        },
        "release-state",
    )
    require(value["schemaVersion"] == 1, "仅支持 release-state schemaVersion=1")
    require(value["channel"] in CHANNELS, f"非法 channel: {value['channel']!r}")
    repository = value["repository"]
    version = value["version"]
    require(isinstance(repository, str)
            and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) is not None,
            "repository 必须为 owner/name")
    require(isinstance(version, str) and VERSION.fullmatch(version) is not None,
            "version 必须为 x.y.z")
    require(value["phase"] in PHASES, f"非法 phase: {value['phase']!r}")
    require_sha(value["binarySourceCommit"], SHA40, "binarySourceCommit")
    require_sha(value["releaseMetadataCommit"], SHA40, "releaseMetadataCommit")
    require(value["binarySourceCommit"] != value["releaseMetadataCommit"], "A/B 不得相同")
    if expected_channel is not None:
        require(value["channel"] == expected_channel, "channel 与仓库不一致")
    if expected_repository is not None:
        require(repository == expected_repository, "repository 与仓库不一致")
    if expected_version is not None:
        require(version == expected_version, "version 与预期不一致")

    inventory = value["artifactInventory"]
    require(isinstance(inventory, dict), "artifactInventory 必须是对象")
    exact_keys(inventory, {"count", "sha256"}, "artifactInventory")
    require(isinstance(inventory["count"], int)
            and not isinstance(inventory["count"], bool) and inventory["count"] > 0,
            "artifactInventory.count 必须是正整数")
    require_sha(inventory["sha256"], SHA64, "artifactInventory.sha256")
    validate_apple_review(value["appleReview"])
    if value["phase"] == "CLOSED":
        validate_publication(value["publication"], repository, version)
    else:
        require_non_closed_publication(value["publication"])
    return value


def validate_freeze_facts(value: Any) -> dict[str, Any]:
    require(isinstance(value, dict), "freeze facts 根必须是对象")
    exact_keys(
        value,
        {
            "schemaVersion", "channel", "repository", "version", "phase",
            "binarySourceCommit", "releaseMetadataCommit", "artifacts", "appleReview",
        },
        "freeze facts",
    )
    require(value["schemaVersion"] == 1, "仅支持 freeze facts schemaVersion=1")
    require(value["phase"] == "FROZEN", "freeze facts 只能生成 FROZEN 状态")
    count, inventory_sha256 = artifact_inventory_sha256(value["artifacts"])
    validate_state({
        "schemaVersion": value["schemaVersion"],
        "channel": value["channel"],
        "repository": value["repository"],
        "version": value["version"],
        "phase": "FROZEN",
        "binarySourceCommit": value["binarySourceCommit"],
        "releaseMetadataCommit": value["releaseMetadataCommit"],
        "artifactInventory": {"count": count, "sha256": inventory_sha256},
        "appleReview": value["appleReview"],
        "publication": None,
    })
    return value


def build_frozen_state(facts: Any) -> dict[str, Any]:
    validate_freeze_facts(facts)
    count, inventory_sha256 = artifact_inventory_sha256(facts["artifacts"])
    return validate_state({
        "schemaVersion": 1,
        "channel": facts["channel"],
        "repository": facts["repository"],
        "version": facts["version"],
        "phase": "FROZEN",
        "binarySourceCommit": facts["binarySourceCommit"],
        "releaseMetadataCommit": facts["releaseMetadataCommit"],
        "artifactInventory": {"count": count, "sha256": inventory_sha256},
        "appleReview": dict(facts["appleReview"]),
        "publication": None,
    })


def validate_closeout_facts(value: Any) -> dict[str, Any]:
    require(isinstance(value, dict), "closeout facts 根必须是对象")
    exact_keys(
        value,
        {
            "schemaVersion", "channel", "repository", "version", "phase",
            "binarySourceCommit", "releaseMetadataCommit", "artifacts",
            "appleReview", "publication",
        },
        "closeout facts",
    )
    require(value["schemaVersion"] == 1, "仅支持 closeout facts schemaVersion=1")
    require(value["phase"] == "CLOSED", "closeout facts 只能生成 CLOSED 状态")
    artifact_inventory_sha256(value["artifacts"])
    state = {
        key: value[key]
        for key in (
            "schemaVersion", "channel", "repository", "version", "phase",
            "binarySourceCommit", "releaseMetadataCommit", "appleReview", "publication",
        )
    }
    count, inventory_sha256 = artifact_inventory_sha256(value["artifacts"])
    state["artifactInventory"] = {"count": count, "sha256": inventory_sha256}
    validate_state(state)
    return value


def build_closed_state(facts: Any) -> dict[str, Any]:
    validate_closeout_facts(facts)
    count, inventory_sha256 = artifact_inventory_sha256(facts["artifacts"])
    return validate_state({
        "schemaVersion": 1,
        "channel": facts["channel"],
        "repository": facts["repository"],
        "version": facts["version"],
        "phase": "CLOSED",
        "binarySourceCommit": facts["binarySourceCommit"],
        "releaseMetadataCommit": facts["releaseMetadataCommit"],
        "artifactInventory": {"count": count, "sha256": inventory_sha256},
        "appleReview": dict(facts["appleReview"]),
        "publication": dict(facts["publication"]),
    })


def build_state_from_facts(facts: Any) -> dict[str, Any]:
    require(isinstance(facts, dict), "facts 根必须是对象")
    phase = facts.get("phase")
    if phase == "FROZEN":
        return build_frozen_state(facts)
    if phase == "CLOSED":
        return build_closed_state(facts)
    raise ReleaseStateError("facts.phase 只允许 FROZEN 或 CLOSED")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_and_validate(path: Path, **expected: str | None) -> dict[str, Any]:
    return validate_state(load_json(path), **expected)


def canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def version_tuple(version: str) -> tuple[int, int, int]:
    require(VERSION.fullmatch(version) is not None, "version 必须为 x.y.z")
    return tuple(int(part) for part in version.split("."))  # type: ignore[return-value]


def validate_state_transition(current: dict[str, Any], target: dict[str, Any]) -> None:
    validate_state(current)
    validate_state(target)
    if current == target:
        return

    require(current["schemaVersion"] == target["schemaVersion"],
            "状态转换不得改变 schemaVersion")
    for key in ("channel", "repository"):
        require(current[key] == target[key], f"状态转换不得改变 {key}")

    if current["phase"] == "PREPARING" and target["phase"] == "FROZEN":
        for key in (
            "version", "binarySourceCommit", "releaseMetadataCommit", "appleReview",
        ):
            require(current[key] == target[key], f"PREPARING→FROZEN 不得改变 {key}")
        return

    if current["phase"] == "FROZEN" and target["phase"] == "CLOSED":
        for key in (
            "version", "binarySourceCommit", "releaseMetadataCommit",
            "artifactInventory", "appleReview",
        ):
            require(current[key] == target[key], f"FROZEN→CLOSED 不得改变 {key}")
        return

    if current["phase"] == "CLOSED" and target["phase"] == "FROZEN":
        require(version_tuple(target["version"]) > version_tuple(current["version"]),
                "历史 CLOSED 只能进入更高版本的 FROZEN")
        return

    raise ReleaseStateError(
        f"非法状态转换: {current['phase']} {current['version']} → "
        f"{target['phase']} {target['version']}"
    )


def validate_closeout_transition(current: dict[str, Any], closed: dict[str, Any]) -> None:
    """保留旧调用入口；实际使用统一严格状态转换器。"""
    require(closed.get("phase") == "CLOSED", "目标状态必须为 CLOSED")
    validate_state_transition(current, closed)


def atomic_write_state(path: Path, state: dict[str, Any]) -> None:
    require(path.parent.is_dir(), f"输出目录不存在: {path.parent}")
    payload = canonical_json(validate_state(state))
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            os.fchmod(handle.fileno(), mode)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--facts", type=Path,
                        help="严格 freeze/closeout facts JSON；默认仅生成到 stdout")
    parser.add_argument("--write", action="store_true",
                        help="将生成状态原子写入 path；未指定时保持 dry-run")
    parser.add_argument("--expected-channel")
    parser.add_argument("--expected-repository")
    parser.add_argument("--expected-version")
    args = parser.parse_args(argv)
    if args.write and args.facts is None:
        parser.error("--write 必须与 --facts 一起使用")
    expected = {
        "expected_channel": args.expected_channel,
        "expected_repository": args.expected_repository,
        "expected_version": args.expected_version,
    }
    try:
        if args.facts is None:
            state = load_and_validate(args.path, **expected)
            print(f"release-state 校验通过: {state['channel']} {state['version']} {state['phase']}")
            return 0
        state = validate_state(build_state_from_facts(load_json(args.facts)), **expected)
        if not args.write:
            sys.stdout.write(canonical_json(state))
            return 0
        if args.path.exists():
            validate_state_transition(load_and_validate(args.path), state)
        atomic_write_state(args.path, state)
        persisted = load_and_validate(args.path, **expected)
        require(persisted == state, "原子写入后读回状态不一致")
        print(
            f"release-state 已原子更新: "
            f"{state['channel']} {state['version']} {state['phase']}"
        )
        return 0
    except (OSError, json.JSONDecodeError, ReleaseStateError) as exc:
        print(f"release-state 处理失败: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
