#!/usr/bin/env python3
"""Canary 与正式消费共用的 Pod 根和 Objective-C 公开方法校验。"""

from __future__ import annotations

import argparse
import re
import tempfile
from pathlib import Path
from typing import Iterable


class ControlPlaneCheckError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ControlPlaneCheckError(message)


def selector_pattern(selector: str) -> re.Pattern[str]:
    require(re.fullmatch(r"[A-Za-z_]\w*(?::[A-Za-z_]\w*)*: ?", selector + " ") is not None, f"Objective-C selector 非法: {selector!r}")
    if ":" not in selector:
        return re.compile(rf"(?m)^[ \t]*[-+][ \t]*\([^\r\n)]*\)[ \t]*{re.escape(selector)}[ \t]*;[ \t]*$")
    require(selector.endswith(":"), f"带参数 selector 必须以冒号结束: {selector}")
    parts = selector[:-1].split(":")
    arguments = []
    for index, part in enumerate(parts):
        arguments.append(rf"{re.escape(part)}[ \t]*:[ \t]*\([^\r\n)]*\)[ \t]*[A-Za-z_]\w*")
        if index + 1 < len(parts):
            arguments.append(r"[ \t\r\n]+")
    return re.compile(r"(?m)^[ \t]*[-+][ \t]*\([^\r\n)]*\)[ \t]*" + "".join(arguments) + r"[ \t]*;[ \t]*$")


def resolve_pod_root(value: str | Path) -> Path:
    raw = Path(value)
    require(str(raw) not in {"", "."}, "POD_ROOT 不能为空")
    try:
        resolved = raw.resolve(strict=True)
    except OSError as exc:
        raise ControlPlaneCheckError(f"POD_ROOT 不存在: {raw}") from exc
    require(resolved.is_dir(), f"POD_ROOT 不是目录: {resolved}")
    return resolved


def validate_public_header_selectors(pod_root: str | Path, header_globs: Iterable[str], selectors: Iterable[str]) -> list[Path]:
    root = resolve_pod_root(pod_root)
    patterns = list(header_globs)
    required_selectors = list(selectors)
    require(patterns, "至少需要一个公开头 glob")
    require(required_selectors, "至少需要一个 Objective-C selector")
    headers: list[Path] = []
    for pattern in patterns:
        relative = Path(pattern)
        require(not relative.is_absolute() and ".." not in relative.parts, f"公开头 glob 必须位于 POD_ROOT 内: {pattern}")
        matched = sorted(path for path in root.glob(pattern) if path.is_file())
        require(matched, f"POD_ROOT 下未匹配公开头: {pattern}")
        headers.extend(matched)
    unique_headers = sorted(set(headers))
    for header in unique_headers:
        source = header.read_text(encoding="utf-8")
        for selector in required_selectors:
            require(selector_pattern(selector).search(source) is not None, f"{header} 缺少 Objective-C selector: {selector}")
    return unique_headers


def fixture_declaration(selector: str) -> str:
    selector_pattern(selector)
    if ":" not in selector:
        return f"- (void){selector};\n"
    parts = selector[:-1].split(":")
    lines = [f"- (void){parts[0]}:(id)value0"]
    for index, part in enumerate(parts[1:], start=1):
        lines.append(f" {part}:(NSError *)value{index}")
    lines[-1] += ";"
    return "\n".join(lines) + "\n"


def run_fixture(module_name: str, header_name: str, selector: str) -> None:
    require(re.fullmatch(r"[A-Za-z_]\w*", module_name) is not None, "fixture module name 非法")
    require(Path(header_name).name == header_name and header_name.endswith(".h"), "fixture header name 非法")
    with tempfile.TemporaryDirectory(prefix="control-plane-canary-") as directory:
        root = Path(directory)
        pod_root = root / "Pods/Local Pod"
        actual_headers = pod_root / "Actual Headers"
        actual_headers.mkdir(parents=True)
        public_headers = pod_root / "Headers/Public" / module_name
        public_headers.parent.mkdir(parents=True)
        public_headers.symlink_to(actual_headers, target_is_directory=True)
        (actual_headers / header_name).write_text(fixture_declaration(selector), encoding="utf-8")
        validated = validate_public_header_selectors(pod_root, [f"Headers/Public/{module_name}/{header_name}"], [selector])
        require(len(validated) == 1, "Canary 公开头夹具匹配数量异常")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate")
    validate.add_argument("--pod-root", required=True)
    validate.add_argument("--header-glob", action="append", required=True)
    validate.add_argument("--selector", action="append", required=True)
    fixture = subparsers.add_parser("fixture")
    fixture.add_argument("--module-name", required=True)
    fixture.add_argument("--header-name", required=True)
    fixture.add_argument("--selector", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            headers = validate_public_header_selectors(args.pod_root, args.header_glob, args.selector)
            print(f"生产公开头校验通过: {len(headers)} 个头")
        else:
            run_fixture(args.module_name, args.header_name, args.selector)
            print("control-plane canary 生产校验函数夹具通过")
        return 0
    except (OSError, UnicodeError, ControlPlaneCheckError) as exc:
        print(f"控制面生产校验失败: {exc}", file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
