"""Malformed clipboard Unicode must fail closed and permit a fresh retry."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from code_input import InputError, bundle_from_text
from desktop_core import ScanRequest, inspect_input, run_scan
from offline_core import scan_text
from offline_report import build_report


class PasteUnicodeRecoveryTests(unittest.TestCase):
    def test_paste_surrogates_are_rejected_as_input_error(self) -> None:
        # Unpaired UTF-16 surrogate code points cannot be represented as UTF-8.
        for fragment in ("\ud800", "\udfff", "\ud800\ud800"):
            with self.subTest(fragment=ascii(fragment)):
                source = "eval(value)\n" + fragment
                for scan in (
                    lambda: bundle_from_text(source, filename="pasted.txt"),
                    lambda: scan_text(source, filename="pasted.py"),
                    lambda: inspect_input(
                        ScanRequest("paste", text=source, language="python")
                    ),
                ):
                    with self.assertRaises(InputError) as error:
                        scan()
                    message = str(error.exception)
                    self.assertIn("UTF-8", message)
                    self.assertNotIn("eval(value)", message)
                    self.assertNotIn("UnicodeEncodeError", message)

    def test_failed_scan_does_not_publish_and_retry_succeeds(self) -> None:
        invalid = ScanRequest("paste", text="print('bad')\n\ud800", language="python")
        valid = ScanRequest("paste", text="eval('1+1')\n", language="python")
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "reports"
            with self.assertRaises(InputError):
                run_scan(invalid, output, "first-attempt")
            self.assertFalse(output.exists(), "Failed paste must not create report files")

            preview = inspect_input(valid)
            result = run_scan(
                valid, output, "retry",
                expected_preview_fingerprint=preview.fingerprint,
            )
            self.assertEqual(result.status, "complete")
            self.assertGreaterEqual(result.findings, 1)
            self.assertGreaterEqual(result.verified, 1)
            self.assertTrue(result.html_path.exists())
            self.assertTrue(result.markdown_path.exists())
            self.assertFalse((output / "first-attempt.html").exists())
            self.assertFalse((output / "first-attempt.md").exists())

    def test_valid_unicode_is_preserved_and_scanned_normally(self) -> None:
        code = 'message = "한글 😀"\nprint(message)\n'
        bundle = bundle_from_text(code, filename="valid.py")
        self.assertIn("한글 😀", bundle.files[0].text)
        report = build_report(scan_text(code, filename="valid.py"))
        self.assertEqual(report.status, "complete")
        self.assertEqual(report.validation_issues, ())


if __name__ == "__main__":
    unittest.main()
