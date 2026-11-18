"""发布身份使用的严格 SemVer（暂不支持 build metadata）。"""
from __future__ import annotations

import re


_NUMBER = r"(?:0|[1-9][0-9]*)"
CORE_VERSION_PATTERN = rf"{_NUMBER}\.{_NUMBER}\.{_NUMBER}"
_PRERELEASE_IDENTIFIER = rf"(?:{_NUMBER}|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)"
VERSION_PATTERN = rf"{CORE_VERSION_PATTERN}(?:-{_PRERELEASE_IDENTIFIER}(?:\.{_PRERELEASE_IDENTIFIER})*)?"
VERSION_RE = re.compile(VERSION_PATTERN)


def validate_version(value: str) -> str:
    if not isinstance(value, str) or VERSION_RE.fullmatch(value) is None:
        raise ValueError(f"版本必须是严格的 x.y.z 或 x.y.z-prerelease，且不含 build metadata：{value!r}")
    return value


def version_key(value: str) -> tuple:
    """返回 SemVer 优先级；数字预发布标识低于文本标识，正式版最高。"""
    core, separator, prerelease = validate_version(value).partition("-")
    numbers = tuple(int(part) for part in core.split("."))
    identifiers = tuple((0, int(part)) if part.isdigit() else (1, part)
                        for part in prerelease.split(".")) if separator else ()
    return (*numbers, 0 if separator else 1, identifiers)


def core_version(value: str) -> str:
    return validate_version(value).partition("-")[0]


def is_prerelease(value: str) -> bool:
    return "-" in validate_version(value)


def main(arguments=None) -> int:
    import argparse
    import sys

    arguments = list(sys.argv[1:] if arguments is None else arguments)
    # 同时服务 shell 选项入口和便于交互的子命令入口。
    if arguments and arguments[0] in {"--validate", "--core", "--pattern"}:
        arguments[0] = arguments[0][2:]
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "core"):
        commands.add_parser(command).add_argument("version")
    commands.add_parser("pattern").add_argument("--posix", action="store_true")
    args = parser.parse_args(arguments)
    try:
        if args.command == "pattern":
            print(VERSION_PATTERN.replace("(?:", "(") if args.posix else VERSION_PATTERN)
        else:
            print(core_version(args.version) if args.command == "core" else validate_version(args.version))
        return 0
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
