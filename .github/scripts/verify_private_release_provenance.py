#!/usr/bin/env python3
"""校验 YT 正式发布与私有源码仓的 provenance。"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Tuple
from urllib.parse import quote
from urllib.request import Request, urlopen


PRIVATE_SOURCE_REPOSITORY = "LJMcarryu/IFLYADLibDemo"
USER_AGENT = "YTIFLYADLib-private-provenance-verifier"
ALLOWED_METADATA_FILES = {"Package.swift", "README.md", "CONTEXT.md"}
CURRENT_RELEASE_VERSION = "6.2.4"
PENDING_BINARY = "__YTIFLYADLIB_6_2_4_BINARY_SOURCE_COMMIT_PENDING__"
PENDING_METADATA = "__YTIFLYADLIB_6_2_4_RELEASE_METADATA_COMMIT_PENDING__"


class VerificationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def current_release_section(document: str, label: str) -> str:
    """返回唯一的当前版本 Markdown 章节，排除历史版本声明。"""

    heading = re.compile(
        rf"^(?P<marks>\#{{1,6}})[ \t]+(?:\[{re.escape(CURRENT_RELEASE_VERSION)}\]|"
        rf"{re.escape(CURRENT_RELEASE_VERSION)})(?=$|[ \t（(])",
    )
    generic_heading = re.compile(r"^(?P<marks>\#{1,6})[ \t]+")
    lines = document.splitlines(keepends=True)
    matches = [
        (index, len(match.group("marks")))
        for index, line in enumerate(lines)
        if (match := heading.match(line)) is not None
    ]
    require(
        len(matches) == 1,
        f"{label} 必须唯一包含 {CURRENT_RELEASE_VERSION} 当前发布状态节",
    )
    start, level = matches[0]
    end = len(lines)
    for index in range(start + 1, len(lines)):
        match = generic_heading.match(lines[index])
        if match is not None and len(match.group("marks")) <= level:
            end = index
            break
    return "".join(lines[start:end])


def parse_document(document: str, label: str) -> Tuple[str, str, str]:
    section = current_release_section(document, label)
    binary_patterns = (
        r"^\s*-\s*`binarySourceCommit`（SDK 二进制源码提交）：`([^`]+)`\s*$",
        r"^\s*binarySourceCommit（提交 A）：`([^`]+)`\s*$",
    )
    metadata_patterns = (
        r"^\s*-\s*`releaseMetadataCommit`（仅回填 checksum、扫描汇总和发布验收事实，"
        r"不是 SDK 二进制源码提交）：`([^`]+)`\s*$",
        r"^\s*releaseMetadataCommit（提交 B）：`([^`]+)`\s*$",
    )
    binary_matches = [
        value for pattern in binary_patterns for value in re.findall(pattern, section, re.M)
    ]
    metadata_matches = [
        value for pattern in metadata_patterns for value in re.findall(pattern, section, re.M)
    ]
    states = re.findall(
        r"^\s*-\s*`releaseState`：`(PENDING|FORMAL)`\s*$", section, re.M
    )
    require(
        len(binary_matches) == len(metadata_matches) == len(states) == 1,
        f"{label} 的 {CURRENT_RELEASE_VERSION} 当前节必须唯一声明 releaseState/A/B",
    )
    binary_commit = binary_matches[0]
    metadata_commit = metadata_matches[0]
    return states[0], binary_commit, metadata_commit


def validate_documents(paths: Tuple[Path, Path, Path]) -> Tuple[str, str, str]:
    values = tuple(
        parse_document(path.read_text(encoding="utf-8"), str(path)) for path in paths
    )
    require(
        len(set(values)) == 1,
        "README.md、CHANGELOG.md、RELEASING.md 的 releaseState/A/B 必须一致",
    )
    state, binary_commit, metadata_commit = values[0]
    pending = (
        state == "PENDING"
        and binary_commit == PENDING_BINARY
        and metadata_commit == PENDING_METADATA
    )
    formal = (
        state == "FORMAL"
        and re.fullmatch(r"[0-9a-f]{40}", binary_commit) is not None
        and re.fullmatch(r"[0-9a-f]{40}", metadata_commit) is not None
        and binary_commit != metadata_commit
    )
    require(
        pending or formal,
        "A/B 必须同时为精确 PENDING，或为 FORMAL 状态下两个不同的 40 位小写 SHA",
    )
    return state, binary_commit, metadata_commit


def validate_manifest(
    manifest: Dict[str, Any], binary_commit: str, metadata_commit: str
) -> None:
    require(
        manifest.get("sourceCommit") == binary_commit,
        "delivery-manifest.sourceCommit 必须等于 binarySourceCommit A",
    )
    source_build = manifest.get("sourceBuild")
    require(isinstance(source_build, dict), "delivery-manifest 缺少 sourceBuild")
    require(
        source_build.get("sourceCommit") == binary_commit,
        "delivery-manifest.sourceBuild.sourceCommit 必须等于 binarySourceCommit A",
    )
    require(
        manifest.get("sourceCommit") != metadata_commit
        and source_build.get("sourceCommit") != metadata_commit,
        "releaseMetadataCommit B 不得冒充二进制 sourceCommit",
    )


def validate_release_body(body: str, binary_commit: str, metadata_commit: str) -> None:
    lines = [line.strip() for line in body.splitlines()]
    accepted_forms = (
        (
            f"- `binarySourceCommit`（SDK 二进制源码提交）：`{binary_commit}`",
            f"- `releaseMetadataCommit`（仅回填 checksum、扫描汇总和发布验收事实，不是 SDK 二进制源码提交）：`{metadata_commit}`",
        ),
        (
            f"二进制源码提交（binarySourceCommit A）：`{binary_commit}`",
            f"发布元数据提交（releaseMetadataCommit B）：`{metadata_commit}`",
        ),
    )
    forms = [form for form in accepted_forms if all(lines.count(item) == 1 for item in form)]
    require(len(forms) == 1, "Release body 缺少或重复正式 provenance A/B 声明")
    required_line = f"delivery-manifest.sourceCommit / sourceBuild.sourceCommit：`{binary_commit}`"
    require(lines.count(required_line) == 1, f"Release body 缺少或重复正式 provenance 声明: {required_line}")
    require(lines.count("B 仅用于 checksum、扫描汇总和验收事实，不是 SDK 二进制源码提交。") == 1,
            "Release body 缺少 B 角色说明")
    require(
        not any(
            metadata_commit in line
            and ("delivery-manifest.sourceCommit" in line or "sourceBuild.sourceCommit" in line)
            for line in lines
        ),
        "Release body 不得把 releaseMetadataCommit B 声明为 sourceCommit",
    )


def metadata_path_allowed(path: str) -> bool:
    return path in ALLOWED_METADATA_FILES or path.startswith("docs/")


def validate_compare_response(
    comparison: Dict[str, Any], binary_commit: str, metadata_commit: str
) -> None:
    require(comparison.get("status") == "ahead", "私有仓 compare 状态必须为 ahead")
    require(comparison.get("ahead_by", 0) >= 1, "提交 B 必须领先提交 A")
    require(comparison.get("behind_by") == 0, "提交 B 不得落后于提交 A")
    require(
        comparison.get("base_commit", {}).get("sha") == binary_commit,
        "compare base_commit 不是提交 A",
    )
    require(
        comparison.get("merge_base_commit", {}).get("sha") == binary_commit,
        "提交 A 不是提交 B 的祖先",
    )

    commits = comparison.get("commits")
    require(isinstance(commits, list) and commits, "compare 未返回 A→B 提交列表")
    total_commits = comparison.get("total_commits")
    require(
        isinstance(total_commits, int)
        and total_commits == comparison.get("ahead_by")
        and total_commits == len(commits),
        "compare 提交列表被分页截断或计数不一致",
    )
    require(commits[-1].get("sha") == metadata_commit, "A→B 提交列表未终止于 B")

    files = comparison.get("files")
    require(isinstance(files, list) and files, "提交 A→B 不得是空变更")
    require(len(files) < 300, "compare 文件列表可能达到 GitHub 截断上限，拒绝放行")
    for file_metadata in files:
        path = file_metadata.get("filename")
        previous_path = file_metadata.get("previous_filename")
        require(
            isinstance(path, str) and metadata_path_allowed(path),
            f"提交 A→B 修改了非元数据路径: {path!r}",
        )
        if previous_path is not None:
            require(
                isinstance(previous_path, str) and metadata_path_allowed(previous_path),
                f"提交 A→B 从非元数据路径重命名: {previous_path!r}",
            )


def fetch_comparison(token: str, binary_commit: str, metadata_commit: str) -> Dict[str, Any]:
    require(bool(token.strip()), "缺少 IFLY_PRIVATE_SOURCE_TOKEN，正式发布必须 fail-closed")
    url = (
        f"https://api.github.com/repos/{PRIVATE_SOURCE_REPOSITORY}/compare/"
        f"{quote(binary_commit, safe='')}...{quote(metadata_commit, safe='')}?per_page=100"
    )
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    require(
        urlsplit_host(request.full_url) == "api.github.com",
        "私有仓令牌只能发送到 api.github.com",
    )
    require(
        f"/repos/{PRIVATE_SOURCE_REPOSITORY}/compare/" in request.full_url,
        "私有仓令牌只能用于固定 provenance compare API",
    )
    with urlopen(request, timeout=30) as response:
        require(response.status == 200, f"私有仓 compare API HTTP {response.status}")
        return json.loads(response.read().decode("utf-8"))


def urlsplit_host(url: str) -> str:
    # Kept local to make the fixed-token destination assertion easy to unit-test.
    from urllib.parse import urlsplit

    return (urlsplit(url).hostname or "").lower()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--readme", type=Path)
    parser.add_argument("--changelog", type=Path)
    parser.add_argument("--releasing", type=Path)
    parser.add_argument("--release-state", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--release-metadata", type=Path)
    parser.add_argument("--token-env", default="IFLY_PRIVATE_SOURCE_TOKEN")
    parser.add_argument("--skip-compare", action="store_true")
    args = parser.parse_args()

    try:
        if args.release_state:
            sys.path.insert(0, str(Path.cwd() / "scripts"))
            from release_state import validate_state

            machine_state = validate_state(json.loads(args.release_state.read_text(encoding="utf-8")))
            require(machine_state["phase"] != "PREPARING", "发布 provenance 不接受 PREPARING")
            state = "FORMAL"
            binary_commit = machine_state["binarySourceCommit"]
            metadata_commit = machine_state["releaseMetadataCommit"]
            require(not any((args.readme, args.changelog, args.releasing)),
                    "--release-state 不得混入 Markdown provenance 输入")
        else:
            require(all((args.readme, args.changelog, args.releasing)),
                    "维护检查必须同时提供 README/CHANGELOG/RELEASING")
            state, binary_commit, metadata_commit = validate_documents(
                (args.readme, args.changelog, args.releasing)
            )
        if state == "PENDING":
            require(args.skip_compare, "PENDING 准备态只能跳过私有仓 compare")
            require(not args.manifest and not args.release_metadata,
                    "PENDING 准备态不得校验正式 Release 资产")
            print("验证 PENDING A/B provenance：精确占位且三份元数据一致")
            return 0

        if args.skip_compare:
            require(not args.manifest and not args.release_metadata,
                    "未执行 compare 时不得校验正式 Release 资产")
            print("验证 FORMAL A/B provenance 文档：三份元数据一致且为两个不同 SHA")
            return 0
        if args.manifest:
            validate_manifest(
                json.loads(args.manifest.read_text(encoding="utf-8")),
                binary_commit,
                metadata_commit,
            )
        if args.release_metadata:
            release = json.loads(args.release_metadata.read_text(encoding="utf-8"))
            validate_release_body(
                release.get("body", ""), binary_commit, metadata_commit
            )

        token = os.environ.get(args.token_env, "")
        comparison = fetch_comparison(token, binary_commit, metadata_commit)
        validate_compare_response(comparison, binary_commit, metadata_commit)
        print(
            "验证 FORMAL 私有源码 provenance："
            f"binarySourceCommit A={binary_commit}, "
            f"releaseMetadataCommit B={metadata_commit}"
        )
    except (OSError, ValueError, json.JSONDecodeError, VerificationError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
