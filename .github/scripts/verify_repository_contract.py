#!/usr/bin/env python3
"""分别校验优土渠道机器分发契约与阻断式 Markdown 发布契约。"""

from __future__ import annotations

import argparse
import json
import plistlib
import re
import shlex
import sys
from pathlib import Path


VERSION = "6.4.0"
PREVIOUS_RELEASE_VERSION = "6.3.5"
PREVIOUS_RELEASE_CHECKSUM = "d5a4e2ecb1fc8495df33ed8ad37b765ca66af4cfd689eec0caf4c5424e8baf83"
REPOSITORY = "LJMcarryu/YTIFLYADLib_iOS"
PENDING = "__YTIFLYADLIB_6_4_0_SWIFTPM_CHECKSUM_PENDING__"
HISTORICAL = {
    "7adf06f9c3f1d6fe915679322ccb941ba9122edf496c9815db12db3f4e459855",
    "144d0c649c1a83d8572e4a3a1295ec0430a65b788554fe62cccf6c12631a0aa5",
    "a3c31e6fc523aa2bb1af71849ba1dc893d94e69ae68246eab4d9d20cbb07232f",
    "303e185b70d5396f9438c8e6a96239fbb1e1ef93166f8487ac4e6ebfb58d3b09",
    "5f3df44ec856f9e38c584311512ede168cf2c0ec45e3d09378052e1b0196e263",
}
RELEASE_STATUS_RE = re.compile(
    r"<!--\s*ifly-release-status:\s*(\{[^\r\n]*\})\s*-->"
)


class ContractError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def read(root: Path, relative: str) -> str:
    return (root / relative).read_text(encoding="utf-8")


def verify_release_status(
    label: str, document: str, allowed_versions: set[str]
) -> str:
    markers = RELEASE_STATUS_RE.findall(document)
    require(len(markers) == 1, f"{label} 发布状态标记数量错误: {len(markers)}")
    try:
        marker = json.loads(markers[0])
    except json.JSONDecodeError as error:
        raise ContractError(f"{label} 发布状态标记不是合法 JSON") from error
    version = marker.get("version")
    require(
        isinstance(version, str) and version in allowed_versions,
        f"{label} 发布状态版本不在允许集合内: {version}",
    )
    expected = {
        "schemaVersion": 1,
        "version": version,
        "releaseState": "FORMAL",
        "distribution": "github-release",
        "releaseUrl": f"https://github.com/{REPOSITORY}/releases/tag/{version}",
    }
    require(marker == expected, f"{label} 发布状态标记漂移: {marker}")
    return version


def state(root: Path) -> dict[str, object]:
    value = json.loads(read(root, "release-state.json"))
    require(value.get("channel") == "yt", "release-state 渠道不匹配")
    return value


def validate_state_version(value: dict[str, object], release_kind: str) -> None:
    version = value.get("version")
    phase = value.get("phase")
    if release_kind in {"draft", "formal"}:
        require(
            version == VERSION and phase == "FROZEN",
            "candidate/tag/Release 必须使用当前分发版本的 FROZEN 状态",
        )
        return
    require(release_kind == "none", "非法验证类型")
    require(
        (version in {PREVIOUS_RELEASE_VERSION, VERSION} and phase == "CLOSED")
        or (version == VERSION and phase == "FROZEN"),
        "release-state 版本不匹配：普通 main 只允许保留上一版/当前版 CLOSED，"
        "或当前版本 FROZEN；candidate/tag/Release 必须使用当前版本 FROZEN",
    )


def allowed_distribution_versions(
    value: dict[str, object], release_kind: str
) -> set[str]:
    validate_state_version(value, release_kind)
    if (
        release_kind == "none"
        and value.get("version") == PREVIOUS_RELEASE_VERSION
        and value.get("phase") == "CLOSED"
    ):
        return {PREVIOUS_RELEASE_VERSION, VERSION}
    return {VERSION}


def verify_checksum(checksum: str, distribution_version: str, preparing: bool) -> None:
    if preparing:
        require(distribution_version == VERSION, "PREPARING 只允许当前分发版本")
        require(checksum == PENDING, "PREPARING 必须使用精确 PENDING checksum")
        return
    require(
        re.fullmatch(r"[0-9a-f]{64}", checksum) is not None,
        "FORMAL checksum 非 64 位小写 SHA-256",
    )
    if distribution_version == PREVIOUS_RELEASE_VERSION:
        require(
            checksum == PREVIOUS_RELEASE_CHECKSUM,
            "上一正式版本 checksum 与冻结值不一致",
        )
        return
    require(distribution_version == VERSION, "非法分发版本")
    require(
        checksum != "0" * 64
        and checksum != PREVIOUS_RELEASE_CHECKSUM
        and checksum not in HISTORICAL,
        "FORMAL checksum 为零或沿用历史值",
    )


def one(pattern: str, text: str, label: str) -> str:
    values = re.findall(pattern, text, re.M)
    require(len(values) == 1, f"{label} 声明数量错误: {values}")
    return values[0]


