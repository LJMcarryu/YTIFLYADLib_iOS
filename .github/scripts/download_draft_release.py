#!/usr/bin/env python3
"""使用最小权限下载并验证同仓 draft Release 的精确资产集。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from download_release_anonymously import (
    VerificationError,
    download_with_retry,
    expected_asset_names,
    require,
    validate_asset_inventory,
)


USER_AGENT = "YTIFLYADLib-draft-release-verifier"
UNEXPECTED_TOKEN_ENVIRONMENT_VARIABLES = (
    "GH_TOKEN",
    "GITHUB_AUTH_TOKEN",
    "IFLY_PRIVATE_SOURCE_TOKEN",
)
CANDIDATE_LINE_RE = re.compile(
    r"^- `candidateId`：`([0-9a-f]{64})`\s*$", re.MULTILINE
)
INVENTORY_LINE_RE = re.compile(
    r"^- `uploadInventorySha256`：`([0-9a-f]{64})`\s*$", re.MULTILINE
)
BINARY_SOURCE_LINE_RE = re.compile(
    r"^- `binarySourceCommit`（SDK 二进制源码提交）：`([^`]+)`\s*$",
    re.MULTILINE,
)
RELEASE_METADATA_LINE_RE = re.compile(
    r"^- `releaseMetadataCommit`（仅回填 checksum、扫描汇总和发布验收事实，"
    r"不是 SDK 二进制源码提交）：`([^`]+)`\s*$",
    re.MULTILINE,
)


def is_github_asset_host(host: str) -> bool:
    return host == "github.com" or host.endswith(".githubusercontent.com")


class SafeGitHubAssetRedirectHandler(HTTPRedirectHandler):
    """只允许 GitHub API 跳到 GitHub 资产主机，并在跳转前移除 Token。"""

    def redirect_request(  # type: ignore[override]
        self,
        request: Request,
        file_pointer: Any,
        code: int,
        message: str,
        headers: Any,
        new_url: str,
    ) -> Request | None:
        redirected = super().redirect_request(
            request, file_pointer, code, message, headers, new_url
        )
        if redirected is None:
            return None
        source = urlsplit(request.full_url)
        target = urlsplit(redirected.full_url)
        source_host = (source.hostname or "").lower()
        target_host = (target.hostname or "").lower()
        require(target.scheme == "https", f"资产重定向不是 HTTPS: {new_url}")
        if source_host == "api.github.com":
            require(
                is_github_asset_host(target_host),
                f"GitHub API 重定向到非 GitHub 资产主机: {new_url}",
            )
        else:
            require(
                is_github_asset_host(source_host)
                and is_github_asset_host(target_host),
                f"资产重定向越过 GitHub 主机边界: {new_url}",
            )
        redirected.remove_header("Authorization")
        require(
            not any(
                name.lower() == "authorization"
                for name, _ in redirected.header_items()
            ),
            "跨主机重定向后仍携带 Authorization",
        )
        return redirected


def build_authenticated_request(url: str, accept: str, token: str) -> Request:
    parsed = urlsplit(url)
    require(
        parsed.scheme == "https" and (parsed.hostname or "").lower() == "api.github.com",
        f"Token 只能发送到 api.github.com: {url}",
    )
    request = Request(
        url,
        headers={
            "Accept": accept,
            "Authorization": f"Bearer {token}",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    require(
        request.get_header("Authorization") == f"Bearer {token}",
        "认证请求缺少 Authorization",
    )
    return request


def validate_draft_release_metadata(
    release: Dict[str, Any],
    repository: str,
    tag: str,
    candidate_id: str,
    release_id: int,
    target_branch: str,
    expected_commit: str,
    resolved_target_commit: str | None = None,
) -> Dict[str, Dict[str, Any]]:
    require(
        release.get("id") == release_id,
        "Draft Release ID 与输入不一致",
    )
    require(release.get("tag_name") == tag, "Draft Release tag 与候选版本不一致")
    require(release.get("draft") is True, "候选 Release 必须保持 draft")
    require(release.get("prerelease") is False, "候选 Release 不得为 prerelease")
    require(release.get("published_at") is None, "Draft Release 不得已有 published_at")
    target = release.get("target_commitish")
    require(
        target in {target_branch, expected_commit},
        "Draft Release target_commitish 必须绑定候选分支或精确提交",
    )
    if target == target_branch:
        require(
            resolved_target_commit == expected_commit,
            "Draft Release 候选分支当前提交与触发 checkout 不一致",
        )

    body = release.get("body")
    require(isinstance(body, str), "Draft Release body 缺失")
    candidate_matches = CANDIDATE_LINE_RE.findall(body)
    require(
        candidate_matches == [candidate_id]
        and body.count("`candidateId`") == 1,
        "Draft Release body 必须唯一声明输入 candidateId",
    )
    inventory_matches = INVENTORY_LINE_RE.findall(body)
    require(
        len(inventory_matches) == 1
        and body.count("`uploadInventorySha256`") == 1,
        "Draft Release body 必须唯一声明 uploadInventorySha256",
    )
    binary_matches = BINARY_SOURCE_LINE_RE.findall(body)
    metadata_matches = RELEASE_METADATA_LINE_RE.findall(body)
    require(
        len(binary_matches) == len(metadata_matches) == 1,
        "Draft Release body 必须唯一声明最终 FORMAL A/B",
    )
    binary_commit = binary_matches[0]
    metadata_commit = metadata_matches[0]
    require(
        re.fullmatch(r"[0-9a-f]{40}", binary_commit) is not None,
        "Draft Release body 的 binarySourceCommit A 非 40 位小写 SHA",
    )
    require(
        re.fullmatch(r"[0-9a-f]{40}", metadata_commit) is not None,
        "Draft Release body 的 releaseMetadataCommit B 非 40 位小写 SHA",
    )
    require(binary_commit != metadata_commit, "Draft Release body 的最终 FORMAL A/B 必须不同")

    html_url = release.get("html_url")
    require(isinstance(html_url, str), "Draft Release html_url 缺失")
    html_url_match = re.fullmatch(
        rf"https://github\.com/{re.escape(repository)}/releases/tag/"
        r"(untagged-[0-9a-f]+)",
        html_url,
    )
    require(
        html_url_match is not None,
        f"Draft Release html_url 非同仓 HTTPS untagged 地址: {html_url!r}",
    )
    draft_selector = html_url_match.group(1)

    by_name = validate_asset_inventory(release, tag)
    for asset in by_name.values():
        name = asset["name"]
        asset_id = asset.get("id")
        require(isinstance(asset_id, int) and asset_id > 0, f"{name} 缺少合法 asset id")
        expected_api_url = (
            f"https://api.github.com/repos/{repository}/releases/assets/{asset_id}"
        )
        require(
            asset.get("url") == expected_api_url,
            f"{name} API 下载地址非固定同仓 endpoint: {asset.get('url')!r}",
        )
        expected_browser_url = (
            f"https://github.com/{repository}/releases/download/"
            f"{quote(draft_selector, safe='')}/{quote(name, safe='')}"
        )
        require(
            asset.get("browser_download_url") == expected_browser_url,
            f"{name} browser_download_url 非预期: {asset.get('browser_download_url')!r}",
        )
        require(asset.get("state") == "uploaded", f"{name} 尚未完成上传")
    return by_name


def stable_release_snapshot(release: Dict[str, Any]) -> Dict[str, Any]:
    assets = release.get("assets", [])
    return {
        "id": release.get("id"),
        "tag_name": release.get("tag_name"),
        "draft": release.get("draft"),
        "prerelease": release.get("prerelease"),
        "target_commitish": release.get("target_commitish"),
        "html_url": release.get("html_url"),
        "body": release.get("body"),
        "assets": sorted(
            (
                asset.get("id"),
                asset.get("name"),
                asset.get("size"),
                asset.get("digest"),
                asset.get("url"),
                asset.get("browser_download_url"),
                asset.get("state"),
            )
            for asset in assets
        ),
    }


def download_and_hash(
    opener: Any, asset: Dict[str, Any], destination: Path, token: str
) -> str:
    def open_response():
        request = build_authenticated_request(
            asset["url"], "application/octet-stream", token
        )
        return opener.open(request, timeout=120)

    def validate_response(response) -> None:
        final_url = urlsplit(response.geturl())
        final_host = (final_url.hostname or "").lower()
        require(final_url.scheme == "https", f"资产响应不是 HTTPS: {response.geturl()}")
        require(final_host == "api.github.com" or is_github_asset_host(final_host),
                f"资产响应来自非 GitHub 资产主机: {response.geturl()}")

    return download_with_retry(asset, destination, open_response, validate_response)


def download_release(
    repository: str,
    tag: str,
    candidate_id: str,
    release_id: int,
    target_branch: str,
    expected_commit: str,
    destination: Path,
    metadata_output: Path,
) -> None:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    require(bool(token), "下载 draft Release 必须显式提供 GITHUB_TOKEN")
    unexpected_tokens = [
        name for name in UNEXPECTED_TOKEN_ENVIRONMENT_VARIABLES if os.environ.get(name)
    ]
    require(
        not unexpected_tokens,
        f"draft 下载环境出现非预期凭据变量: {unexpected_tokens}",
    )
    require(
        re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) is not None,
        f"非法 GitHub repository: {repository!r}",
    )
    require(
        re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", tag) is not None,
        f"非法候选版本: {tag!r}",
    )
    require(
        re.fullmatch(r"[0-9a-f]{64}", candidate_id) is not None,
        f"非法 candidateId: {candidate_id!r}",
    )
    require(release_id > 0, f"非法 Draft Release ID: {release_id!r}")
    expected_branch = f"release-candidate/{tag}-{candidate_id}"
    require(target_branch == expected_branch, "候选分支与版本/candidateId 不一致")
    require(
        re.fullmatch(r"[0-9a-f]{40}", expected_commit) is not None,
        f"非法候选提交: {expected_commit!r}",
    )
    require(not metadata_output.exists(), f"元数据输出已存在，禁止覆盖: {metadata_output}")

    api_url = f"https://api.github.com/repos/{repository}/releases/{release_id}"
    expected_api_prefix = f"https://api.github.com/repos/{repository}/releases/"
    require(api_url.startswith(expected_api_prefix), "Release API 不是固定同仓 endpoint")
    opener = build_opener(SafeGitHubAssetRedirectHandler())
    request = build_authenticated_request(api_url, "application/vnd.github+json", token)
    with opener.open(request, timeout=30) as response:
        require(response.status == 200, f"Draft Release API HTTP {response.status}")
        release = json.loads(response.read().decode("utf-8"))

    def resolve_target(value: Dict[str, Any]) -> str | None:
        if value.get("target_commitish") != target_branch:
            return None
        ref_url = (
            f"https://api.github.com/repos/{repository}/git/ref/heads/"
            f"{quote(target_branch, safe='')}"
        )
        ref_request = build_authenticated_request(
            ref_url, "application/vnd.github+json", token
        )
        with opener.open(ref_request, timeout=30) as response:
            require(response.status == 200, f"候选分支 API HTTP {response.status}")
            reference = json.loads(response.read().decode("utf-8"))
        commit = reference.get("object", {}).get("sha")
        require(isinstance(commit, str), "候选分支 API 缺少 object.sha")
        return commit

    assets = validate_draft_release_metadata(
        release,
        repository,
        tag,
        candidate_id,
        release_id,
        target_branch,
        expected_commit,
        resolve_target(release),
    )

    destination.mkdir(parents=True, exist_ok=True)
    for path in destination.iterdir():
        require(path.is_file() and not path.is_symlink(),
                f"下载目录只能包含普通文件缓存: {path}")
        if path.name.endswith(".part"):
            path.unlink()
    for name in sorted(assets):
        actual = download_and_hash(opener, assets[name], destination / name, token)

    final_request = build_authenticated_request(
        api_url, "application/vnd.github+json", token
    )
    with opener.open(final_request, timeout=30) as response:
        require(response.status == 200, f"Draft Release 二次 API HTTP {response.status}")
        final_release = json.loads(response.read().decode("utf-8"))
    validate_draft_release_metadata(
        final_release,
        repository,
        tag,
        candidate_id,
        release_id,
        target_branch,
        expected_commit,
        resolve_target(final_release),
    )
    require(
        stable_release_snapshot(final_release) == stable_release_snapshot(release),
        "Draft Release 元数据或资产库存在下载期间发生变化",
    )
    release = final_release

    actual_names = {path.name for path in destination.iterdir() if path.is_file()}
    require(
        actual_names == expected_asset_names(tag),
        f"下载目录资产不精确: {sorted(actual_names)}",
    )
    with metadata_output.open("x", encoding="utf-8") as output:
        output.write(json.dumps(release, ensure_ascii=False, indent=2) + "\n")
    print(f"认证下载并验证 draft candidate {tag} / Release ID {release_id} 的 4 个资产及 API digest")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--release-id", required=True, type=int)
    parser.add_argument("--target-branch", required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--metadata-output", type=Path, required=True)
    args = parser.parse_args()
    try:
        download_release(
            args.repository,
            args.tag,
            args.candidate_id,
            args.release_id,
            args.target_branch,
            args.expected_commit,
            args.destination,
            args.metadata_output,
        )
    except (OSError, ValueError, json.JSONDecodeError, VerificationError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
