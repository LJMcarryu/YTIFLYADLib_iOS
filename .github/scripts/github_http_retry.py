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
