"""公开仓下载器共用的有界网络重试；不读取或添加任何凭据。"""
from __future__ import annotations

from email.utils import parsedate_to_datetime
import json
import math
import socket
import ssl
import time
from urllib.error import HTTPError, URLError


class RateLimitWaitRequired(RuntimeError):
    pass


def _number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) and result >= 0 else None
    except (TypeError, ValueError, OverflowError):
        return None


def rate_limit_wait(error: HTTPError, *, now=None):
    """只有明确限流证据才接受 403，保留服务端给出的最早重试时间。"""
    now = time.time() if now is None else now
    headers = {str(k).lower(): str(v) for k, v in (error.headers or {}).items()}
    retry_after = headers.get("retry-after")
    delay = _number(retry_after)
    if delay is None and retry_after:
        try:
            date = parsedate_to_datetime(retry_after)
            if date.tzinfo is not None:
                delay = max(0.0, date.timestamp() - now)
        except (TypeError, ValueError, OverflowError):
            pass
    reset = _number(headers.get("x-ratelimit-reset"))
    if headers.get("x-ratelimit-remaining") == "0" and reset is not None:
        delay = max(delay or 0.0, reset - now, 0.0)
    if delay is not None:
        return delay
    # HTTPError 的响应流只能读取一次；只缓存判定结果，不输出响应内容。
    if not hasattr(error, "_ifly_confirmed_rate_limit"):
        message = ""
        try:
            payload = json.loads(error.read(16384))
            if isinstance(payload, dict) and isinstance(payload.get("message"), str):
                message = payload["message"].lower()
        except (TypeError, ValueError, OSError):
            pass
        error._ifly_confirmed_rate_limit = any(text in message for text in (
            "api rate limit exceeded", "exceeded a secondary rate limit",
            "secondary rate limit exceeded",
        ))
    return 0.0 if error._ifly_confirmed_rate_limit else None


def retry_delay(error: BaseException, attempt: int, *, now=None):
    backoff = min(2 ** (attempt - 1), 8)
    if isinstance(error, HTTPError):
        if error.code in (403, 429):
            wait = rate_limit_wait(error, now=now)
            if wait is None and error.code == 403:
                return None
            if wait is not None and wait > 60:
                raise RateLimitWaitRequired(
                    f"GitHub 限流要求等待 {math.ceil(wait)} 秒，超过单次 60 秒等待预算；"
                    "请在配额恢复后续跑原发布任务"
                ) from error
            return max(backoff, wait or 0.0)
        return backoff if error.code == 408 or 500 <= error.code <= 599 else None
    reason = error.reason if isinstance(error, URLError) else error
    if isinstance(reason, (TimeoutError, socket.timeout, ssl.SSLError, ConnectionError)):
        return backoff
    return None


def failure_classification(error: BaseException) -> str:
    """给发布汇总提供稳定失败分类，不包含 URL、响应正文或凭据。"""
    if isinstance(error, WorkerFailure):
        return error.classification
    if isinstance(error, RateLimitWaitRequired):
        return "rate_limited"
    if isinstance(error, HTTPError):
        if error.code in (403, 429) and rate_limit_wait(error) is not None:
            return "rate_limited"
        if error.code == 408 or 500 <= error.code <= 599:
            return "network_timeout"
        return "deterministic"
    reason = error.reason if isinstance(error, URLError) else error
    if isinstance(reason, (TimeoutError, socket.timeout, ssl.SSLError, ConnectionError)):
        return "network_timeout"
    return "deterministic"


def call_with_retry(operation, *, max_attempts=5, sleeper=None):
    if not isinstance(max_attempts, int) or isinstance(max_attempts, bool) or max_attempts < 1:
        raise ValueError("max_attempts 必须为正整数")
    sleeper = time.sleep if sleeper is None else sleeper
    for attempt in range(1, max_attempts + 1):
        try:
            return operation()
        except Exception as error:
            if attempt == max_attempts:
                raise
            delay = retry_delay(error, attempt)
            if delay is None:
                raise
            sleeper(delay)
    raise AssertionError("unreachable")


