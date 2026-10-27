"""P1-S: read-only, local historical report navigation contract (synthetic)."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from code_input import InputError
from desktop_core import ScanRequest, run_scan
from report_history import validate_historical_report


class HistoricalReportTests(unittest.TestCase):
    def make_report(self, root: Path, name: str = "code-checker-previous"):
        output = root / "한국어 결과"
        report = run_scan(
            ScanRequest("paste", text="eval('synthetic')\n", language="python"),
            output, name,
        )
        return output, report

    def test_existing_session_report_opens_after_new_process_style_lookup(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder, report = self.make_report(Path(tmp))
            old_html, old_md = report.html_path.read_bytes(), report.markdown_path.read_bytes()
            self.assertEqual(validate_historical_report(str(folder), str(report.html_path)), report.html_path)
            self.assertEqual(report.html_path.read_bytes(), old_html)
            self.assertEqual(report.markdown_path.read_bytes(), old_md)

    def test_custom_headless_report_basename_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder, report = self.make_report(Path(tmp), "my-result-20261027")
            self.assertEqual(validate_historical_report(folder, report.html_path), report.html_path)

    def test_selection_from_another_folder_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original, _ = self.make_report(root)
            other = root / "outside"
            _, outside = self.make_report(other)
            with self.assertRaises(InputError):
                validate_historical_report(original, outside.html_path)

    def test_missing_markdown_pair_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder, report = self.make_report(Path(tmp))
            report.markdown_path.unlink()
            with self.assertRaises(InputError):
                validate_historical_report(folder, report.html_path)
            self.assertTrue(report.html_path.exists())

    def test_html_or_markdown_header_tampering_denied(self):
        for extension, altered in (
            (".html", b"<html>not-a-report</html>"),
            (".md", b"# Unrelated file\n"),
        ):
            with self.subTest(extension=extension), tempfile.TemporaryDirectory() as tmp:
                folder, report = self.make_report(Path(tmp))
                path = report.html_path if extension == ".html" else report.markdown_path
                path.write_bytes(altered)
                with self.assertRaises(InputError):
                    validate_historical_report(folder, report.html_path)

    def test_report_symlink_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder, report = self.make_report(root)
            backup = folder / "backup.html"
            report.html_path.rename(backup)
            try:
                report.html_path.symlink_to(backup)
            except (NotImplementedError, OSError):
                self.skipTest("symlink unavailable without privileges")
            with self.assertRaises(InputError):
                validate_historical_report(folder, report.html_path)
            self.assertTrue(backup.exists())

    def test_hardlink_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder, report = self.make_report(root)
            alias = root / "second-link.html"
            os.link(report.html_path, alias)
            with self.assertRaises(InputError):
                validate_historical_report(folder, report.html_path)

    def test_empty_nonexistent_or_wrong_extension_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder, report = self.make_report(Path(tmp))
            for selected in ("", str(report.markdown_path), str(folder / "absent.html")):
                with self.subTest(selected=selected), self.assertRaises(InputError):
                    validate_historical_report(folder, selected)
            with self.assertRaises(InputError):
                validate_historical_report(folder / "missing", report.html_path)

    def test_do_not_open_network_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder, _ = self.make_report(Path(tmp))
            with self.assertRaises(InputError):
                validate_historical_report(folder, "//remote/share/something.html")

    def test_reader_does_not_create_reports_or_delete(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder, report = self.make_report(Path(tmp))
            before = {path.name: path.read_bytes() for path in folder.iterdir()}
            validate_historical_report(folder, report.html_path)
            after = {path.name: path.read_bytes() for path in folder.iterdir()}
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
