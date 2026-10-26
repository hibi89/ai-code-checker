"""Offline Day 2 report tests: synthetic fixtures only; no customer source or API."""
from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
import zipfile
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from code_input import InputError
from offline_core import scan_path, scan_text
from offline_report import (
    build_report, main, render_html, render_markdown, write_report,
)


class OfflineReportTests(unittest.TestCase):
    def test_complete_python_findings_are_located_and_verified(self) -> None:
        scan = scan_text("x = 1\neval(input('value'))\n", filename="main.py")
        report = build_report(scan)
        self.assertEqual(report.status, "complete")
        self.assertEqual(report.verified_count, 1)
        self.assertEqual(report.findings[0].rule_id, "PY-DYNAMIC-EXEC")
        self.assertIn("main.py:2", render_markdown(report))
        self.assertIn("eval", render_html(report))
        self.assertIn("Content-Security-Policy", render_html(report))
        self.assertNotIn("<script", render_html(report))

    def test_clean_code_no_findings_does_not_assert_safe(self) -> None:
        report = build_report(scan_text("print('ok')\n", filename="safe.py"))
        self.assertEqual(report.status, "complete")
        self.assertEqual(len(report.findings), 0)
        self.assertIn("안전하다는 의미는 아닙니다", render_markdown(report))

    def test_multi_txt_maps_back_to_original_source_line(self) -> None:
        scan = scan_text(
            "===== FILE: src/main.py =====\nx = 1\neval('1+1')\n",
            filename="combined.txt",
        )
        report = build_report(scan)
        self.assertEqual(report.status, "complete")
        self.assertIn("src/main.py:2 (원본 combined.txt:3)", render_markdown(report))
        self.assertEqual(report.findings[0].origin_line, 3)

    def test_unsupported_and_failed_files_cannot_be_clean(self) -> None:
        unsupported = scan_text("const a = 1;\n", filename="main.js")
        report = build_report(unsupported)
        self.assertEqual(report.status, "partial")
        self.assertIn("제한적 패턴 검사", render_html(report))
        broken = scan_text("def oops(:\n pass\n", filename="bad.py")
        failed = build_report(broken)
        self.assertEqual(failed.status, "partial")
        self.assertIn("구문 분석 실패", render_html(failed))

    def test_forged_citation_flag_and_source_are_not_trusted(self) -> None:
        scan = scan_text("eval('1+1')\n", filename="main.py")
        item = scan.findings[0]
        scan.findings = [
            replace(item, file_path="../unknown.py", citation_verified=True, evidence="SECRET-UNVERIFIED"),
            replace(item, start_line=42, end_line=42, citation_verified=True),
            replace(item, evidence="NOT IN CODE", citation_verified=True),
            replace(item, source="ai", citation_verified=True),
        ]
        report = build_report(scan)
        self.assertEqual(report.status, "partial")
        self.assertEqual(report.verified_count, 0)
        self.assertEqual(len(report.validation_issues), 4)
        self.assertNotIn("SECRET-UNVERIFIED", render_html(report))
        self.assertNotIn("NOT IN CODE", render_markdown(report))

    def test_repeated_findings_are_deduplicated(self) -> None:
        scan = scan_text("eval('1+1')\n", filename="main.py")
        scan.findings.append(scan.findings[0])
        report = build_report(scan)
        self.assertEqual(len(report.findings), 1)
        self.assertEqual(report.verified_count, 1)

    def test_xss_and_markdown_controls_are_escaped(self) -> None:
        scan = scan_text("eval('<img src=x onerror=alert(1)>')\n", filename="x.py")
        item = scan.findings[0]
        scan.findings[0] = replace(
            item, title="<script>alert(1)</script>", impact="[evil](https://example.com)",
            recommendation="**no** | table > heading",
        )
        report = build_report(scan)
        html_text = render_html(report)
        md_text = render_markdown(report)
        self.assertNotIn("<script>", html_text)
        self.assertNotIn("<img src=x", html_text)
        self.assertIn("&lt;script&gt;", html_text)
        self.assertIn("&lt;img", html_text)
        self.assertNotIn("[evil](https://example.com)", md_text)
        self.assertNotIn("**no**", md_text)

    def test_sensitive_code_is_redacted_in_reports(self) -> None:
        token = "synthetic-supersecretpassword-123456"
        scan = scan_text("password = '" + token + "'\n", filename="app.py")
        report = build_report(scan)
        self.assertNotIn(token, render_html(report))
        self.assertNotIn(token, render_markdown(report))

    def test_atomic_report_output_and_collision(self) -> None:
        scan = scan_text("eval('1+1')\n", filename="main.py")
        with tempfile.TemporaryDirectory() as tmp:
            html_path, md_path = write_report(build_report(scan), tmp, name="검사결과")
            self.assertTrue(html_path.exists())
            self.assertTrue(md_path.exists())
            original = html_path.read_bytes()
            with self.assertRaises(FileExistsError):
                write_report(build_report(scan), tmp, name="검사결과")
            self.assertEqual(original, html_path.read_bytes())
            self.assertEqual(list(Path(tmp).glob("*.tmp")), [])

    def test_failed_second_publish_rolls_back_first(self) -> None:
        report = build_report(scan_text("print('ok')\n", filename="x.py"))
        with tempfile.TemporaryDirectory() as tmp:
            original_link = os.link
            call_count = 0

            def failing_link(src: object, dst: object) -> None:
                nonlocal call_count
                call_count += 1
                if call_count == 2:
                    raise OSError("synthetic link failure")
                original_link(src, dst)

            with patch("offline_report.os.link", side_effect=failing_link):
                with self.assertRaises(OSError):
                    write_report(report, tmp)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_output_name_and_symlink_validation(self) -> None:
        report = build_report(scan_text("print(1)\n", filename="x.py"))
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("../outside", "..", ".hidden", "bad/name"):
                with self.assertRaises(InputError):
                    write_report(report, tmp, name=name)

    def test_zip_cli_success_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source.zip"
            output = Path(tmp) / "reports"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("main.py", "eval('1+1')\n")
            with patch("socket.create_connection", side_effect=AssertionError("network forbidden")):
                with patch.object(sys, "argv", [
                    "offline_report.py", str(path), "--output-dir", str(output),
                ]):
                    with patch("sys.stdout", new_callable=io.StringIO) as stdout:
                        code = main()
            self.assertEqual(code, 0)
            self.assertIn('"status": "complete"', stdout.getvalue())
            self.assertTrue((output / "code-checker-report.html").exists())
            self.assertTrue((output / "code-checker-report.md").exists())

    def test_cli_partial_exit_code_on_unknown_language(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source.js"
            path.write_text("const a = 1;\n", encoding="utf-8")
            with patch.object(sys, "argv", [
                "offline_report.py", str(path), "--output-dir", str(Path(tmp) / "reports"),
            ]):
                with patch("sys.stdout", new_callable=io.StringIO):
                    self.assertEqual(main(), 3)


if __name__ == "__main__":
    unittest.main()
