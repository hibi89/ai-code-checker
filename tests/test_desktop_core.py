"""Synthetic-only desktop workflow tests; Tk window is never launched here."""
from __future__ import annotations

import importlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from code_input import InputError
from desktop_core import ScanRequest, inspect_input, run_scan


class DesktopWorkflowTests(unittest.TestCase):
    def test_preview_does_not_invoke_static_checks(self) -> None:
        source = ScanRequest("paste", text="eval('1+1')\n", language="python")
        with patch("offline_core.run_static_checks", side_effect=AssertionError("premature scan")):
            preview = inspect_input(source)
        self.assertEqual(preview.files, 1)
        self.assertEqual(preview.python_files, 1)
        self.assertEqual(preview.generic_files, 0)
        self.assertIn("정적 코드 검사는 실행하지 않습니다", preview.display())

    def test_preflight_and_scan_for_1200_line_python_txt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "example.txt"
            source.write_text("x = 1\n" * 1199 + "eval('1+1')\n", encoding="utf-8")
            unchanged = source.read_bytes()
            request = ScanRequest("path", source=str(source), language="python")
            preflight = inspect_input(request)
            self.assertEqual(preflight.files, 1)
            self.assertEqual(preflight.lines, 1200)
            result = run_scan(request, Path(tmp) / "reports", "test-scan")
            self.assertEqual(result.status, "complete")
            self.assertGreaterEqual(result.findings, 1)
            self.assertEqual(result.verified, result.findings)
            self.assertEqual(source.read_bytes(), unchanged)
            self.assertIn("example.py:1200", result.html_path.read_text(encoding="utf-8"))
            self.assertTrue(result.markdown_path.exists())

    def test_multi_txt_preview_excluded_and_origin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "combined.txt"
            path.write_text(
                "===== FILE: src/main.py =====\n"
                "eval('1+1')\n"
                "===== FILE: .env =====\n"
                "PRIVATE=synthetic-do-not-publish\n"
                "===== FILE: README.md =====\n"
                "Explanation only\n", encoding="utf-8",
            )
            req = ScanRequest("path", source=str(path))
            preview = inspect_input(req)
            self.assertEqual(preview.kind, "multi-txt")
            self.assertEqual(preview.files, 2)
            self.assertEqual(preview.excluded, 1)
            self.assertEqual(preview.excluded_paths, (".env",))
            self.assertIn("제외·미지원 파일", preview.display())
            self.assertIn(".env", preview.display())
            self.assertNotIn("synthetic-do-not-publish", preview.display())
            self.assertEqual(preview.python_files, 1)
            self.assertEqual(preview.generic_files, 1)
            result = run_scan(req, Path(tmp) / "result", "combined")
            self.assertEqual(result.status, "partial")
            self.assertEqual(result.excluded, 1)
            self.assertIn("combined.txt:2", result.html_path.read_text(encoding="utf-8"))
            self.assertNotIn("synthetic-do-not-publish", result.html_path.read_text(encoding="utf-8"))

    def test_zip_preview_counts_and_avoids_customer_code_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "project.zip"
            marker = Path(tmp) / "must-not-exist"
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("main.py", f"open({str(marker)!r}, 'w').write('bad')\n")
                z.writestr("app.js", "const a = 1;\n")
                z.writestr(".env", "secret=notread")
            original = path.read_bytes()
            request = ScanRequest("path", source=str(path))
            with patch("socket.create_connection", side_effect=AssertionError("no network")):
                preview = inspect_input(request)
                result = run_scan(request, Path(tmp) / "reports", "zip")
            self.assertEqual(preview.files, 2)
            self.assertEqual(preview.excluded, 1)
            self.assertEqual(preview.excluded_paths, (".env",))
            self.assertIn("제외·미지원 파일", preview.display())
            self.assertIn(".env", preview.display())
            self.assertNotIn("secret=notread", preview.display())
            self.assertEqual(result.status, "partial")
            self.assertEqual(result.limited, 1)
            self.assertFalse(marker.exists())
            self.assertEqual(path.read_bytes(), original)

    def test_paste_python_and_unknown_language_report_states(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            request = ScanRequest("paste", text="eval('1+1')\n", language="python")
            ok = run_scan(request, Path(tmp) / "ok", "paste")
            self.assertEqual(ok.status, "complete")
            self.assertEqual(ok.analyzed, 1)
            unknown = run_scan(
                ScanRequest("paste", text="const x = 1;\n"),
                Path(tmp) / "unknown", "paste-unknown",
            )
            self.assertEqual(unknown.status, "partial")
            self.assertEqual(unknown.limited, 1)
            self.assertEqual(unknown.analyzed, 0)

    def test_reject_empty_mode_language_and_non_txt_suffix_selection(self) -> None:
        with self.assertRaises(InputError):
            inspect_input(ScanRequest("paste", text="   ", language="python"))
        with self.assertRaises(InputError):
            inspect_input(ScanRequest("other", text="hello"))
        with self.assertRaises(InputError):
            inspect_input(ScanRequest("path", source=""))
        with self.assertRaises(InputError):
            inspect_input(ScanRequest("path", source="x.py", language="python"))
        with self.assertRaises(InputError):
            inspect_input(ScanRequest("paste", text="text", language="ruby"))
        with self.assertRaises(InputError):
            inspect_input(ScanRequest("paste", text="===== FILE: main.py =====\nprint(1)\n", language="python"))

    def test_zip_traversal_is_blocked_before_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = Path(tmp) / "unsafe.zip"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("../escape.py", "print('x')")
            with self.assertRaises(InputError):
                inspect_input(ScanRequest("path", source=str(zip_path)))
            with self.assertRaises(InputError):
                run_scan(ScanRequest("path", source=str(zip_path)), Path(tmp) / "reports", "blocked")
            self.assertFalse((Path(tmp) / "reports").exists())

    def test_report_names_do_not_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            request = ScanRequest("paste", text="print('safe')\n", language="python")
            run_scan(request, tmp, "same")
            original = (Path(tmp) / "same.html").read_bytes()
            with self.assertRaises(FileExistsError):
                run_scan(request, tmp, "same")
            self.assertEqual(original, (Path(tmp) / "same.html").read_bytes())

    def test_headless_gui_import_does_not_start_window(self) -> None:
        with patch("desktop_core.inspect_input", side_effect=AssertionError("no scan on import")):
            module = importlib.import_module("desktop_ui")
            self.assertTrue(callable(module.launch))


if __name__ == "__main__":
    unittest.main()
