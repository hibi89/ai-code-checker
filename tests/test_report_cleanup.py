"""Synthetic local report deletion checks. No personal or customer files are read."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from desktop_core import ScanRequest, run_scan
from report_cleanup import (
    ReportCleanupError, capture_report_receipt, delete_report_pair,
    validate_current_report_receipt,
)


class ReportCleanupTests(unittest.TestCase):
    def make_pair(self, root: Path):
        dest = root / "outputs"
        result = run_scan(
            ScanRequest("paste", text="eval('1')\n", language="python"),
            dest, "code-checker-synthetic",
        )
        self.assertIsNotNone(result.report_receipt)
        return result

    def test_only_current_generated_pair_removed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.py"
            source.write_text("critical synthetic input", encoding="utf-8")
            result = self.make_pair(root)
            sibling = result.html_path.parent / "other-report.md"
            sibling.write_text("retain", encoding="utf-8")
            receipt = result.report_receipt
            self.assertEqual(receipt.html.path, result.html_path)
            self.assertEqual(receipt.markdown.path, result.markdown_path)
            delete_report_pair(receipt)
            self.assertFalse(result.html_path.exists())
            self.assertFalse(result.markdown_path.exists())
            self.assertTrue(sibling.exists())
            self.assertEqual(source.read_text(encoding="utf-8"), "critical synthetic input")

    def test_changed_contents_even_if_same_size_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.make_pair(Path(tmp))
            before = result.html_path.read_bytes()
            result.html_path.write_bytes(before.replace(b"<title>", b"<TITLE>", 1))
            self.assertEqual(len(before), result.html_path.stat().st_size)
            with self.assertRaises(ReportCleanupError):
                delete_report_pair(result.report_receipt)
            self.assertTrue(result.html_path.exists())
            self.assertTrue(result.markdown_path.exists())

    def test_missing_partner_blocks_both_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.make_pair(Path(tmp))
            result.markdown_path.unlink()
            with self.assertRaises(ReportCleanupError):
                delete_report_pair(result.report_receipt)
            self.assertTrue(result.html_path.exists())

    def test_replaced_symlink_blocks_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.make_pair(root)
            target = root / "important"
            target.write_text("keep", encoding="utf-8")
            result.html_path.unlink()
            try:
                result.html_path.symlink_to(target)
            except (NotImplementedError, OSError):
                self.skipTest("symlink not available without Windows privilege")
            with self.assertRaises(ReportCleanupError):
                delete_report_pair(result.report_receipt)
            self.assertEqual(target.read_text(encoding="utf-8"), "keep")
            self.assertTrue(result.markdown_path.exists())

    def test_hardlink_protected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.make_pair(root)
            linked = root / "linked.html"
            os.link(result.html_path, linked)
            with self.assertRaises(ReportCleanupError):
                delete_report_pair(result.report_receipt)
            self.assertTrue(result.html_path.exists())
            self.assertTrue(result.markdown_path.exists())
            self.assertTrue(linked.exists())

    def test_current_report_open_accepts_unchanged_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = self.make_pair(Path(tmp))
            self.assertEqual(
                validate_current_report_receipt(report.report_receipt),
                report.html_path,
            )

    def test_current_report_open_blocks_same_size_html_modification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = self.make_pair(Path(tmp))
            original = report.html_path.read_bytes()
            changed = original.replace(b"<title>", b"<TITLE>", 1)
            self.assertNotEqual(original, changed)
            self.assertEqual(len(original), len(changed))
            report.html_path.write_bytes(changed)
            with self.assertRaises(ReportCleanupError):
                validate_current_report_receipt(report.report_receipt)
            self.assertTrue(report.html_path.exists())
            self.assertTrue(report.markdown_path.exists())

    def test_current_report_open_blocks_changed_or_missing_markdown(self) -> None:
        for missing in (False, True):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as tmp:
                report = self.make_pair(Path(tmp))
                if missing:
                    report.markdown_path.unlink()
                else:
                    report.markdown_path.write_bytes(b"# different markdown\n")
                with self.assertRaises(ReportCleanupError):
                    validate_current_report_receipt(report.report_receipt)
                self.assertTrue(report.html_path.exists())

    def test_current_report_open_requires_verified_receipt_and_single_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = self.make_pair(root)
            with self.assertRaises(ReportCleanupError):
                validate_current_report_receipt(None)
            alias = root / "other.html"
            os.link(report.html_path, alias)
            with self.assertRaises(ReportCleanupError):
                validate_current_report_receipt(report.report_receipt)
            self.assertTrue(report.html_path.exists())
            self.assertTrue(alias.exists())

    def test_no_arbitrary_pair_or_output_directory_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a.html"
            b = root / "b.md"
            a.write_text("a", encoding="utf-8")
            b.write_text("b", encoding="utf-8")
            self.assertIsNone(capture_report_receipt(a, b))
            with self.assertRaises(ReportCleanupError):
                delete_report_pair(None)
            self.assertTrue(a.exists())
            self.assertTrue(b.exists())

    def test_paired_unlink_failure_is_reported_not_silenced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.make_pair(Path(tmp))
            real_unlink = Path.unlink

            def failing_unlink(path, *args, **kwargs):
                if path == result.markdown_path:
                    raise PermissionError("synthetic second unlink denied")
                return real_unlink(path, *args, **kwargs)

            with patch("report_cleanup.Path.unlink", new=failing_unlink):
                with self.assertRaisesRegex(ReportCleanupError, "1/2"):
                    delete_report_pair(result.report_receipt)
            self.assertFalse(result.html_path.exists())
            self.assertTrue(result.markdown_path.exists())

    def test_deleted_pair_cannot_be_deleted_again(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.make_pair(Path(tmp))
            delete_report_pair(result.report_receipt)
            with self.assertRaises(ReportCleanupError):
                delete_report_pair(result.report_receipt)


if __name__ == "__main__":
    unittest.main()
