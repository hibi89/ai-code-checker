"""P1-S: read-only, local historical report navigation contract (synthetic)."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from code_input import InputError
from desktop_core import ScanRequest, run_scan
from report_history import list_historical_reports, validate_historical_report


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

    def test_fake_report_cannot_insert_script_before_csp(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder, report = self.make_report(Path(tmp))
            original = report.html_path.read_bytes()
            self.assertIn(b"<head>", original)
            report.html_path.write_bytes(
                original.replace(b"<head>", b"<head><script>alert('synthetic')</script>", 1)
            )
            with self.assertRaises(InputError):
                validate_historical_report(folder, report.html_path)
            self.assertTrue(report.markdown_path.exists())

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


    def test_recent_list_orders_valid_pairs_and_skips_unrelated_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder, old = self.make_report(root, "older")
            _, new = self.make_report(root, "newer")
            os.utime(old.html_path, ns=(1_700_000_000_000_000_000,) * 2)
            os.utime(new.html_path, ns=(1_700_000_100_000_000_000,) * 2)
            (folder / "unrelated.html").write_text("<html>not ours</html>", encoding="utf-8")
            (folder / "unpaired.html").write_bytes(old.html_path.read_bytes())
            original = {
                path.name: path.read_bytes() for path in folder.iterdir() if path.is_file()
            }
            self.assertEqual(list_historical_reports(folder), (new.html_path, old.html_path))
            self.assertEqual(list_historical_reports(folder, limit=1), (new.html_path,))
            after = {
                path.name: path.read_bytes() for path in folder.iterdir() if path.is_file()
            }
            self.assertEqual(original, after)

    def test_recent_list_returns_empty_for_directory_without_valid_pairs(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "ordinary.html").write_text("<html>test</html>", encoding="utf-8")
            self.assertEqual(list_historical_reports(folder), ())

    def test_recent_list_never_trusts_stale_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder, report = self.make_report(Path(tmp))
            self.assertEqual(list_historical_reports(folder), (report.html_path,))
            report.html_path.write_text("<html>changed</html>", encoding="utf-8")
            with self.assertRaises(InputError):
                validate_historical_report(folder, report.html_path)

    def test_recent_list_excludes_symlink_and_hardlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder, report = self.make_report(root)
            os.link(report.html_path, root / "external-html-hardlink.html")
            self.assertEqual(list_historical_reports(folder), ())
            alias = folder / "alias.html"
            try:
                alias.symlink_to(report.html_path)
            except (NotImplementedError, OSError):
                pass
            else:
                self.assertEqual(list_historical_reports(folder), ())

    def test_recent_list_bounded_and_invalid_limit_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for bad in (0, 51, -1, True, 1.2, None):
                with self.subTest(limit=bad), self.assertRaises(ValueError):
                    list_historical_reports(folder, limit=bad)
            for i in range(513):
                (folder / f"extra-{i:03d}.html").write_bytes(b"x")
            with self.assertRaisesRegex(InputError, "512"):
                list_historical_reports(folder)

    def test_recent_list_rejects_invalid_or_remote_output_location(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            with self.assertRaises(InputError):
                list_historical_reports(folder / "missing")
            with self.assertRaises(InputError):
                list_historical_reports("//remote/share")


if __name__ == "__main__":
    unittest.main()
