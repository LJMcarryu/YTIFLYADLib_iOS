#!/usr/bin/env python3
"""校验公开 SDK 仓库的统一结构契约。"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


class ContractError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"无法读取 JSON: {path}: {exc}") from exc


def check(root: Path) -> None:
    contract_path = root / "repository-contract.json"
    contract = read_json(contract_path)
    require(contract.get("schemaVersion") == 1, "repository-contract schemaVersion 必须为 1")
    repo = contract.get("repository")
    channel = contract.get("channel")
    require(isinstance(repo, str) and re.fullmatch(r"[^/]+/[^/]+", repo), "repository 必须为 owner/name")
    require(isinstance(channel, str) and channel, "channel 不能为空")

    required_root = contract.get("requiredRootFiles")
    require(isinstance(required_root, list) and required_root, "requiredRootFiles 不能为空")
    for relative in required_root:
        path = root / relative
        require(path.is_file(), f"缺少根目录契约文件: {relative}")

    package = contract.get("package")
    require(isinstance(package, dict), "package 必须为对象")
    for key in ("manifest", "podspec"):
        relative = package.get(key)
        require(isinstance(relative, str) and (root / relative).is_file(), f"缺少 package.{key}: {relative}")

    demo = contract.get("demo")
    require(isinstance(demo, dict), "demo 必须为对象")
    for key in ("root", "readme", "podfile", "project", "scheme"):
        value = demo.get(key)
        require(isinstance(value, str) and value, f"demo.{key} 不能为空")
    for key in ("root", "readme", "podfile", "project"):
        require((root / demo[key]).exists(), f"缺少 Demo {key}: {demo[key]}")
    demo_readme = (root / demo["readme"]).read_text(encoding="utf-8")
    require("## " in demo_readme, "Demo README 缺少章节")
    project_text = (root / demo["project"] / "project.pbxproj").read_text(encoding="utf-8", errors="replace")
    require(demo["scheme"] in project_text, f"Demo 工程未出现 scheme/target 名称: {demo['scheme']}")

    docs = contract.get("docs")
    require(isinstance(docs, dict), "docs 必须为对象")
    for key in ("index", "guideRoot", "releaseHistory"):
        value = docs.get(key)
        require(isinstance(value, str) and (root / value).exists(), f"缺少 docs.{key}: {value}")
    guide_names = docs.get("guides")
    require(isinstance(guide_names, list) and guide_names, "docs.guides 不能为空")
    index_text = (root / docs["index"]).read_text(encoding="utf-8")
    for name in guide_names:
        require((root / docs["guideRoot"] / name).is_file(), f"缺少接入指南: {name}")
        require(name in index_text, f"接入指南索引未链接: {name}")

    github = contract.get("github")
    require(isinstance(github, dict), "github 必须为对象")
    for key in ("workflow", "pullRequestTemplate", "issueConfig", "bugTemplate"):
        value = github.get(key)
        require(isinstance(value, str) and (root / value).is_file(), f"缺少 GitHub 配置: {value}")

    state = read_json(root / "release-state.json")
    require(state.get("repository") == repo, "release-state.repository 与契约不一致")
    require(state.get("channel") == channel, "release-state.channel 与契约不一致")
    version = state.get("version")
    require(isinstance(version, str) and re.fullmatch(r"\d+\.\d+\.\d+", version), "release-state.version 非法")
    readme = (root / "README.md").read_text(encoding="utf-8")
    marker = re.search(r"ifly-release-status:\s*(\{[^\n]+\})", readme)
    require(marker is not None, "README 缺少 ifly-release-status 标记")
    try:
        marker_data = json.loads(marker.group(1))
    except json.JSONDecodeError as exc:
        raise ContractError(f"README 发布标记不是合法 JSON: {exc}") from exc
    require(marker_data.get("version") == version, "README 发布标记版本与 release-state 不一致")
    if state.get("distributionBackend") == "tos":
        require(state.get("schemaVersion") == 4, "TOS 状态 schema 非法")
        expected_url = f"https://download-adsdk.voiceads.cn/ios_sdk/{version}/{channel}/release-record.json"
        require(marker_data.get("distribution") == "tos", "TOS 发布标记来源不一致")
    else:
        expected_url = f"https://github.com/{repo}/releases/tag/{version}"
    require(marker_data.get("releaseUrl") == expected_url, "README Release URL 与契约不一致")

    if (root / ".git").exists():
        try:
            output = subprocess.run(
                ["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True, text=False
            ).stdout.decode("utf-8", "replace")
        except (OSError, subprocess.CalledProcessError):
            output = ""
        tracked = [item for item in output.split("\0") if item]
        require(not any(Path(item).name == ".DS_Store" for item in tracked), "禁止跟踪 .DS_Store")
        require(not any(item.startswith("Pods/") or "/Pods/" in item for item in tracked), "禁止跟踪 Pods 目录")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    try:
        check(root)
    except ContractError as exc:
        print(f"公开仓契约校验失败: {exc}", file=sys.stderr)
        return 1
    print(f"公开仓契约校验通过: {root.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
