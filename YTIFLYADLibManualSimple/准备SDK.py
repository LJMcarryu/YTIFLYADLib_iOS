#!/usr/bin/env python3
"""按同目录清单准备固定版本 SDK；仅使用 Python 标准库。"""
from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import zipfile

HOST = "download-adsdk.voiceads.cn"
MAX_ARCHIVE = 512 * 1024 * 1024
MAX_EXTRACTED = 2 * 1024 * 1024 * 1024
MAX_ENTRIES = 50000
TIMEOUT = 30
DEADLINE = 180
STATE = ".prepared.json"


class PrepareError(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise PrepareError(message)


def validate_url(url):
    require(isinstance(url, str), "资产 URL 必须为字符串")
    parsed = urllib.parse.urlsplit(url)
    require(parsed.scheme == "https" and parsed.netloc == HOST
            and not parsed.query and not parsed.fragment,
            "资产只允许使用指定 TOS 主机的 HTTPS 地址")
    return parsed


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def manifest(root):
    path = root / "sdk-artifacts.json"
    require(path.is_file() and not path.is_symlink(), "缺少普通文件 sdk-artifacts.json")
    raw = path.read_bytes()
    require(len(raw) <= 1024 * 1024, "资产清单超过大小上限")
    data = json.loads(raw)
    require(isinstance(data, dict), "资产清单必须为对象")
    require(data.get("schemaVersion") == 1, "资产清单 schemaVersion 必须为 1")
    version, channel = data.get("version"), data.get("channel")
    require(isinstance(version, str) and re.fullmatch(r"\d+\.\d+\.\d+", version), "SDK 版本格式非法")
    require(channel in {"general", "ys", "yt", "youku", "ys-splash"}, "SDK 渠道非法")
    assets = data.get("assets")
    require(isinstance(assets, list) and 0 < len(assets) <= 20, "资产列表必须包含 1 至 20 项")
    names, filenames = set(), set()
    for asset in assets:
        require(isinstance(asset, dict), "资产必须为对象")
        name = asset.get("name")
        require(isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9_-]+\.xcframework", name), "XCFramework 名称非法")
        require(name not in names, "资产名称重复")
        names.add(name)
        parsed = validate_url(asset.get("url"))
        filename = PurePosixPath(parsed.path).name
        require(re.fullmatch(r"[A-Za-z0-9_.-]+\.zip", filename)
                and parsed.path == f"/ios_sdk/{version}/{channel}/{filename}", "资产 URL 与版本或渠道不一致")
        require(filename not in filenames, "资产 ZIP 文件名重复")
        filenames.add(filename)
        require(isinstance(asset.get("sha256"), str)
                and re.fullmatch(r"[0-9a-f]{64}", asset["sha256"]), "资产 SHA-256 必须为小写十六进制摘要")
    return data, hashlib.sha256(raw).hexdigest()


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def inventory(vendor):
    require(vendor.is_dir() and not vendor.is_symlink(), "Vendor 必须为普通目录")
    result = {}
    for path in sorted(vendor.rglob("*")):
        relative = path.relative_to(vendor).as_posix()
        if relative == STATE:
            continue
        require(not path.is_symlink(), "Vendor 中不允许符号链接")
        if path.is_dir():
            result[relative] = {"type": "directory"}
        else:
            require(path.is_file() and path.stat().st_nlink == 1, "Vendor 中不允许特殊文件或硬链接")
            result[relative] = {"type": "file", "sha256": digest(path),
                                "mode": stat.S_IMODE(path.stat().st_mode)}
    return result


def acquire(asset, target, archive_dir):
    started = time.monotonic()
    if archive_dir is not None:
        source = archive_dir / PurePosixPath(asset["url"]).name
        require(source.is_file() and not source.is_symlink(), f"离线 ZIP 不存在或不是普通文件：{source.name}")
        stream = source.open("rb")
    else:
        # 默认 ProxyHandler 使用 HTTPS_PROXY/http_proxy 等用户环境配置。
        opener = urllib.request.build_opener(SafeRedirect())
        stream = opener.open(asset["url"], timeout=TIMEOUT)
    total = 0
    value = hashlib.sha256()
    with stream, target.open("wb") as output:
        while True:
            require(time.monotonic() - started < DEADLINE, "单资产下载超过总期限")
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            require(total <= MAX_ARCHIVE, "资产 ZIP 超过大小上限")
            output.write(chunk)
            value.update(chunk)
    require(time.monotonic() - started < DEADLINE, "单资产下载超过总期限")
    require(value.hexdigest() == asset["sha256"], f"资产 SHA-256 校验失败：{asset['name']}")


def _download_worker(asset, target, connection):
    try:
        acquire(asset, Path(target), None)
        connection.send(None)
    except Exception as exc:
        connection.send(str(exc))
    finally:
        connection.close()


def download(asset, target, archive_dir):
    if archive_dir is not None:
        return acquire(asset, target, archive_dir)
    # 独立进程保证 DNS、代理握手或持续慢速响应也受总期限限制。
    context = multiprocessing.get_context("spawn")
    receiving, sending = context.Pipe(duplex=False)
    process = context.Process(target=_download_worker, args=(asset, str(target), sending))
    process.start()
    sending.close()
    try:
        process.join(DEADLINE)
        require(not process.is_alive(), "单资产下载超过总期限")
        require(process.exitcode == 0 and receiving.poll(), "下载进程异常结束")
        error = receiving.recv()
        require(error is None, f"下载失败：{error}")
    finally:
        if process.is_alive():
            process.terminate()
            process.join(2)
        if process.is_alive():
            process.kill()
            process.join()
        receiving.close()


def extract(archive, destination, name):
    with zipfile.ZipFile(archive) as source:
        entries = source.infolist()
        require(len(entries) <= MAX_ENTRIES, "ZIP 文件数量超过上限")
        require(sum(item.file_size for item in entries) <= MAX_EXTRACTED, "ZIP 解压大小超过上限")
        seen = set()
        for item in entries:
            relative = PurePosixPath(item.filename)
            require(item.filename and "\\" not in item.filename and not relative.is_absolute()
                    and ".." not in relative.parts and relative.parts[0] == name
                    and all(part not in {"", "."} for part in item.filename.rstrip("/").split("/")),
                    "ZIP 含路径穿越或非预期根目录")
            key = relative.as_posix().casefold()
            require(key not in seen, "ZIP 含重复路径")
            seen.add(key)
            kind = stat.S_IFMT(item.external_attr >> 16)
            require(kind in {0, stat.S_IFREG, stat.S_IFDIR}, "ZIP 不允许符号链接或特殊文件")
            require(kind != stat.S_IFDIR or item.is_dir(), "ZIP 目录类型不一致")
            output = destination.joinpath(*relative.parts)
            if item.is_dir():
                output.mkdir(parents=True, exist_ok=True)
            else:
                output.parent.mkdir(parents=True, exist_ok=True)
                with source.open(item) as incoming, output.open("xb") as outgoing:
                    shutil.copyfileobj(incoming, outgoing, 1024 * 1024)
                output.chmod(0o755 if item.external_attr >> 16 & 0o111 else 0o644)
    require((destination / name / "Info.plist").is_file(), f"ZIP 缺少 {name}/Info.plist")


def prepare(root, *, refresh=False, archive_dir=None):
    root = Path(root).resolve()
    data, manifest_sha = manifest(root)
    vendor = root / "Vendor"
    require(not vendor.is_symlink(), "拒绝符号链接 Vendor；请人工检查")
    require(not vendor.exists() or vendor.is_dir(), "Vendor 必须为目录")
    if vendor.exists() and not refresh:
        try:
            state_path = vendor / STATE
            require(not state_path.is_symlink() and state_path.is_file(), "缺少准备状态")
            state = json.loads(state_path.read_text())
            require(isinstance(state, dict) and state.get("schemaVersion") == 1 and state.get("manifestSha256") == manifest_sha
                    and state.get("tree") == inventory(vendor), "清单或 Vendor 文件发生变化")
        except (OSError, ValueError, PrepareError) as exc:
            raise PrepareError("Vendor 校验失败；请使用 --refresh 明确重建本示例 Vendor") from exc
        return "已复用通过校验的 Vendor"
    with tempfile.TemporaryDirectory(prefix=".sdk-prepare-", dir=root) as temporary:
        temporary = Path(temporary)
        staged = temporary / "Vendor"
        staged.mkdir()
        for index, asset in enumerate(data["assets"]):
            archive = temporary / f"{index}.zip"
            download(asset, archive, Path(archive_dir) if archive_dir is not None else None)
            extract(archive, staged, asset["name"])
            archive.unlink()
        state = {"schemaVersion": 1, "version": data["version"], "channel": data["channel"],
                 "manifestSha256": manifest_sha, "tree": inventory(staged)}
        (staged / STATE).write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
        # 同一文件系统内重命名；失败时恢复原 Vendor，绝不合并半成品。
        backup = temporary / "previous"
        require(not vendor.is_symlink(), "拒绝符号链接 Vendor")
        had_vendor = vendor.exists()
        if had_vendor:
            vendor.rename(backup)
        try:
            staged.rename(vendor)
        except OSError:
            if had_vendor:
                backup.rename(vendor)
            raise
    return "SDK 已准备到本示例 Vendor"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="完整校验后替换本示例 Vendor")
    parser.add_argument("--archive-dir", type=Path, help="从此目录读取与 URL 同名的 ZIP，不联网")
    args = parser.parse_args()
    try:
        print(prepare(Path(__file__).resolve().parent, refresh=args.refresh, archive_dir=args.archive_dir))
        return 0
    except (PrepareError, OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"准备 SDK 失败：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
