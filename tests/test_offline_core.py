"""Synthetic-only offline MVP Day 1 acceptance tests; no remote API calls."""
from __future__ import annotations

import io
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from code_input import InputError, InputLimits
from offline_core import OFFLINE_LIMITS, scan_path, scan_text


class OfflineCoreTests(unittest.TestCase):
    def test_1200_line_txt_python_maps_original_line(self) -> None:
        content = "".join("number = 1\n" for _ in range(1199)) + "eval(input('command'))\n"
        result = scan_text(content, filename="long.txt", language="python")
        self.assertEqual(result.status, "complete")
        self.assertEqual(result.counts["analyzed"], 1)
        self.assertEqual(result.bundle.files[0].line_count, 1200)
        self.assertTrue(any(f.start_line == 1200 and "동적 코드 실행" in f.title for f in result.findings))
        self.assertEqual(result.origin_for("long.py", 1200), ("long.txt", 1200))

    def test_txt_unknown_language_marks_limited_not_clean(self) -> None:
        result = scan_text("eval(user_input)\n", filename="unclassified.txt")
        self.assertEqual(result.status, "partial")
        self.assertEqual(result.counts["limited"], 1)
        self.assertEqual(result.counts["analyzed"], 0)
        self.assertFalse(any("동적 코드 실행" in f.title for f in result.findings))

    def test_multi_file_txt_recovers_paths_and_source_lines(self) -> None:
        content = (
            "===== FILE: src/main.py =====\n"
            "from auth import validate\n"
            "eval('1+1')\n"
            "===== FILE: src/auth.py =====\n"
            "def validate():\n"
            "    return True\n"
        )
        result = scan_text(content, filename="combined.txt")
        self.assertEqual(result.status, "complete")
        self.assertEqual(result.counts["analyzed"], 2)
        self.assertEqual(result.origin_for("src/main.py", 2), ("combined.txt", 3))
        self.assertEqual(result.origin_for("src/auth.py", 2), ("combined.txt", 6))
        self.assertTrue(any(f.file_path == "src/main.py" and f.start_line == 2 for f in result.findings))

    def test_multi_file_marker_escape_survives(self) -> None:
        text = (
            "===== FILE: main.py =====\n"
            "# example\n"
            "\\===== FILE: example.py =====\n"
            "print('done')\n"
        )
        result = scan_text(text, filename="combined.txt")
        self.assertIn("===== FILE: example.py =====", result.bundle.files[0].text)
        self.assertEqual(result.counts["analyzed"], 1)
        self.assertEqual(result.origin_for("main.py", 2), ("combined.txt", 3))

    def test_malformed_header_rejected(self) -> None:
        with self.assertRaises(InputError):
            scan_text("===== FILE: a.py ===\nprint(1)\n", filename="combine.txt")

    def test_duplicate_windows_case_path_rejected(self) -> None:
        text = "===== FILE: src/A.py =====\nprint(1)\n===== FILE: src/a.py =====\nprint(2)\n"
        with self.assertRaises(InputError):
            scan_text(text, filename="combine.txt")

    def test_path_traversal_in_combined_txt_rejected(self) -> None:
        with self.assertRaises(InputError):
            scan_text("===== FILE: ../secret.py =====\nprint(1)\n", filename="combine.txt")

    def test_sensitive_section_excluded_without_source_leak(self) -> None:
        secret = "GEMINI_API_KEY=synthetic-private-token-123456789"
        text = (
            "===== FILE: src/app.py =====\nprint('ok')\n"
            "===== FILE: .env =====\n" + secret + "\n"
        )
        result = scan_text(text, filename="bundle.txt")
        self.assertEqual(result.status, "partial")
        self.assertEqual(result.counts["excluded"], 1)
        self.assertNotIn(secret, result.bundle.render())
        self.assertNotIn(secret, str(result.summary()))

    def test_syntax_error_not_reported_as_complete(self) -> None:
        result = scan_text("def oops(:\n pass\n", filename="broken.py")
        self.assertEqual(result.status, "partial")
        self.assertEqual(result.counts["failed"], 1)
        self.assertTrue(any("구문 오류" in f.title for f in result.findings))

    def test_zip_12_files_and_original_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "project.zip"
            with zipfile.ZipFile(path, "w") as z:
                for i in range(12):
                    z.writestr(f"src/file{i}.py", "print('ok')\n" * 100)
                z.writestr(".env", "PRIVATE=synthetic-secret")
            original = path.read_bytes()
            result = scan_path(path)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(result.counts["analyzed"], 12)
            self.assertEqual(result.counts["excluded"], 1)
            self.assertEqual(result.status, "partial")
            self.assertNotIn("synthetic-secret", result.bundle.render())

    def test_zip_traversal_is_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "unsafe.zip"
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("../escaped.py", "print('danger')")
            with self.assertRaises(InputError):
                scan_path(path)

    def test_zip_duplicate_case_path_is_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "duplicate.zip"
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("SRC/main.py", "print(1)")
                z.writestr("src/Main.py", "print(2)")
            with self.assertRaises(InputError):
                scan_path(path)

    def test_large_12000_lines_and_200_files_within_limits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(200):
                (root / f"module_{i}.py").write_text("number = 1\n" * 60, encoding="utf-8")
            result = scan_path(root)
            self.assertEqual(result.status, "complete")
            self.assertEqual(result.counts["analyzed"], 200)
            self.assertEqual(sum(s.line_count for s in result.bundle.files), 12000)
            self.assertEqual(len(result.findings), 0)

    def test_mixed_txt_marks_unsupported_without_truncating_supported(self) -> None:
        text = (
            "===== FILE: main.py =====\nprint('ok')\n"
            "===== FILE: binary.exe =====\nnot-executable-data\n"
        )
        result = scan_text(text, filename="mixed.txt")
        self.assertEqual(result.counts["analyzed"], 1)
        self.assertEqual(result.counts["unsupported"], 1)
        self.assertEqual(result.status, "partial")

    def test_language_selection_invalid_is_fail_closed(self) -> None:
        with self.assertRaises(InputError):
            scan_text("print('x')", filename="code.py", language="python")
        with self.assertRaises(InputError):
            scan_text("print('x')", filename="code.txt", language="unknown")

    def test_ignores_untrusted_commands_and_never_networks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "should-never-exist"
            source = f"from pathlib import Path\nPath({str(marker)!r}).write_text('bad')\n"
            with patch("socket.create_connection", side_effect=AssertionError("network forbidden")):
                result = scan_text(source, filename="synthetic.py")
            self.assertEqual(result.status, "complete")
            self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
