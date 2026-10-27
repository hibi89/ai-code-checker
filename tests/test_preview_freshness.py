"""P1-R: preview-to-scan freshness for bounded synthetic local sources."""
from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from code_input import InputError
from desktop_core import ScanRequest, inspect_input, run_scan


class PreviewFreshnessTests(unittest.TestCase):
    def test_unchanged_file_preview_scans_without_changing_original(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "sample.py"
            path.write_text("eval(value)\n", encoding="utf-8")
            original = path.read_bytes()
            request = ScanRequest("path", source=str(path))
            before = inspect_input(request)
            self.assertEqual(len(before.fingerprint), 64)
            self.assertNotIn(before.fingerprint, before.display())
            result = run_scan(
                request, root / "reports", "unchanged",
                expected_preview_fingerprint=before.fingerprint,
            )
            self.assertEqual(result.status, "complete")
            self.assertTrue(result.html_path.is_file())
            self.assertEqual(path.read_bytes(), original)

    def test_same_size_file_change_blocks_before_report_creation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "sample.py"
            source.write_text("eval(value)\n", encoding="utf-8")
            request = ScanRequest("path", source=str(source))
            fingerprint = inspect_input(request).fingerprint
            source.write_text("exec(value)\n", encoding="utf-8")
            output = root / "reports"
            with self.assertRaisesRegex(InputError, "다시 미리보기"):
                run_scan(
                    request, output, "outdated",
                    expected_preview_fingerprint=fingerprint,
                )
            self.assertFalse(output.exists())
            self.assertEqual(source.read_text(encoding="utf-8"), "exec(value)\n")

    def test_folder_added_and_removed_files_change_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            project.mkdir()
            (project / "a.py").write_text("print('ok')\n", encoding="utf-8")
            request = ScanRequest("path", source=str(project))
            fingerprint = inspect_input(request).fingerprint
            extra = project / "b.py"
            extra.write_text("print('another')\n", encoding="utf-8")
            self.assertNotEqual(fingerprint, inspect_input(request).fingerprint)
            with self.assertRaises(InputError):
                run_scan(
                    request, root / "reports", "added",
                    expected_preview_fingerprint=fingerprint,
                )
            extra.unlink()
            self.assertEqual(fingerprint, inspect_input(request).fingerprint)

    def test_excluded_folder_list_change_invalidates_preview(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            project.mkdir()
            (project / "a.py").write_text("print('ok')\n", encoding="utf-8")
            request = ScanRequest("path", source=str(project))
            original = inspect_input(request)
            ignored = project / "node_modules"
            ignored.mkdir()
            (ignored / "private.py").write_text("ignored", encoding="utf-8")
            modified = inspect_input(request)
            self.assertNotEqual(original.fingerprint, modified.fingerprint)
            with self.assertRaises(InputError):
                run_scan(
                    request, root / "reports", "pruned",
                    expected_preview_fingerprint=original.fingerprint,
                )

    def test_archive_change_detected_before_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "source.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("code.py", "eval(value)\n")
            request = ScanRequest("path", source=str(archive))
            fingerprint = inspect_input(request).fingerprint
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("code.py", "exec(value)\n")
            with self.assertRaises(InputError):
                run_scan(
                    request, root / "reports", "zip",
                    expected_preview_fingerprint=fingerprint,
                )

    def test_multi_txt_changed_section_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "combined.txt"
            path.write_text(
                "===== FILE: src/main.py =====\neval(value)\n"
                "===== FILE: README.md =====\nHello\n",
                encoding="utf-8",
            )
            request = ScanRequest("path", source=str(path))
            initial = inspect_input(request)
            self.assertEqual(initial.kind, "multi-txt")
            path.write_text(
                "===== FILE: src/main.py =====\nexec(value)\n"
                "===== FILE: README.md =====\nHello\n",
                encoding="utf-8",
            )
            with self.assertRaises(InputError):
                run_scan(
                    request, root / "reports", "multi",
                    expected_preview_fingerprint=initial.fingerprint,
                )

    def test_default_headless_scan_remains_backward_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            request = ScanRequest("paste", text="eval(value)\n", language="python")
            result = run_scan(request, Path(tmp) / "reports", "direct")
            self.assertEqual(result.findings, 1)
            self.assertTrue(result.markdown_path.exists())

    def test_invalid_preview_token_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            request = ScanRequest("paste", text="print('ok')\n", language="python")
            output = Path(tmp) / "reports"
            with self.assertRaisesRegex(InputError, "미리보기"):
                run_scan(request, output, "invalid", expected_preview_fingerprint="")
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
