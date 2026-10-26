"""Synthetic Windows Chromium/Edge HTML -> PDF print acceptance probe.

Verifies a real local browser engine can print our offline HTML in CI.
This is not the GUI print button (users print in their own browser), nor
a full PDF visual inspection or a clean consumer Windows PC test.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from desktop_core import ScanRequest, run_scan


def find_browser() -> Path | None:
    if sys.platform != "win32":
        return None
    candidates = [
        Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)"))
        / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        Path(os.environ.get("ProgramFiles", "C:/Program Files"))
        / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        Path(os.environ.get("ProgramFiles", "C:/Program Files"))
        / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)"))
        / "Google" / "Chrome" / "Application" / "chrome.exe",
    ]
    return next((p for p in candidates if p.is_file()), None)


def main() -> int:
    browser = find_browser()
    if browser is None:
        print("WINDOWS_BROWSER_PRINT_UNAVAILABLE: no installed Chrome/Edge", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="code-checker-print-") as tmp:
        target = Path(tmp) / "한글 PDF 결과"
        target.mkdir()
        scan = run_scan(
            ScanRequest("paste", text="x = 1\neval('1+1')\n", language="python"),
            target, "synthetic-print",
        )
        html = scan.html_path.read_text(encoding="utf-8")
        if "코드체커 오프라인 진단 보고서" not in html:
            print("REPORT_HTML_INVALID", file=sys.stderr)
            return 1
        if re.search(r"""(?:src|href)\s*=\s*['"]https?://""", html, re.I):
            print("REMOTE_ASSET_REFERENCE_DETECTED", file=sys.stderr)
            return 1
        expected_pdf = target / "브라우저 출력 검사.pdf"
        user_dir = target / "temporary-browser-profile"
        args = [
            str(browser),
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-networking",
            "--disable-sync",
            "--disable-extensions",
            "--no-pdf-header-footer",
            "--no-sandbox",
            "--user-data-dir=" + str(user_dir),
            "--print-to-pdf=" + str(expected_pdf),
            scan.html_path.resolve().as_uri(),
        ]
        try:
            completed = subprocess.run(
                args, timeout=70, capture_output=True, text=True, errors="replace",
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            print("PDF_BROWSER_EXECUTION_FAILURE " + type(exc).__name__, file=sys.stderr)
            return 1
        if completed.returncode != 0:
            print("PDF_BROWSER_EXIT " + str(completed.returncode), file=sys.stderr)
            return 1
        if not expected_pdf.is_file():
            print("PDF_NOT_CREATED", file=sys.stderr)
            return 1
        if expected_pdf.stat().st_size < 1500 or expected_pdf.open("rb").read(5) != b"%PDF-":
            print("PDF_SIGNATURE_OR_SIZE_INVALID", file=sys.stderr)
            return 1
        print("WINDOWS_BROWSER_PDF_SYNTHETIC_PASS")
        print("BROWSER=" + browser.name)
        print("PDF_BYTES=" + str(expected_pdf.stat().st_size))
        print("PDF_GUI_PRINT_DIALOG=UNVERIFIED")
        print("PDF_VISUAL_INSPECTION=UNVERIFIED")
        print("CLEAN_WINDOWS_BROWSERS=UNVERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
