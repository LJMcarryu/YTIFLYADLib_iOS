#!/usr/bin/env python3
"""公开仓 TOS 元数据合同；不依赖私有源码或上传凭据。"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

BASE = "https://download-adsdk.voiceads.cn/ios_sdk"
CHANNELS = {
    "general": ("IFLYADLib.podspec", "IFLYADLib-modelA-{version}.zip",
        {"IFLYAd" + name: "IFLYAd" + name + ".xcframework.zip"
         for name in ("Core", "VideoUI", "Banner", "Splash", "Interstitial", "NativeFeed", "Reward")}),
    "ys": ("YSIFLYADLib.podspec", "YSIFLYADLib-{version}.zip", {"YSIFLYADLib": "YSIFLYADLib.xcframework.zip"}),
    "yt": ("YTIFLYADLib.podspec", "YTIFLYADLib-{version}.zip", {"YTIFLYADLib": "YTIFLYADLib.xcframework.zip"}),
    "youku": ("YKIFLYADLib.podspec", "YKIFLYADLib-{version}.zip", {"IFLYADLib": "IFLYADLib.xcframework.zip"}),
    "ys-splash": ("YSIFLYADLibSplash.podspec", "YSIFLYADLib-SplashOnly-{version}.zip",
                  {"YSIFLYADLib": "YSIFLYADLib-SplashOnly.xcframework.zip"}),
}


def expected_asset_names(channel, version):
    _, combined, targets = CHANNELS[channel]
    names = set(targets.values()) | {combined.format(version=version), "checksums.txt"}
    if channel == "general":
        names.add("binary-targets.remote.swift")
    if channel in {"yt", "youku"}:
        names.add("delivery-manifest.json")
    return names


def inventory_digest(assets):
    fields = [{key: asset[key] for key in ("name", "size", "sha256", "url")} for asset in assets]
    return hashlib.sha256(json.dumps(sorted(fields, key=lambda a: a["name"]), sort_keys=True,
        ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def verify_inventory(assets, channel, version):
    if not isinstance(assets, list) or not all(isinstance(a, dict) for a in assets):
        raise ValueError("TOS 库存必须为对象列表")
    names = [a.get("name") for a in assets]
    if not all(isinstance(name, str) for name in names) or len(set(names)) != len(names):
        raise ValueError("TOS 库存名称非法或重复")
    if set(names) != expected_asset_names(channel, version):
        raise ValueError("TOS 库存不是渠道批准的精确资产集合")
    for asset in assets:
        if (not isinstance(asset.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", asset["sha256"]) or
            type(asset.get("size")) is not int or asset["size"] < 0 or
            asset.get("url") != f"{BASE}/{version}/{channel}/{asset['name']}"):
            raise ValueError("TOS 库存字段非法")
    return {a["name"]: a for a in assets}


def read(root, relative):
    path = root / relative
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("合同路径越界")
    current = path
    while current != root.parent:
        if current.is_symlink():
            raise ValueError("公开元数据不得使用符号链接")
        current = current.parent
    if not path.is_file() or path.stat().st_nlink != 1:
        raise ValueError("公开元数据须为单链接普通文件")
    return path.read_text()


def verify(root: Path, version: str | None = None, *, metadata_only=False, allow_pending=False):
    root = root.absolute()
    contract = json.loads(read(root, "repository-contract.json"))
    state = json.loads(read(root, "release-state.json"))
    channel = contract["channel"]
    if channel not in CHANNELS or state.get("channel") != channel or state.get("repository") != contract["repository"]:
        raise ValueError("公开仓/渠道身份不一致")
    version = version or state["version"]
    if re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version) is None:
        raise ValueError("版本非法")
    for path in contract["requiredRootFiles"]:
        read(root, path)
    base = f"{BASE}/{version}/{channel}"
    expected_marker = {"version": version, "status": "FORMAL", "distribution": "tos",
                       "releaseUrl": base + "/release-record.json"}
    for name in ("README.md", "CHANGELOG.md", "RELEASING.md"):
        text = read(root, name)
        markers = re.findall(r"<!--\s*ifly-release-status:\s*(\{.*?\})\s*-->", text, re.S)
        if len(markers) != 1 or json.loads(markers[0]) != expected_marker:
            raise ValueError(f"{name} TOS 发布标记不一致")
    if allow_pending:
        return {"status": "success", "channel": channel, "version": version, "distributionBackend": "tos", "metadata": "pending"}
    podspec_name, combined, targets = CHANNELS[channel]
    package = read(root, "Package.swift")
    # 注释可出现在字段间；剥离整行注释再解析。
    package = re.sub(r"^\s*//[^\n]*", "", package, flags=re.M)
    blocks = re.findall(r'\.binaryTarget\(\s*name:\s*"([^"\n]+)"\s*,\s*url:\s*"([^"\n]+)"\s*,\s*checksum:\s*"([0-9a-f]{64})"\s*,?\s*\)', package, re.S)
    if len(blocks) != len(targets) or {b[0] for b in blocks} != set(targets):
        raise ValueError("SwiftPM binaryTarget 集合或 checksum 非法")
    for name, url, checksum in blocks:
        if url != base + "/" + targets[name]:
            raise ValueError("SwiftPM TOS URL 身份不符")
    pod = read(root, podspec_name)
    versions = re.findall(r"^\s*s\.version\s*=\s*['\"]([^'\"]+)['\"]", pod, re.M)
    sources = re.findall(r"^\s*s\.source\s*=\s*\{\s*:http\s*=>\s*['\"]([^'\"]+)['\"]\s*\}", pod, re.M)
    if versions != [version] or sources != [base + "/" + combined.format(version=version)]:
        raise ValueError("Podspec 版本或 TOS URL 不一致")
    if not metadata_only:
        if state.get("schemaVersion") != 4 or state.get("distributionBackend") != "tos" or state.get("phase") not in {"FROZEN", "CLOSED"} or state["version"] != version:
            raise ValueError("TOS 状态 schema/phase/version 非法")
        assets = state["assets"]
        by_name = verify_inventory(assets, channel, version)
        # uploadInventorySha256 绑定整个私有冻结计划；单仓只可复算自身 channelInventorySha256。
        if (not isinstance(state.get("uploadInventorySha256"), str) or
                not re.fullmatch(r"[0-9a-f]{64}", state["uploadInventorySha256"]) or
                state.get("channelInventorySha256") != inventory_digest(assets)):
            raise ValueError("TOS 库存摘要非法或与渠道库存不符")
        for name, url, checksum in blocks:
            if by_name[targets[name]]["sha256"] != checksum:
                raise ValueError("SwiftPM 摘要与冻结库存不同")
        if combined.format(version=version) not in by_name:
            raise ValueError("缺少 CocoaPods 整包库存")
    return {"status": "success", "channel": channel, "version": version, "distributionBackend": "tos",
            "binaryTargets": sorted(targets), "podspec": podspec_name}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--version")
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.root, args.version, metadata_only=args.metadata_only), ensure_ascii=False))
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, f"TOS 元数据校验失败：{exc}\n")
