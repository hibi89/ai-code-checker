"""One-command minimum *working* offline Code Checker acceptance.

Uses synthetic sources only. Verifies the real preview -> scan -> HTML/Markdown
report path and fail-closed inputs without customer code, remote requests,
Windows settings, a GUI window, or release/certification assertions.

Usage: python -m scripts.mvp_acceptance
"""
from __future__ import annotations

import socket
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

from code_input import InputError
from desktop_core import ScanRequest, inspect_input, run_scan


def run_mvp_acceptance() -> dict[str, bool]:
    """Exercise the user-critical pipeline with no external services."""
    checks: dict[str, bool] = {}

    def prohibit_network(*_args, **_kwargs):
        raise AssertionError("Offline MVP attempted network access")

    with tempfile.TemporaryDirectory(prefix="codechecker-mvp-") as name:
        root = Path(name)
        source = root / "synthetic-input"
        source.mkdir()
        reports = root / "reports"
        source_file = source / "main.py"
        source_file.write_text(
            "print('synthetic sample')\n"
            "eval(input('synthetic parameter: '))\n",
            encoding="utf-8",
        )
        untouched = source_file.read_bytes()
        request = ScanRequest("path", source=str(source))

        with patch("socket.create_connection", side_effect=prohibit_network), \
             patch.object(socket.socket, "connect", prohibit_network), \
             patch.object(socket.socket, "connect_ex", prohibit_network):
            preview = inspect_input(request)
            if preview.files != 1 or preview.python_files != 1:
                raise AssertionError("MVP preview failed to identify synthetic Python")
            checks["preview"] = True

            result = run_scan(
                request, reports, "synthetic-python",
                expected_preview_fingerprint=preview.fingerprint,
            )
            if (result.status != "complete" or result.analyzed != 1
                    or result.findings < 1 or result.verified < 1):
                raise AssertionError("MVP Python scan failed to locate supported risk")
            checks["scan_and_findings"] = True

            html = result.html_path.read_text(encoding="utf-8")
            markdown = result.markdown_path.read_text(encoding="utf-8")
            if (not result.html_path.is_file() or not result.markdown_path.is_file()
                    or "Content-Security-Policy" not in html
                    or "main.py:2" not in html
                    or "eval" not in markdown
                    or len(html) < 200 or len(markdown) < 100):
                raise AssertionError("MVP Korean reports are missing critical content")
            checks["html_and_markdown"] = True

            if source_file.read_bytes() != untouched:
                raise AssertionError("Customer source was modified during inspection")
            checks["source_untouched"] = True

            try:
                run_scan(request, reports, "synthetic-python")
            except FileExistsError:
                pass
            else:
                raise AssertionError("MVP overwrote an existing report")
            if result.html_path.read_text(encoding="utf-8") != html:
                raise AssertionError("Failed overwrite modified prior report")
            checks["no_overwrite"] = True

            mixed_zip = root / "mixed.zip"
            with zipfile.ZipFile(mixed_zip, "w") as archive:
                archive.writestr("safe.py", "print('ok')\n")
                archive.writestr("frontend.js", "const value = 1;\n")
                archive.writestr(".env", "SYNTHETIC_SECRET_NOT_FOR_REPORT=unit_test_only")
            zip_bytes = mixed_zip.read_bytes()
            mixed_req = ScanRequest("path", source=str(mixed_zip))
            zip_preview = inspect_input(mixed_req)
            zip_report = run_scan(
                mixed_req, reports, "synthetic-mixed",
                expected_preview_fingerprint=zip_preview.fingerprint,
            )
            if (zip_report.status != "partial" or zip_report.limited < 1
                    or zip_report.excluded < 1):
                raise AssertionError("MVP falsely declared partial JS/ZIP coverage complete")
            if ("SYNTHETIC_SECRET_NOT_FOR_REPORT" in
                    zip_report.html_path.read_text(encoding="utf-8")):
                raise AssertionError("MVP report leaked excluded secret fixture")
            if mixed_zip.read_bytes() != zip_bytes:
                raise AssertionError("Original ZIP changed")
            checks["partial_and_redaction"] = True

            unsafe_zip = root / "unsafe.zip"
            with zipfile.ZipFile(unsafe_zip, "w") as archive:
                archive.writestr("../out-of-folder.py", "print('must-not-run')\n")
            try:
                run_scan(
                    ScanRequest("path", source=str(unsafe_zip)),
                    reports, "must-not-publish",
                )
            except InputError:
                pass
            else:
                raise AssertionError("MVP accepted ZIP path traversal")
            if ((reports / "must-not-publish.html").exists()
                    or (reports / "must-not-publish.md").exists()):
                raise AssertionError("Blocked ZIP generated a report")
            checks["blocked_input_no_report"] = True

    required = (
        "preview", "scan_and_findings", "html_and_markdown",
        "source_untouched", "no_overwrite", "partial_and_redaction",
        "blocked_input_no_report",
    )
    if tuple(checks) != required or not all(checks.values()):
        raise AssertionError("MVP acceptance did not cover all required workflows")
    return checks


def main() -> int:
    try:
        checked = run_mvp_acceptance()
    except Exception as exc:
        # Do not print source contents or environment paths in public CI logs.
        print("OFFLINE_MVP_ACCEPTANCE_FAIL=" + type(exc).__name__)
        return 1
    print("OFFLINE_MVP_ACCEPTANCE_PASS")
    print("MVP_ACCEPTANCE_GATE_COUNT=" + str(len(checked)))
    print("OFFLINE_NO_MODEL_API=TRUE")
    print("CUSTOMER_WINDOWS_ACCEPTANCE=UNVERIFIED")
    print("LICENSE_AND_RELEASE_APPROVED=FALSE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
