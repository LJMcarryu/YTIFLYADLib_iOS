#!/usr/bin/env python3
"""Download and verify the exact public Release asset set without credentials."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import socket
import ssl
import sys
import time
from pathlib import Path
from typing import Any, Dict
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


TOKEN_ENVIRONMENT_VARIABLES = (
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GITHUB_AUTH_TOKEN",
    "IFLY_PRIVATE_SOURCE_TOKEN",
)
USER_AGENT = "YTIFLYADLib-anonymous-release-verifier"
DOWNLOAD_MAX_ATTEMPTS = 5


class VerificationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def build_anonymous_request(url: str, accept: str) -> Request:
    request = Request(
        url,
        headers={
            "Accept": accept,
            "User-Agent": USER_AGENT,
        },
    )
    header_names = {name.lower() for name, _ in request.header_items()}
    require("authorization" not in header_names, "匿名请求不得携带 Authorization")
    require(
        header_names == {"accept", "user-agent"},
        f"匿名请求出现非预期请求头: {sorted(header_names)}",
    )
    return request


def expected_asset_names(tag: str) -> set[str]:
    return {
        "YTIFLYADLib.xcframework.zip",
        f"YTIFLYADLib-{tag}.zip",
        "checksums.txt",
        "delivery-manifest.json",
    }


def validate_asset_inventory(
    release: Dict[str, Any], tag: str
) -> Dict[str, Dict[str, Any]]:
    assets = release.get("assets")
    require(isinstance(assets, list), "Release assets 不是数组")
    expected = expected_asset_names(tag)
    require(
        all(
            isinstance(asset, dict) and isinstance(asset.get("name"), str)
            for asset in assets
        ),
        "Release asset 元数据格式错误",
    )
    names = [asset["name"] for asset in assets]
    require(len(assets) == len(expected), f"Release 必须精确包含 4 个资产: {names}")
    require(len(set(names)) == len(names), f"Release 资产名重复: {names}")
    require(set(names) == expected, f"实际资产 {sorted(names)}，期望 {sorted(expected)}")

    by_name: Dict[str, Dict[str, Any]] = {}
    for asset in assets:
        name = asset["name"]
        digest = asset.get("digest")
        require(
            isinstance(digest, str)
            and re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is not None,
            f"{name} 缺少合法 GitHub API sha256 digest: {digest!r}",
        )
        require(
            isinstance(asset.get("size"), int) and asset["size"] >= 0,
            f"{name} 缺少合法 size",
        )
        by_name[name] = asset
    return by_name


def validate_release_metadata(
    release: Dict[str, Any], repository: str, tag: str
) -> Dict[str, Dict[str, Any]]:
    require(release.get("tag_name") == tag, "Release tag 与目标 tag 不一致")
    require(release.get("draft") is False, "Release 不得为 draft")
    require(release.get("prerelease") is False, "Release 不得为 prerelease")
    require(bool(release.get("published_at")), "Release 缺少 published_at")
    require(isinstance(release.get("body"), str), "Release body 缺失")
    expected_html_url = (
        f"https://github.com/{repository}/releases/tag/{quote(tag, safe='')}"
    )
    require(
        release.get("html_url") == expected_html_url,
        f"Release html_url 非预期: {release.get('html_url')!r}",
    )

    by_name = validate_asset_inventory(release, tag)
    for asset in by_name.values():
        name = asset["name"]
        expected_url = (
            f"https://github.com/{repository}/releases/download/"
            f"{quote(tag, safe='')}/{quote(name, safe='')}"
        )
        require(
            asset.get("browser_download_url") == expected_url,
            f"{name} browser_download_url 非预期: {asset.get('browser_download_url')!r}",
        )
    return by_name


def _retryable_download_error(error: BaseException) -> bool:
    if isinstance(error, HTTPError):
        return error.code in {408, 429} or 500 <= error.code <= 599
    if isinstance(error, URLError):
        return isinstance(error.reason, (TimeoutError, socket.timeout, ssl.SSLError, ConnectionError))
    return isinstance(error, (TimeoutError, socket.timeout, ssl.SSLError, ConnectionError))


def _verified_cache(asset: Dict[str, Any], destination: Path) -> str | None:
    if not destination.exists() and not destination.is_symlink():
        return None
    require(destination.is_file() and not destination.is_symlink(),
            f"{asset['name']} 缓存目标必须是普通文件")
    if destination.stat().st_size != asset["size"]:
        destination.unlink()
        return None
    actual = hashlib.sha256(destination.read_bytes()).hexdigest()
    if not hmac.compare_digest(actual, asset["digest"].removeprefix("sha256:")):
        destination.unlink()
        return None
    return actual


def download_with_retry(asset: Dict[str, Any], destination: Path, open_response,
                        validate_response, *, max_attempts: int = DOWNLOAD_MAX_ATTEMPTS,
                        sleeper=time.sleep) -> str:
    cached = _verified_cache(asset, destination)
    if cached is not None:
        return cached
    temporary = destination.with_name(destination.name + ".part")
    require(not temporary.is_symlink(), f"临时下载目标不得为符号链接: {temporary}")
    temporary.unlink(missing_ok=True)
    for attempt in range(1, max_attempts + 1):
        try:
            digest = hashlib.sha256()
            downloaded_size = 0
            with open_response() as response, temporary.open("xb") as output:
                validate_response(response)
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
                    digest.update(chunk)
                    downloaded_size += len(chunk)
            require(downloaded_size == asset["size"],
                    f"{asset['name']} 下载大小与 API size 不一致")
            actual = digest.hexdigest()
            require(hmac.compare_digest(actual, asset["digest"].removeprefix("sha256:")),
                    f"{asset['name']} SHA-256 与 API digest 不一致")
            temporary.replace(destination)
            return actual
        except Exception as error:
            temporary.unlink(missing_ok=True)
            if (isinstance(error, VerificationError) or not _retryable_download_error(error)
                    or attempt == max_attempts):
                raise
            sleeper(min(2 ** (attempt - 1), 8))
    raise AssertionError("unreachable")


def download_and_hash(asset: Dict[str, Any], destination: Path) -> str:
    def open_response():
        request = build_anonymous_request(
            asset["browser_download_url"], "application/octet-stream"
        )
        return urlopen(request, timeout=120)

    def validate_response(response) -> None:
        final_url = urlsplit(response.geturl())
        final_host = (final_url.hostname or "").lower()
        require(final_url.scheme == "https", f"资产重定向不是 HTTPS: {response.geturl()}")
        require(final_host == "github.com" or final_host.endswith(".githubusercontent.com"),
                f"资产重定向到非 GitHub 主机: {response.geturl()}")

    return download_with_retry(asset, destination, open_response, validate_response)


def download_release(
    repository: str, tag: str, destination: Path, metadata_output: Path
) -> None:
    leaked_tokens = [
        name for name in TOKEN_ENVIRONMENT_VARIABLES if os.environ.get(name)
    ]
    require(
        not leaked_tokens,
        f"匿名 Release 下载环境不得包含凭据变量: {leaked_tokens}",
    )
    require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) is not None,
            f"非法 GitHub repository: {repository!r}")
    require(re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", tag) is not None,
            f"非法 Release tag: {tag!r}")

    api_url = (
        f"https://api.github.com/repos/{repository}/releases/tags/"
        f"{quote(tag, safe='')}"
    )
    request = build_anonymous_request(api_url, "application/vnd.github+json")
    with urlopen(request, timeout=30) as response:
        require(response.status == 200, f"Release API HTTP {response.status}")
        release = json.loads(response.read().decode("utf-8"))
    assets = validate_release_metadata(release, repository, tag)

    destination.mkdir(parents=True, exist_ok=True)
    for path in destination.iterdir():
        require(path.is_file() and not path.is_symlink(),
                f"下载目录只能包含普通文件缓存: {path}")
        if path.name.endswith(".part"):
            path.unlink()
    for name in sorted(assets):
        actual = download_and_hash(assets[name], destination / name)

    actual_names = {path.name for path in destination.iterdir() if path.is_file()}
    require(
        actual_names == expected_asset_names(tag),
        f"下载目录资产不精确: {sorted(actual_names)}",
    )
    metadata_output.write_text(
        json.dumps(release, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"匿名下载并验证 Release {tag} 的 4 个资产及 API digest")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--metadata-output", type=Path, required=True)
    args = parser.parse_args()
    try:
        download_release(
            args.repository, args.tag, args.destination, args.metadata_output
        )
    except (OSError, ValueError, json.JSONDecodeError, VerificationError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