def verify_machine(
    root: Path, release_kind: str, podspec_json_path: Path
) -> None:
    require(release_kind in {"none", "draft", "formal"}, "非法验证类型")
    machine = state(root)
    allowed_versions = allowed_distribution_versions(machine, release_kind)
    package = read(root, "Package.swift")
    podspec = read(root, "YTIFLYADLib.podspec")
    podfile = read(root, "YTIFLYADLibSimple/Podfile")
    podspec_json = json.loads(podspec_json_path.read_text(encoding="utf-8"))
    version = one(r"s\.version\s*=\s*['\"]([^'\"]+)", podspec, "podspec version")
    require(version in allowed_versions, f"podspec 版本错误: {version}")
    require(podspec_json.get("version") == version, "podspec JSON 版本漂移")
    package_url = one(r'url:\s*"([^"]*YTIFLYADLib\.xcframework\.zip)"',
                      package, "SwiftPM URL")
    pod_url = one(r"s\.source\s*=\s*\{\s*:http\s*=>\s*['\"]([^'\"]+)",
                  podspec, "podspec URL")
    require(
        package_url == f"https://github.com/{REPOSITORY}/releases/download/"
        f"{version}/YTIFLYADLib.xcframework.zip",
        "SwiftPM URL 版本或仓库错误",
    )
    require(
        pod_url == f"https://github.com/{REPOSITORY}/releases/download/"
        f"{version}/YTIFLYADLib-{version}.zip",
        "podspec URL 版本或仓库错误",
    )
    demo_url = one(r":podspec\s*=>\s*'([^']+)'", podfile, "Demo podspec URL")
    require(
        demo_url == f"https://raw.githubusercontent.com/{REPOSITORY}/"
        f"{version}/YTIFLYADLib.podspec",
        "Demo podspec URL 版本错误",
    )
    checksum = one(r'checksum:\s*"([^"]+)"', package, "SwiftPM checksum")
    preparing = machine.get("phase") == "PREPARING"
    verify_checksum(checksum, version, preparing)
    if release_kind in {"draft", "formal"}:
        require(not preparing, f"{release_kind} 禁止 PREPARING")
    for marker in (
        'name: "YTIFLYADLib"',
        'targets: ["YTIFLYADLib", "YTIFLYADLibResources"]',
        '.copy("YTAdvSDK.bundle")',
    ):
        require(marker in package, f"Package.swift 缺少包契约: {marker}")
    frameworks = podspec_json.get("frameworks", [])
    weak_frameworks = podspec_json.get("weak_frameworks", [])
    if isinstance(frameworks, str):
        frameworks = [frameworks]
    if isinstance(weak_frameworks, str):
        weak_frameworks = [weak_frameworks]
    require("AdSupport" in frameworks, "podspec JSON 缺少 AdSupport 强链接声明")
    require(
        "AppTrackingTransparency" in weak_frameworks,
        "podspec JSON 缺少 AppTrackingTransparency 弱链接声明",
    )
    for key in ("pod_target_xcconfig", "user_target_xcconfig"):
        config = podspec_json.get(key, {})
        require(isinstance(config, dict), f"podspec JSON {key} 非对象")
        flags = config.get("OTHER_LDFLAGS", "")
        require(
            isinstance(flags, str) and "-ObjC" in shlex.split(flags),
            f"podspec JSON {key}.OTHER_LDFLAGS 缺少 -ObjC",
        )
    require((root / "spm/YTIFLYADLibResources/YTIFLYADLibResources.swift").is_file(),
            "缺少 SwiftPM 资源锚点")
    bundle = root / "spm/YTIFLYADLibResources/YTAdvSDK.bundle"
    privacy = bundle / "PrivacyInfo.xcprivacy"
    require(privacy.is_file(), "缺少 SwiftPM PrivacyInfo.xcprivacy")
    executable = [
        path for path in bundle.rglob("*")
        if path.is_file() and path.stat().st_mode & 0o111
    ]
    require(not executable, f"资源包含可执行位文件: {executable}")
    domains = plistlib.loads(privacy.read_bytes())["NSPrivacyTrackingDomains"]
    require("msdk.voiceads.cn" in domains, "隐私清单缺少 msdk.voiceads.cn")
    require("youku-sdk-grey.voiceads.cn" not in domains, "隐私清单残留灰度域名")


def verify_docs(root: Path, _release_kind: str) -> None:
    machine = state(root)
    allowed_versions = allowed_distribution_versions(machine, _release_kind)
    documents = {
        name: read(root, name)
        for name in ("README.md", "CHANGELOG.md", "RELEASING.md")
    }
    demo = read(root, "YTIFLYADLibSimple/README.md")
    if machine.get("phase") == "PREPARING":
        require("待发布" in documents["CHANGELOG.md"], "CHANGELOG 缺少待发布展示")
        require("PENDING" in documents["RELEASING.md"], "RELEASING 缺少 PENDING 展示")
        require("尚未发布" in demo, "Demo 缺少待发布展示")
    else:
        versions = {
            verify_release_status(label, document, allowed_versions)
            for label, document in documents.items()
        }
        require(len(versions) == 1, f"发布文档版本不一致: {sorted(versions)}")
        distribution_version = versions.pop()
        require(distribution_version in demo, "Demo 缺少当前分发版本展示")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--scope", choices=("machine", "docs"), required=True)
    parser.add_argument("--podspec-json", type=Path)
    parser.add_argument(
        "--release-kind", choices=("none", "draft", "formal"), default="none"
    )
    args = parser.parse_args()
    try:
        if args.scope == "machine":
            if args.podspec_json is None:
                parser.error("--scope machine 必须提供 --podspec-json")
            verify_machine(
                args.root.resolve(), args.release_kind, args.podspec_json.resolve()
            )
        else:
            verify_docs(args.root.resolve(), args.release_kind)
    except (ContractError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1
    print(f"OK {args.scope} contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
