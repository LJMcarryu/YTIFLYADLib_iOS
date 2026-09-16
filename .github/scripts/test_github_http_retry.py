from __future__ import annotations

from email.message import Message
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest import mock
from urllib.error import HTTPError


SCRIPT = next(parent / "scripts/github_http_retry.py" for parent in Path(__file__).resolve().parents
              if (parent / "scripts/github_http_retry.py").is_file())
SPEC = importlib.util.spec_from_file_location("tested_github_http_retry", SCRIPT)
RETRY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RETRY)
ERRORS = []


def http_error(code=403, headers=None, message="Forbidden"):
    values = Message()
    for key, value in (headers or {}).items():
        values[key] = value
    error = HTTPError("https://api.github.com/repos/owner/sdk/releases", code, message,
                      values, io.BytesIO(json.dumps({"message": message}).encode()))
    ERRORS.append(error)
    return error


class GitHubRetryTests(unittest.TestCase):
    def tearDown(self):
        for error in ERRORS:
            error.close()
        ERRORS.clear()

    def test_permission_denial_is_not_retried(self):
        operation = mock.Mock(side_effect=http_error())
        sleeper = mock.Mock()
        with self.assertRaises(HTTPError):
            RETRY.call_with_retry(operation, sleeper=sleeper)
        self.assertEqual(operation.call_count, 1)
        sleeper.assert_not_called()

    def test_confirmed_rate_limit_recovers_without_changing_request(self):
        operation = mock.Mock(side_effect=[http_error(message="API rate limit exceeded for shared runner"), {"id": 7}])
        sleeper = mock.Mock()
        self.assertEqual(RETRY.call_with_retry(operation, sleeper=sleeper), {"id": 7})
        self.assertEqual(operation.call_count, 2)
        sleeper.assert_called_once_with(1)

    def test_rate_limit_body_can_be_classified_more_than_once(self):
        error = http_error(message="You have exceeded a secondary rate limit.")
        self.assertEqual(RETRY.retry_delay(error, 1), 1)
        self.assertEqual(RETRY.retry_delay(error, 2), 2)

    def test_server_retry_time_is_respected(self):
        self.assertEqual(RETRY.retry_delay(http_error(headers={"Retry-After": "12"}), 1), 12)
        self.assertEqual(RETRY.retry_delay(http_error(headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1030"}), 1, now=1000), 30)

    def test_long_server_wait_fails_with_actionable_message(self):
        with self.assertRaisesRegex(RETRY.RateLimitWaitRequired, "超过单次 60 秒"):
            RETRY.retry_delay(http_error(headers={"Retry-After": "3600"}), 1)

    def test_malformed_or_incomplete_rate_headers_do_not_relax_403(self):
        for headers in ({"Retry-After": "NaN"}, {"Retry-After": "-1"},
                        {"X-RateLimit-Remaining": "0"},
                        {"X-RateLimit-Remaining": "1", "X-RateLimit-Reset": "1030"}):
            with self.subTest(headers=headers):
                self.assertIsNone(RETRY.retry_delay(http_error(headers=headers), 1, now=1000))

    def test_missing_or_unauthorized_asset_is_never_retried(self):
        for code in (401, 404):
            self.assertIsNone(RETRY.retry_delay(http_error(code, {"Retry-After": "1"}), 1))

    def test_retry_count_is_bounded(self):
        operation = mock.Mock(side_effect=TimeoutError("connection stalled"))
        sleeper = mock.Mock()
        with self.assertRaises(TimeoutError):
            RETRY.call_with_retry(operation, max_attempts=3, sleeper=sleeper)
        self.assertEqual(operation.call_count, 3)
        self.assertEqual(sleeper.call_args_list, [mock.call(1), mock.call(2)])

    def test_validation_failure_is_not_retried(self):
        operation = mock.Mock(side_effect=ValueError("SHA-256 mismatch"))
        with self.assertRaises(ValueError):
            RETRY.call_with_retry(operation)
        self.assertEqual(operation.call_count, 1)


if __name__ == "__main__":
    unittest.main()
