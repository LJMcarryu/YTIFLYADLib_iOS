#!/usr/bin/env python3
"""校验最终消费产物的 AdSupport 与 ATT 链接方式。"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def framework_load_commands(binary: Path, framework: str) -> list[str]:
    output = subprocess.check_output(["xcrun", "otool", "-l", str(binary)], text=True)
    current_command = ""
    commands = []
    framework_marker = f"/{framework}.framework/"
    for raw_line in output.splitlines():
        fields = raw_line.strip().split()
        if len(fields) >= 2 and fields[0] == "cmd":
            current_command = fields[1]
        elif (
            len(fields) >= 2
            and fields[0] == "name"
            and framework_marker in fields[1]
        ):
            commands.append(current_command)
    return commands


def verify(binary: Path, description: str) -> None:
    if not binary.is_file():
        raise RuntimeError(f"{description} 最终链接产物不存在: {binary}")
    dependencies = subprocess.check_output(
        ["xcrun", "otool", "-L", str(binary)], text=True
    )
    if "/AdSupport.framework/AdSupport" not in dependencies:
        raise RuntimeError(f"{description} 缺少 AdSupport 依赖")
    att_commands = framework_load_commands(binary, "AppTrackingTransparency")
    if not att_commands:
        raise RuntimeError(f"{description} 缺少 AppTrackingTransparency 依赖")
    if set(att_commands) != {"LC_LOAD_WEAK_DYLIB"}:
        raise RuntimeError(
            f"{description} 的 AppTrackingTransparency 未保持弱链接: {att_commands}"
        )
    print(f"{description}: AdSupport 已链接，AppTrackingTransparency=LC_LOAD_WEAK_DYLIB")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--description", required=True)
    args = parser.parse_args()
    try:
        verify(args.binary, args.description)
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
