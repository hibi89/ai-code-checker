"""P2-12: virtual paste basename and preview/report contract (synthetic only)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from code_input import InputError
from desktop_core import ScanRequest, inspect_input, run_scan


class PasteVirtualFilenameTests(unittest.TestCase):
    def test_explicit_name_survives_preview_scan_and_verified_report(self) -> None:
        cases = (
            ("my-audit.py", "python", "my-audit.py", "complete"),
            ("한글자료.txt", "python", "한글자료.py", "complete"),
            ("frontend.js", "javascript", "frontend.js", "partial"),
            ("typed.ts", "typescript", "typed.ts", "partial"),
            ("module.pyi", "python", "module.pyi", "complete"),
        )
        for filename, language, actual, status in cases:
            with self.subTest(filename=filename):
                req = ScanRequest("paste", text="eval(value)\n", language=language, filename=filename)
                preview = inspect_input(req)
                self.assertEqual(preview.paths, (actual,))
                with tempfile.TemporaryDirectory() as tmp:
                    result = run_scan(req, Path(tmp) / "results", "sample",
                                      expected_preview_fingerprint=preview.fingerprint)
                    self.assertEqual(result.status, status)
                    html = result.html_path.read_text(encoding="utf-8")
                    self.assertIn(actual, html)
                    if language == "python":
                        self.assertGreaterEqual(result.verified, 1)
                        self.assertIn(actual + ":1", result.markdown_path.read_text(encoding="utf-8"))

    def test_name_change_invalidates_preview_and_publishes_nothing(self) -> None:
        before = ScanRequest("paste", text="eval(value)\n", language="python", filename="original.py")
        after = ScanRequest("paste", text=before.text, language=before.language, filename="renamed.py")
        fingerprint = inspect_input(before).fingerprint
        self.assertNotEqual(fingerprint, inspect_input(after).fingerprint)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "report"
            with self.assertRaisesRegex(InputError, "다시 미리보기"):
                run_scan(after, output, "stale", expected_preview_fingerprint=fingerprint)
            self.assertFalse(output.exists())

    def test_unsafe_virtual_filenames_are_rejected_before_output(self) -> None:
        names = (
            "", " ", "../source.py", "x/source.py", r"x\source.py", "C:source.py",
            "CON.py", "PRN.txt", "com2.py", "LPT9.txt", "foo.py.",
            "foo.py ", ".env", "source.exe", "bad|name.py", "bad\nname.py",
            "surrogate\ud800.py", "a" * 130 + ".py",
        )
        for name in names:
            with self.subTest(name=ascii(name)):
                req = ScanRequest("paste", text="eval(value)\n", language="python", filename=name)
                with self.assertRaises(InputError):
                    inspect_input(req)
                with tempfile.TemporaryDirectory() as tmp:
                    output = Path(tmp) / "output"
                    with self.assertRaises(InputError):
                        run_scan(req, output, "blocked")
                    self.assertFalse(output.exists())

    def test_suffix_conflict_rejected(self) -> None:
        for filename, language in (
            ("script.js", "python"), ("script.py", "typescript"), ("script.ts", "javascript"),
        ):
            with self.subTest(filename=filename):
                req = ScanRequest("paste", text="eval(value)\n", language=language, filename=filename)
                with self.assertRaisesRegex(InputError, "언어"):
                    inspect_input(req)

    def test_python_named_source_does_not_invoke_multitxt_parser(self) -> None:
        req = ScanRequest("paste", text="===== FILE: fake.py =====\nprint('literal')\n",
                          filename="literal.py")
        preview = inspect_input(req)
        self.assertEqual(preview.kind, "paste")
        self.assertEqual(preview.paths, ("literal.py",))
        with tempfile.TemporaryDirectory() as tmp:
            result = run_scan(req, Path(tmp) / "output", "literal",
                              expected_preview_fingerprint=preview.fingerprint)
            self.assertEqual(result.status, "partial")
            self.assertEqual(result.failed, 1)


if __name__ == "__main__":
    unittest.main()
