#!/usr/bin/env python3
"""计算或核对 Release 精确四资产的稳定内容指纹。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

from download_release_anonymously import VerificationError, expected_asset_names, require


def asset_identity(directory: Path, tag: str) -> str:
    require(directory.is_dir(), f"Release 资产目录不存在: {directory}")
    expected = expected_asset_names(tag)
    actual = {path.name for path in directory.iterdir() if path.is_file()}
    require(actual == expected, f"Release 资产不精确: {sorted(actual)}")
    records = []
    for name in sorted(expected):
        path = directory / name
        require(path.is_file() and not path.is_symlink(), f"Release 资产非法: {path}")
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        records.append(
            {"name": name, "sha256": digest.hexdigest(), "size": path.stat().st_size}
        )
    canonical = json.dumps(
        records, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--expected")
    parser.add_argument("--github-output", action="store_true")
    args = parser.parse_args()
    try:
        require(
            re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", args.tag) is not None,
            f"非法 Release tag: {args.tag!r}",
        )
        identity = asset_identity(args.directory, args.tag)
        if args.expected is not None:
            require(
                re.fullmatch(r"[0-9a-f]{64}", args.expected) is not None,
                f"非法期望资产指纹: {args.expected!r}",
            )
            require(identity == args.expected, "本次下载资产与公共前置门禁不是同一内容")
        if args.github_output:
            output_path = os.environ.get("GITHUB_OUTPUT", "")
            require(bool(output_path), "--github-output 要求 GITHUB_OUTPUT")
            with Path(output_path).open("a", encoding="utf-8") as output:
                output.write(f"identity={identity}\n")
        print(f"Release 四资产内容指纹: {identity}")
    except (OSError, ValueError, VerificationError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
