#!/usr/bin/env python3
"""正式 Release 元数据来源与版本控制契约的 fail-closed 校验。"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import quote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from github_http_retry import call_with_retry


VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
RELEASE_ID = re.compile(r"^[1-9][0-9]*$")
PREPARATION_MODES = frozenset({"local", "repository"})
DRAFT_CONSUMPTION_MODES = frozenset({"candidate", "draft_candidate"})
FORMAL_CONSUMPTION_MODES = frozenset({"tag", "formal", "formal_release"})


class ReleaseControlError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReleaseControlError(message)


def validate_release_control(
    value: Any,
    *,
    repository: str,
    channel: str,
    release_phase: str,
    release_version: str,
    validation_mode: str,
) -> dict[str, Any]:
    require(isinstance(value, dict), "release-control 根必须是对象")
    expected = {
        "schemaVersion", "state", "channel", "repository",
        "closedVersion", "targetVersion",
    }
    require(set(value) == expected,
            f"release-control 字段漂移: {sorted(set(value) ^ expected)}")
    require(value["schemaVersion"] == 1, "仅支持 release-control schemaVersion=1")
    require(value["repository"] == repository, "release-control repository 漂移")
    require(value["channel"] == channel, "release-control channel 漂移")
    closed_version = value["closedVersion"]
    require(isinstance(closed_version, str)
            and VERSION.fullmatch(closed_version) is not None,
            "release-control closedVersion 格式非法")
    target = value["targetVersion"]
    require(isinstance(target, str) and VERSION.fullmatch(target) is not None,
            "release-control targetVersion 格式非法")
    state = value["state"]
    require(state in {"BOOTSTRAP_CLOSED", "CANDIDATE"},
            f"release-control state 非法: {state!r}")
    if state == "BOOTSTRAP_CLOSED":
        require(target == closed_version,
                "BOOTSTRAP_CLOSED 的 targetVersion 必须等于 closedVersion")
        require(validation_mode in PREPARATION_MODES,
                "BOOTSTRAP_CLOSED 只接受 repository/local 准备模式")
        require(release_phase == "CLOSED" and release_version == closed_version,
                "BOOTSTRAP_CLOSED 必须绑定 closedVersion 的 CLOSED 状态")
    else:
        require(target != closed_version,
                "CANDIDATE 的 targetVersion 不得复用 closedVersion")
        if validation_mode in PREPARATION_MODES:
            require(release_phase == "CLOSED",
                    "候选准备或 closeout 只接受 CLOSED 状态")
            require(release_version in {closed_version, target},
                    "候选准备或 closeout 的 CLOSED 版本必须是 closedVersion 或 targetVersion")
        elif validation_mode in (
            DRAFT_CONSUMPTION_MODES | FORMAL_CONSUMPTION_MODES
        ):
            require(release_phase == "FROZEN" and release_version == target,
                    "draft/正式消费必须绑定 targetVersion 的 FROZEN 状态")
        else:
            raise ReleaseControlError(
                f"release-control validation_mode 非法: {validation_mode!r}"
            )
    return value


def read_release_control(
    path: Path,
    *,
    repository: str,
    channel: str,
    release_state_path: Path,
    validation_mode: str,
) -> dict[str, Any]:
    state = json.loads(release_state_path.read_text(encoding="utf-8"))
    require(state.get("repository") == repository, "release-state repository 漂移")
    require(state.get("channel") == channel, "release-state channel 漂移")
    release_phase = state.get("phase")
    require(isinstance(release_phase, str), "release-state phase 非法")
    release_version = state.get("version")
    require(isinstance(release_version, str)
            and VERSION.fullmatch(release_version) is not None,
            "release-state version 非法")
    value = json.loads(path.read_text(encoding="utf-8"))
    return validate_release_control(
        value,
        repository=repository,
        channel=channel,
        release_phase=release_phase,
        release_version=release_version,
        validation_mode=validation_mode,
    )


class CrossHostCredentialSafeRedirect(urllib.request.HTTPRedirectHandler):
    """控制 API 如发生跨主机重定向，必须剥离 Authorization。"""

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        target = urlsplit(newurl)
        require(
            target.scheme == "https" and target.netloc.lower() == "api.github.com",
            "控制 API 重定向不得离开 https://api.github.com",
        )
        redirected = super().redirect_request(request, fp, code, msg, headers, newurl)
        if redirected is not None and (
            urlsplit(request.full_url).netloc.lower()
            != urlsplit(newurl).netloc.lower()
        ):
            redirected.remove_header("Authorization")
        return redirected


def authenticated_release_request(
    url: str,
    headers: Mapping[str, str],
) -> dict[str, Any]:
    def request_once() -> dict[str, Any]:
        request = urllib.request.Request(url, headers=dict(headers))
        opener = urllib.request.build_opener(CrossHostCredentialSafeRedirect())
        with opener.open(request, timeout=30) as response:
            value = json.load(response)
        require(isinstance(value, dict), "Release API 响应必须是对象")
        return value

    value = call_with_retry(request_once)
    require(isinstance(value, dict), "Release API 响应必须是对象")
    return value


def formal_release_metadata(
    *,
    repository: str,
    tag: str,
    release_id: str,
    event_name: str,
    event_path: Path | None,
    token: str,
    request_json: Callable[[str, Mapping[str, str]], dict[str, Any]] = authenticated_release_request,
) -> dict[str, Any]:
    """从 release event 或认证 ID 查询取得元数据；绝不匿名查 tag。"""
    require(REPOSITORY.fullmatch(repository) is not None, "repository 格式非法")
    require(VERSION.fullmatch(tag) is not None, "tag 格式非法")
    require(RELEASE_ID.fullmatch(release_id) is not None,
            "正式 Release ID 必须为十进制正整数")
    expected_id = int(release_id)

    if event_name == "release":
        require(event_path is not None, "release 事件缺少 GITHUB_EVENT_PATH")
        payload = json.loads(event_path.read_text(encoding="utf-8"))
        require(isinstance(payload, dict), "release 事件 payload 必须是对象")
        require(payload.get("action") == "published",
                "release 事件 action 必须为 published")
        event_repository = payload.get("repository")
        require(isinstance(event_repository, dict), "release 事件缺少 repository")
        require(event_repository.get("full_name") == repository,
                "release 事件 repository 身份漂移")
        release = payload.get("release")
        require(isinstance(release, dict), "release 事件缺少 release 对象")
    elif event_name == "workflow_dispatch":
        require(bool(token), "按 Release ID 复验必须注入控制 API Token")
        url = (
            f"https://api.github.com/repos/{repository}/releases/"
            f"{quote(release_id, safe='')}"
        )
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "IFLYADLib-release-control",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        release = request_json(url, headers)
    else:
        raise ReleaseControlError(
            f"正式 Release 元数据不接受事件类型: {event_name!r}"
        )

    actual_id = release.get("id")
    require(
        isinstance(actual_id, int)
        and not isinstance(actual_id, bool)
        and actual_id == expected_id,
        "Release ID 与可信输入不一致",
    )
    require(release.get("tag_name") == tag, "Release tag_name 与可信输入不一致")
    require(release.get("draft") is False, "正式 Release 不得为 draft")
    require(release.get("prerelease") is False, "正式 Release 不得为 prerelease")
    require(bool(release.get("published_at")), "正式 Release 缺少 published_at")
    assets = release.get("assets")
    require(isinstance(assets, list), "正式 Release assets 必须是数组")
    return release