class WorkerFailure(OSError):
    """子进程只返回失败分类，不把 URL、响应正文或凭据带回诊断。"""

    def __init__(self, classification, status=None):
        self.classification = classification
        self.status = status
        detail = f" HTTP {status}" if status is not None else ""
        super().__init__(f"GitHub 请求失败：{classification}{detail}")


class WorkerCleanupFailure(WorkerFailure):
    pass


def execute_in_worker(module_path, function_name, arguments, *, timeout_seconds):
    """CLI 主线程入口：取消会回收 worker，并恢复调用前的 SIGTERM handler。"""
    import signal
    import threading
    if threading.current_thread() is not threading.main_thread():
        raise ValueError("独立下载 worker 必须从 CLI 主线程启动")
    previous = signal.getsignal(signal.SIGTERM)
    if previous != signal.SIG_DFL:
        raise ValueError("独立下载 worker 不接管调用方已有的 SIGTERM handler")
    def cancel(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, cancel)
    try:
        return _execute_in_worker(module_path, function_name, arguments,
                                  timeout_seconds=timeout_seconds)
    finally:
        signal.signal(signal.SIGTERM, previous)


def _execute_in_worker(module_path, function_name, arguments, *, timeout_seconds):
    """使用独立解释器对整个操作实施墙钟期限，包含 DNS、读取和退避。

    参数通过匿名 pipe 传递；调用方可显式注入同签名执行器做同步逻辑测试。
    worker 不发布最终资产，调用方仅在此函数成功返回后提交已校验的 .part。
    """
    import os
    from pathlib import Path
    import signal
    import subprocess
    import sys

    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) \
            or not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("总请求期限必须是有限正数")
    deadline = time.monotonic() + timeout_seconds
    payload = json.dumps({"module": str(Path(module_path).resolve()),
                          "function": function_name, "arguments": arguments}).encode()
    environment = dict(os.environ)
    for name in ("GH_TOKEN", "GITHUB_TOKEN", "GITHUB_AUTH_TOKEN", "IFLY_PRIVATE_SOURCE_TOKEN"):
        environment.pop(name, None)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    process = None

    def terminate():
        if process is None:
            return
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except OSError:
            raise WorkerCleanupFailure("worker_cleanup_failed") from None
        # 期限之后只允许有界回收；未回收成功不能当作普通网络重试。
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            raise WorkerCleanupFailure("worker_cleanup_failed") from None

    try:
        # 屏蔽创建窗口内的取消；登记 PID 后解除时，待处理信号进入下方清场。
        previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM})
        try:
            environment["_IFLY_RELEASE_PARENT_SIGNAL_MASK"] = ",".join(str(int(item)) for item in previous_mask)
            process = subprocess.Popen(
                [sys.executable, "-B", str(Path(__file__).resolve()), "--worker"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                env=environment, start_new_session=True,
            )
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise subprocess.TimeoutExpired(process.args, timeout_seconds)
        stdout, _ = process.communicate(payload, timeout=remaining)
    except subprocess.TimeoutExpired:
        terminate()
        raise TimeoutError("GitHub 操作超过总期限（包括传输、重试和退避）") from None
    except BaseException:
        terminate()
        raise
    # communicate 已回收成功后不得再向旧 PID/PGID 发信号。
    if time.monotonic() >= deadline:
        raise TimeoutError("GitHub 操作超过总期限（包括传输、重试和退避）")
    if process.returncode != 0:
        raise WorkerFailure("worker_failed")
    try:
        result = json.loads(stdout)
        if result["ok"] is True:
            if time.monotonic() >= deadline:
                raise TimeoutError("GitHub 操作超过总期限，未接受 worker 结果")
            return result["value"]
        if result["ok"] is not False:
            raise ValueError("invalid worker response")
        classification = result["classification"]
        if classification not in {"rate_limited", "network_timeout", "deterministic"}:
            raise ValueError("invalid worker failure")
        status = result.get("status")
        if status is not None and (type(status) is not int or not 100 <= status <= 599):
            raise ValueError("invalid worker status")
    except (KeyError, TypeError, ValueError):
        raise WorkerFailure("worker_protocol_failed") from None
    raise WorkerFailure(classification, status)


def _worker_main():
    import os
    import signal
    # exec 继承了临时屏蔽；只在 worker 中还原父进程进入创建窗口前的 mask。
    inherited_mask = os.environ.pop("_IFLY_RELEASE_PARENT_SIGNAL_MASK", "")
    signal.pthread_sigmask(signal.SIG_SETMASK, {int(item) for item in inherited_mask.split(",") if item})
    import importlib.util
    from pathlib import Path
    import sys

    try:
        request = json.load(sys.stdin)
        path = Path(request["module"]).resolve()
        sys.path.insert(0, str(path.parent))
        import contextlib
        import os
        with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            specification = importlib.util.spec_from_file_location("_ifly_worker_operation", path)
            module = importlib.util.module_from_spec(specification)
            sys.modules[specification.name] = module
            specification.loader.exec_module(module)
            operation = getattr(module, request["function"])
            value = operation(**request["arguments"])
        result = {"ok": True, "value": value}
    except BaseException as error:
        result = {"ok": False, "classification": failure_classification(error)}
        if isinstance(error, HTTPError):
            result["status"] = error.code
    encoded = json.dumps(result)
    if len(encoded.encode("utf-8")) > 4 * 1024 * 1024:
        encoded = json.dumps({"ok": False, "classification": "deterministic"})
    sys.stdout.write(encoded)
    sys.stdout.flush()


def read_json_response(response):
    """元数据有界读取；大型二进制只能走资产流式路径。"""
    chunks = []
    size = 0
    while chunk := response.read(min(64 * 1024, 4 * 1024 * 1024 + 1 - size)):
        size += len(chunk)
        if size > 4 * 1024 * 1024:
            raise ValueError("GitHub API JSON 超过 4 MiB 上限")
        chunks.append(chunk)
    return json.loads(b"".join(chunks).decode("utf-8"))


def isolated_asset_download(module_path, function_name, arguments, destination, *,
                            timeout_seconds=300, executor=None):
    """worker 验证 .part；父进程回收 worker 后才原子发布结果。"""
    from pathlib import Path
    destination = Path(destination)
    temporary = destination.with_name(destination.name + ".part")
    if temporary.is_symlink():
        raise ValueError("临时下载目标不得为符号链接")
    runner = execute_in_worker if executor is None else executor
    deadline = time.monotonic() + timeout_seconds
    cleanup_safe = True
    try:
        result = runner(module_path, function_name, arguments,
                        timeout_seconds=max(0.001, deadline - time.monotonic()))
        import re
        if (not isinstance(result, dict) or not isinstance(result.get("digest"), str)
                or re.fullmatch(r"[0-9a-f]{64}", result["digest"]) is None
                or type(result.get("cached")) is not bool):
            raise WorkerFailure("worker_protocol_failed")
        if result["cached"] and (destination.is_symlink() or not destination.is_file()):
            raise WorkerFailure("worker_protocol_failed")
        if time.monotonic() >= deadline:
            raise TimeoutError("GitHub 资产超过总期限，未提交临时文件")
        if result.get("cached") is not True:
            if temporary.is_symlink() or not temporary.is_file():
                raise WorkerFailure("worker_protocol_failed")
            temporary.replace(destination)
        return result["digest"]
    except WorkerCleanupFailure:
        cleanup_safe = False
        raise
    finally:
        # 清场无法确认时保留现场，不删除仍可能被占用的临时文件。
        if cleanup_safe:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    import sys
    if sys.argv[1:] != ["--worker"]:
        raise SystemExit("仅支持内部 worker 调用")
    # 下载模块导入本 helper 时复用同一类身份，避免限流异常被误分类。
    sys.modules["github_http_retry"] = sys.modules[__name__]
    _worker_main()
