"""真实独立解释器的总期限，以及各渠道流式缓存/原子提交回归。"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import time
import unittest
from unittest import mock

SCRIPTS = next(parent / "scripts" for parent in Path(__file__).resolve().parents
               if (parent / "scripts/github_http_retry.py").is_file())
sys.path.insert(0, str(SCRIPTS))
import github_http_retry as retry

FIXTURE = '''
import os
from pathlib import Path
import socket
import time
from github_http_retry import call_with_retry

def run(mode, path, secret=""):
    path = Path(path)
    path.with_suffix(".pid").write_text(str(os.getpid()))
    if mode == "open":
        socket.getaddrinfo = lambda *args: time.sleep(20)
        socket.getaddrinfo("blocked.invalid", 443)
    elif mode == "read":
        left, right = socket.socketpair()
        left.makefile("rb").read(1)
    elif mode == "drip":
        with path.open("wb") as stream:
            while True:
                stream.write(b"x")
                stream.flush()
                time.sleep(.02)
    elif mode == "backoff":
        def fail():
            with path.open("a") as stream:
                stream.write("attempt\\n")
            raise TimeoutError("retry")
        call_with_retry(fail)
    elif mode == "orphan":
        import subprocess
        import sys
        program = "import pathlib,time,sys; f=pathlib.Path(sys.argv[1]).open('ab',buffering=0); "
        program += "[(f.write(b'x'), time.sleep(.02)) for _ in iter(int, 1)]"
        child = subprocess.Popen([sys.executable, "-c", program, str(path)])
        path.with_suffix(".child").write_text(str(child.pid))
        os._exit(0)
    elif mode == "rate_body":
        from urllib.error import HTTPError
        left, right = socket.socketpair()
        error = HTTPError("https://api.github.com/fixture", 403, "Forbidden", {}, left.makefile("rb"))
        def fail():
            raise error
        call_with_retry(fail)
    elif mode == "long_rate":
        import io
        from urllib.error import HTTPError
        def fail():
            raise HTTPError("https://api.github.com/fixture", 429, "rate", {"Retry-After":"61"}, io.BytesIO())
        call_with_retry(fail)
    elif mode == "secret":
        print(secret)
        raise ValueError("https://example.invalid/?token=" + secret)
    elif mode == "large":
        return "x" * (4 * 1024 * 1024 + 1)
    elif mode == "credentials":
        return {"secret": secret, "environment": os.environ.get("GITHUB_TOKEN")}
    elif mode == "part":
        path.write_bytes(b"verified")
        return {"digest": __import__("hashlib").sha256(b"verified").hexdigest(), "cached": False}
    return None
'''


def load_downloader():
    for name in ("release_asset_downloader.py", "download_release_assets.py", "download_release_anonymously.py"):
        path = SCRIPTS / name
        if path.is_file():
            spec = importlib.util.spec_from_file_location("deadline_test_downloader", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    raise AssertionError("missing downloader")


class WorkerDeadlineTests(unittest.TestCase):
    def setUp(self):
        self.temporary = self.enterContext(tempfile.TemporaryDirectory())
        self.root = Path(self.temporary)
        self.module = self.root / "worker_fixture.py"
        self.module.write_text(FIXTURE)

    def invoke(self, mode, *, timeout=.6, secret=""):
        return retry.execute_in_worker(self.module, "run", {
            "mode": mode, "path": str(self.root / "asset.part"), "secret": secret,
        }, timeout_seconds=timeout)

    def test_dns_open_socket_read_drip_and_backoff_share_hard_deadline(self):
        for mode in ("open", "read", "drip", "backoff", "rate_body"):
            with self.subTest(mode=mode):
                path = self.root / "asset.part"
                path.unlink(missing_ok=True)
                started = time.monotonic()
                with self.assertRaises(TimeoutError):
                    self.invoke(mode)
                self.assertLess(time.monotonic() - started, 2.5)
                pid = int(path.with_suffix(".pid").read_text())
                with self.assertRaises(ProcessLookupError):
                    os.kill(pid, 0)
                contents = path.read_bytes() if path.exists() else None
                time.sleep(.08)
                self.assertEqual(contents, path.read_bytes() if path.exists() else None)
                if mode == "backoff":
                    self.assertEqual(b"attempt\n", contents)

    def test_exited_leader_does_not_leave_descendant_holding_pipe(self):
        import subprocess
        with self.assertRaises(TimeoutError):
            self.invoke("orphan")
        child = int((self.root / "asset.child").read_text())
        state = subprocess.run(["ps", "-p", str(child), "-o", "stat="],
                               capture_output=True, text=True, check=False).stdout.strip()
        self.assertTrue(not state or state.startswith("Z"), state)
        before = (self.root / "asset.part").read_bytes()
        time.sleep(.08)
        self.assertEqual(before, (self.root / "asset.part").read_bytes())

    def test_cancellation_kills_and_reaps_worker(self):
        import subprocess
        real_popen = subprocess.Popen
        processes = []
        def launch(*args, **kwargs):
            process = real_popen(*args, **kwargs)
            processes.append(process)
            original = process.communicate
            # 第二次communicate必须实际回收，以确认取消路径而非只模拟状态。
            count = 0
            def communicate(*args, **kwargs):
                nonlocal count
                count += 1
                if count == 1:
                    raise KeyboardInterrupt()
                return original(*args, **kwargs)
            process.communicate = communicate
            return process
        with mock.patch.object(subprocess, "Popen", side_effect=launch):
            with self.assertRaises(KeyboardInterrupt):
                self.invoke("read", timeout=3)
        self.assertIsNotNone(processes[0].returncode)
        with self.assertRaises(ProcessLookupError):
            os.kill(processes[0].pid, 0)

    def test_sigterm_cancellation_reaps_worker_and_restores_handler(self):
        import signal
        import subprocess
        program = "import pathlib,signal,sys; sys.path.insert(0,sys.argv[1]); import github_http_retry as r; "
        program += "previous=signal.getsignal(signal.SIGTERM)\n"
        program += "try: r.execute_in_worker(sys.argv[2], 'run', {'mode':'read','path':sys.argv[3]}, timeout_seconds=10)\n"
        program += "except SystemExit as e:\n assert signal.getsignal(signal.SIGTERM)==previous; sys.exit(e.code)\n"
        parent = subprocess.Popen([sys.executable, "-B", "-c", program, str(SCRIPTS),
                                   str(self.module), str(self.root / "asset.part")],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        child = None
        completed = False
        try:
            deadline = time.monotonic() + 3
            pid_file = self.root / "asset.pid"
            while not pid_file.exists() and time.monotonic() < deadline:
                time.sleep(.01)
            self.assertTrue(pid_file.exists(), "worker did not become ready")
            child = int(pid_file.read_text())
            parent.send_signal(signal.SIGTERM)
            stdout, stderr = parent.communicate(timeout=3)
            self.assertEqual(143, parent.returncode, stderr.decode())
            with self.assertRaises(ProcessLookupError):
                os.kill(child, 0)
            completed = True
        finally:
            # 即使被测清场逻辑回归，测试夹具也不能遗留独立 worker。
            if not completed and child is not None:
                try:
                    os.killpg(child, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            if parent.poll() is None:
                parent.kill()
            parent.communicate(timeout=3)

    def test_non_main_thread_and_existing_sigterm_handler_fail_before_spawn(self):
        import signal
        import threading
        errors = []
        def invoke():
            try:
                self.invoke("read")
            except ValueError as error:
                errors.append(error)
        thread = threading.Thread(target=invoke)
        thread.start()
        thread.join(timeout=2)
        self.assertEqual(1, len(errors))
        self.assertFalse((self.root / "asset.pid").exists())
        previous = signal.getsignal(signal.SIGTERM)
        handler = lambda signum, frame: None
        signal.signal(signal.SIGTERM, handler)
        try:
            with self.assertRaises(ValueError):
                self.invoke("read")
            self.assertIs(handler, signal.getsignal(signal.SIGTERM))
        finally:
            signal.signal(signal.SIGTERM, previous)

    def test_sigterm_between_spawn_and_pid_registration_is_deferred_and_reaped(self):
        import signal
        import subprocess
        original_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())
        original_handler = signal.getsignal(signal.SIGTERM)
        real_popen = subprocess.Popen
        processes = []
        def interrupted_spawn(*args, **kwargs):
            process = real_popen(*args, **kwargs)
            processes.append(process)
            os.kill(os.getpid(), signal.SIGTERM)
            return process
        with mock.patch.object(subprocess, "Popen", side_effect=interrupted_spawn):
            with self.assertRaises(SystemExit) as caught:
                self.invoke("read", timeout=3)
        self.assertEqual(143, caught.exception.code)
        self.assertEqual(original_mask, signal.pthread_sigmask(signal.SIG_BLOCK, set()))
        self.assertEqual(original_handler, signal.getsignal(signal.SIGTERM))
        self.assertIsNotNone(processes[0].returncode)
        with self.assertRaises(ProcessLookupError):
            os.kill(processes[0].pid, 0)

    def test_imported_rate_limit_exception_keeps_classification_in_real_worker(self):
        with self.assertRaises(retry.WorkerFailure) as caught:
            self.invoke("long_rate", timeout=3)
        self.assertEqual("rate_limited", retry.failure_classification(caught.exception))

    def test_asset_timeout_cleans_partial_after_worker_is_reaped(self):
        destination = self.root / "asset"
        with self.assertRaises(TimeoutError):
            retry.isolated_asset_download(self.module, "run", {
                "mode": "drip", "path": str(self.root / "asset.part"),
            }, destination, timeout_seconds=.6)
        self.assertFalse(destination.exists())
        self.assertFalse((self.root / "asset.part").exists())
        time.sleep(.08)
        self.assertFalse((self.root / "asset.part").exists())

    def test_parent_commits_only_verified_worker_result(self):
        destination = self.root / "asset"
        actual = retry.isolated_asset_download(self.module, "run", {
            "mode": "part", "path": str(self.root / "asset.part"),
        }, destination, timeout_seconds=3)
        self.assertEqual(hashlib.sha256(b"verified").hexdigest(), actual)
        self.assertEqual(b"verified", destination.read_bytes())
        self.assertFalse((self.root / "asset.part").exists())

    def test_parent_rechecks_deadline_before_commit(self):
        destination = self.root / "asset"
        partial = self.root / "asset.part"
        def late(*args, **kwargs):
            partial.write_bytes(b"late")
            time.sleep(.04)
            return {"digest": "a" * 64, "cached": False}
        with self.assertRaises(TimeoutError):
            retry.isolated_asset_download(self.module, "run", {}, destination,
                                          timeout_seconds=.01, executor=late)
        self.assertFalse(destination.exists())
        self.assertFalse(partial.exists())

    def test_unconfirmed_cleanup_keeps_partial_evidence(self):
        destination = self.root / "asset"
        partial = self.root / "asset.part"
        partial.write_bytes(b"evidence")
        with self.assertRaises(retry.WorkerCleanupFailure):
            retry.isolated_asset_download(self.module, "run", {}, destination,
                executor=mock.Mock(side_effect=retry.WorkerCleanupFailure("worker_cleanup_failed")))
        self.assertEqual(b"evidence", partial.read_bytes())

    def test_worker_failure_redacts_secrets_and_large_results_fail_closed(self):
        for mode in ("secret", "large"):
            with self.subTest(mode=mode), self.assertRaises(retry.WorkerFailure) as caught:
                self.invoke(mode, timeout=3, secret="fixture-private-token")
            self.assertNotIn("fixture-private-token", str(caught.exception))
            self.assertNotIn("example.invalid", str(caught.exception))
            self.assertEqual("deterministic", retry.failure_classification(caught.exception))

    def test_credentials_use_stdin_and_are_removed_from_worker_environment(self):
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "environment-secret"}):
            result = self.invoke("credentials", timeout=3, secret="stdin-secret")
        self.assertEqual({"secret": "stdin-secret", "environment": None}, result)

    def test_json_reader_accepts_short_reads_and_enforces_limit(self):
        class ShortReads(io.BytesIO):
            def read(self, size=-1):
                return super().read(min(size, 3))
        self.assertEqual({"value": 1}, retry.read_json_response(ShortReads(b'{"value":1}')))
        with self.assertRaises(ValueError):
            retry.read_json_response(io.BytesIO(b" " * (4 * 1024 * 1024 + 1)))


class ChannelDeadlineTests(unittest.TestCase):
    def setUp(self):
        self.downloader = load_downloader()
        self.temporary = self.enterContext(tempfile.TemporaryDirectory())
        self.destination = Path(self.temporary) / "asset.zip"
        self.payload = b"verified" * (300 * 1024)
        self.asset = {"name": self.destination.name, "size": len(self.payload),
            "digest": "sha256:" + hashlib.sha256(self.payload).hexdigest(),
            "url": "https://api.github.com/repos/owner/sdk/releases/assets/1",
            "browser_download_url": "https://github.com/owner/sdk/releases/download/1.0.0/asset.zip"}

    def download(self, *, executor=None, authenticated=False):
        module = self.downloader
        if hasattr(module, "download_anonymously"):
            if authenticated:
                return module.download_authenticated(self.asset, self.destination, "fixture-token", executor=executor)
            return module.download_anonymously(self.asset, self.destination, executor=executor)
        if hasattr(module, "download_asset"):
            return module.download_asset(self.asset, self.destination,
                mode="draft_candidate" if authenticated else "formal_release", token="fixture-token", executor=executor)
        return module.download_and_hash(self.asset, self.destination, executor=executor)

    def inline(self, path, name, arguments, **kwargs):
        return getattr(self.downloader, name)(**arguments)

    def test_verified_cache_with_stale_partial_cannot_be_overwritten(self):
        self.destination.write_bytes(self.payload)
        partial = self.destination.with_name("asset.zip.part")
        partial.write_bytes(b"unverified stale data")
        # 走真正worker：无网络合法缓存只能被复用，残留.part不能被发布。
        self.assertEqual(self.asset["digest"][7:], self.download())
        self.assertEqual(self.payload, self.destination.read_bytes())
        self.assertFalse(partial.exists())

    def test_asset_reads_and_cache_hash_are_streamed(self):
        module = self.downloader
        calls = []
        class StreamingResponse(io.BytesIO):
            def read(self, size=-1):
                if size <= 0 or size > 1024 * 1024:
                    raise AssertionError("unbounded asset read")
                calls.append(size)
                return super().read(min(size, 17777))
            def geturl(self):
                return "https://release-assets.githubusercontent.com/object"
        factory = mock.Mock(return_value=StreamingResponse(self.payload))
        target = "open_url" if hasattr(module, "open_url") else "urlopen"
        with mock.patch.object(module, target, factory), \
             mock.patch.object(Path, "read_bytes", side_effect=AssertionError("whole-file cache read")):
            self.assertEqual(self.asset["digest"][7:], self.download(executor=self.inline))
            self.assertEqual(self.asset["digest"][7:], self.download(executor=self.inline))
        self.assertGreater(len(calls), 2)
        factory.assert_called_once()
        self.assertEqual(self.payload, self.destination.read_bytes())

    def test_ys_oversized_stream_stops_before_another_read(self):
        module = self.downloader
        if not hasattr(module, "open_url"):
            return
        class OversizedResponse(io.BytesIO):
            calls = 0
            def read(self, size=-1):
                self.calls += 1
                if self.calls > 1:
                    raise AssertionError("oversized stream must stop before next read")
                return b"xx"
            def geturl(self):
                return "https://release-assets.githubusercontent.com/object"
        self.asset["size"] = 1
        response = OversizedResponse()
        with mock.patch.object(module, "open_url", return_value=response):
            with self.assertRaisesRegex(module.DownloadError, "下载大小"):
                self.download(executor=self.inline)
        self.assertEqual(1, response.calls)
        self.assertFalse(self.destination.exists())
        self.assertFalse(self.destination.with_name("asset.zip.part").exists())

    def test_asset_entry_points_enforce_default_total_budget(self):
        captured = []
        self.destination.write_bytes(self.payload)
        def executor(path, name, arguments, *, timeout_seconds):
            captured.append((name, arguments, timeout_seconds))
            return {"digest": "a" * 64, "cached": True}
        self.download(executor=executor)
        self.assertEqual("_download_asset_worker", captured[0][0])
        self.assertGreater(captured[0][2], 299)
        self.assertLessEqual(captured[0][2], 300)
        if hasattr(self.downloader, "download_anonymously") or hasattr(self.downloader, "download_asset"):
            self.download(executor=executor, authenticated=True)
            self.assertEqual("fixture-token", captured[-1][1]["token"])

    def test_metadata_entry_points_wrap_complete_retry_in_180_second_worker(self):
        from urllib.request import Request
        captured = []
        def executor(path, name, arguments, *, timeout_seconds):
            captured.append((name, timeout_seconds))
            return {}
        module = self.downloader
        request = Request("https://api.github.com/repos/owner/sdk/releases/1")
        if hasattr(module, "read_json"):
            self.assertEqual({}, module.read_json(request, executor=executor))
        elif hasattr(module, "request_json"):
            self.assertEqual({}, module.request_json(request.full_url, {}, executor=executor))
        else:
            spec = importlib.util.spec_from_file_location("deadline_test_draft", SCRIPTS / "download_draft_release.py")
            draft = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(draft)
            self.assertEqual({}, draft.read_authenticated_json(None, request, "test", executor=executor))
        spec = importlib.util.spec_from_file_location("deadline_test_control", SCRIPTS / "release_metadata_control.py")
        control = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(control)
        self.assertEqual({}, control.authenticated_release_request(request.full_url, {}, executor=executor))
        self.assertEqual(2, len(captured))
        self.assertTrue(all(name.endswith("_worker") and budget == 180 for name, budget in captured))

    def test_digest_failure_does_not_publish_or_retry(self):
        module = self.downloader
        response = io.BytesIO(b"x" * len(self.payload))
        response.geturl = lambda: "https://release-assets.githubusercontent.com/object"
        target = "open_url" if hasattr(module, "open_url") else "urlopen"
        with mock.patch.object(module, target, return_value=response) as opened:
            with self.assertRaises((RuntimeError, ValueError)):
                self.download(executor=self.inline)
        opened.assert_called_once()
        self.assertFalse(self.destination.exists())
        self.assertFalse(self.destination.with_name("asset.zip.part").exists())


if __name__ == "__main__":
    unittest.main()
