"""PROOFQA AX P70 real agent-browser localhost-only synthetic UI acceptance.

Hardcoded local HTTP server. No customer URL, cookie, token, payments, external
site, credential, destructive action, browser extension, or cloud session.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from proofqa_p70 import AGENT_BROWSER_VERSION

HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>ProofQA Local Fixture</title></head>
<body><h1>PROOFQA synthetic staging</h1>
<button id="load-ok">Load 200</button>
<button id="load-fail">Load 500</button>
<input id="draft" aria-label="Synthetic draft" value="initial">
<button id="save">Save synthetic</button>
<button id="reopen">Reopen synthetic</button>
<p id="status" aria-live="polite">idle</p><p id="reopened">not-read</p>
<script>
const status = document.querySelector("#status");
const reopened = document.querySelector("#reopened");
document.querySelector("#load-ok").onclick = async () => {
  const r = await fetch("/api/ok");
  status.textContent = "HTTP " + r.status;
};
document.querySelector("#load-fail").onclick = async () => {
  const r = await fetch("/api/fail");
  status.textContent = "HTTP " + r.status;
};
document.querySelector("#save").onclick = async () => {
  const r = await fetch("/api/save", {
    method: "POST", headers: {"Content-Type":"application/json"},
    body: JSON.stringify({draft: document.querySelector("#draft").value})
  });
  status.textContent = "SAVED " + r.status;
};
document.querySelector("#reopen").onclick = async () => {
  const r = await fetch("/api/reopen");
  const data = await r.json();
  reopened.textContent = data.draft;
  status.textContent = "REOPEN " + r.status;
};
</script></body></html>"""


class LocalFixtureHandler(BaseHTTPRequestHandler):
    events: list[tuple[str, str, int]] = []
    draft: str = "initial"
    events_lock = threading.Lock()

    def log_message(self, *_args) -> None:
        return

    def _answer(self, code: int, payload: bytes, content_type: str = "application/json") -> None:
        with type(self).events_lock:
            type(self).events.append((self.command, self.path, code))
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "null")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; script-src 'unsafe-inline'; connect-src 'self'; "
            "style-src 'none'; img-src 'none'; base-uri 'none'; form-action 'none'",
        )
        self.end_headers()
        self.wfile.write(payload)

    def _allowed_host(self) -> bool:
        host = self.headers.get("Host", "")
        return host.startswith("127.0.0.1:") and host.count(":") == 1

    def do_GET(self) -> None:
        if not self._allowed_host():
            return self._answer(403, b'{"error":"host not allowed"}')
        path = urlsplit(self.path).path
        if path == "/":
            return self._answer(200, HTML.encode("utf-8"), "text/html; charset=utf-8")
        if path == "/api/ok":
            return self._answer(200, b'{"ok":true}')
        if path == "/api/fail":
            return self._answer(500, b'{"ok":false,"synthetic":true}')
        if path == "/api/reopen":
            return self._answer(200, json.dumps({"draft": type(self).draft}).encode("utf-8"))
        if path == "/favicon.ico":
            return self._answer(204, b"")
        return self._answer(404, b'{"error":"not found"}')

    def do_POST(self) -> None:
        if not self._allowed_host() or urlsplit(self.path).path != "/api/save":
            return self._answer(403, b'{"error":"not allowed"}')
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 1 <= length <= 500 or self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                return self._answer(400, b'{"error":"invalid body"}')
            data = json.loads(self.rfile.read(length))
            value = data.get("draft")
            if not isinstance(value, str) or len(value) > 80:
                return self._answer(400, b'{"error":"invalid draft"}')
            type(self).draft = value
        except (ValueError, KeyError, TypeError):
            return self._answer(400, b'{"error":"invalid json"}')
        return self._answer(200, b'{"saved":true}')


def browser_call(session: str, *arguments: str) -> str:
    command = ["agent-browser", "--session", session, *arguments]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=55, check=False)
    if result.returncode:
        raise RuntimeError("Agent browser failed on local synthetic action: "
                           + " ".join(arguments) + "\n"
                           + result.stderr[-1600:] + "\n" + result.stdout[-700:])
    return result.stdout.strip()


def assert_dom(session: str, selector: str, expected: str) -> str:
    previous = ""
    for _ in range(15):
        previous = browser_call(session, "get", "text", selector)
        if expected in previous:
            return previous
        time.sleep(.2)
    raise AssertionError(f"Synthetic DOM mismatch selector={selector}, expected={expected}, got={previous}")


def evaluate() -> dict[str, object]:
    version = subprocess.run(["agent-browser", "--version"], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=15, check=True)
    if AGENT_BROWSER_VERSION not in version.stdout:
        raise AssertionError("Wrong pinned agent-browser CLI version: " + version.stdout)
    LocalFixtureHandler.events = []
    LocalFixtureHandler.draft = "initial"
    server = ThreadingHTTPServer(("127.0.0.1", 0), LocalFixtureHandler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}/"
    session = "proofqa-p70-" + str(os.getpid())
    try:
        browser_call(session, "open", url)
        snapshot = browser_call(session, "snapshot", "-i")
        if not all(text in snapshot for text in ("Load 200", "Load 500", "Save synthetic", "Reopen synthetic")):
            raise AssertionError("Real agent-browser accessibility snapshot lacks fixture controls")
        browser_call(session, "click", "#load-ok")
        assert_dom(session, "#status", "HTTP 200")
        browser_call(session, "click", "#load-fail")
        assert_dom(session, "#status", "HTTP 500")
        browser_call(session, "fill", "#draft", "proofqa-approved-synthetic")
        browser_call(session, "click", "#save")
        assert_dom(session, "#status", "SAVED 200")
        browser_call(session, "reload")
        browser_call(session, "click", "#reopen")
        assert_dom(session, "#status", "REOPEN 200")
        assert_dom(session, "#reopened", "proofqa-approved-synthetic")
        # Server-side evidence avoids trusting only a changed browser DOM.
        events = list(LocalFixtureHandler.events)
        requirements = [
            ("GET", "/api/ok", 200), ("GET", "/api/fail", 500),
            ("POST", "/api/save", 200), ("GET", "/api/reopen", 200),
        ]
        if not all(event in events for event in requirements):
            raise AssertionError(f"Real HTTP request/response evidence missing: {events!r}")
        if any(path not in {"/", "/api/ok", "/api/fail", "/api/save", "/api/reopen", "/favicon.ico"}
               for _, path, _ in events):
            raise AssertionError("Unexpected network path reached local fixture")
        return {
            "contract": "proofqa.p70.browser.acceptance.v1",
            "status": "PASS",
            "agent_browser_version": AGENT_BROWSER_VERSION,
            "browser_kind": "real Chromium controlled by agent-browser",
            "scope": "synthetic 127.0.0.1 only",
            "snapshot_confirmed": True,
            "clicked_controls": 4,
            "http_requests_checked": requirements,
            "persist_and_reopen_verified": True,
            "browser_network_evidence": "server-received real GET/POST and 200/500",
            "customer_site_tested": False, "payment_or_destructive_actions": False,
            "release_state": "HOLD",
        }
    finally:
        try:
            browser_call(session, "close")
        except Exception:
            pass
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    try:
        print(json.dumps(evaluate(), ensure_ascii=False, sort_keys=True, indent=2))
    except Exception as exc:
        print("PROOFQA_P70_BROWSER_FAIL:", exc, file=sys.stderr)
        raise
