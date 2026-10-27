"""Synthetic offline v2 input locality privacy regressions.

Tests never open remote mounts or upload/execute customer source. Mocked Windows
drive observations check rejection before the code loader is invoked.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from code_input import InputError
from desktop_core import ScanRequest, inspect_input, run_scan
from input_safety import validate_offline_input_path
from offline_core import scan_path


class OfflineInputSafetyTests(unittest.TestCase):
    def test_unc_and_device_paths_rejected_before_filesystem_lookup(self):
        for source in (r"\\server\share\project", "//server/share/code.py",
                       r"\\?\C:\project", ""):
            with self.subTest(source=source):
                with patch("input_safety._windows_drive_type",
                           side_effect=AssertionError("remote lookup attempted")):
                    with self.assertRaises(InputError):
                        validate_offline_input_path(source)

    def test_drive_letter_mapped_remote_rejected_before_gui_preview_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "client.py"
            source.write_text("print('private fixture')", encoding="utf-8")
            with patch("input_safety._windows_drive_type", return_value=4):
                with patch("desktop_core.load_path", side_effect=AssertionError("source opened")):
                    with self.assertRaisesRegex(InputError, "네트워크 연결"):
                        inspect_input(ScanRequest("path", source=str(source)))
            self.assertEqual(source.read_text(encoding="utf-8"), "print('private fixture')")

    def test_remote_input_denied_before_output_preflight_or_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            (project / "test.py").write_text("eval('1')\n", encoding="utf-8")
            target = Path(tmp) / "results"
            with patch("input_safety._windows_drive_type", return_value=4):
                with patch("desktop_core.scan_path", side_effect=AssertionError("source opened")):
                    with self.assertRaises(InputError):
                        run_scan(ScanRequest("path", source=str(project)),
                                 target, "must-not-write")
            self.assertFalse(target.exists())

    def test_cli_scan_path_directly_enforces_locality(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source.py"
            path.write_text("pass\n", encoding="utf-8")
            with patch("input_safety._windows_drive_type", return_value=4):
                with patch("offline_core.load_path", side_effect=AssertionError("source opened")):
                    with self.assertRaises(InputError):
                        scan_path(path)

    def test_unknown_drive_types_and_failed_lookup_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "code.py"
            for code in (0, 1, 4, 5):
                with self.subTest(code=code):
                    with patch("input_safety._windows_drive_type", return_value=code):
                        with self.assertRaises(InputError):
                            validate_offline_input_path(path)
            with patch("input_safety._windows_drive_type", side_effect=OSError("drive not found")):
                with self.assertRaises(InputError):
                    validate_offline_input_path(path)

    def test_supported_local_drive_types_have_no_input_side_effect(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "한글.py"
            file.write_text("print('safe')\n", encoding="utf-8")
            for code in (2, 3, 6):
                with self.subTest(code=code):
                    with patch("input_safety._windows_drive_type", return_value=code):
                        self.assertEqual(validate_offline_input_path(file), file)
            self.assertEqual(file.read_text(encoding="utf-8"), "print('safe')\n")

    def test_directory_alias_or_parent_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real = root / "real"
            real.mkdir()
            (real / "file.py").write_text("print('safe')\n", encoding="utf-8")
            link = root / "alias"
            try:
                link.symlink_to(real, target_is_directory=True)
            except (NotImplementedError, OSError):
                self.skipTest("symlink creation unavailable")
            for source in (link, link / "file.py"):
                with self.subTest(source=source):
                    with self.assertRaises(InputError):
                        validate_offline_input_path(source)

    def test_valid_local_python_single_file_works_in_preview_and_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.py"
            source.write_text("eval('1')\n", encoding="utf-8")
            preview = inspect_input(ScanRequest("path", source=str(source)))
            self.assertEqual(preview.files, 1)
            result = run_scan(ScanRequest("path", source=str(source)), root / "out", "report")
            self.assertEqual(result.status, "complete")
            self.assertGreaterEqual(result.findings, 1)
            self.assertTrue(result.html_path.is_file())
            self.assertEqual(source.read_text(encoding="utf-8"), "eval('1')\n")

    def test_legacy_code_input_loader_is_not_modified(self):
        # This module guards offline v2 entry points; v1 loader is not patched.
        from code_input import load_path
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "legacy.py"
            source.write_text("print('legacy')\n", encoding="utf-8")
            bundle = load_path(source)
            self.assertEqual(len(bundle.files), 1)

    @unittest.skipUnless(os.name == "nt", "Windows GetDriveTypeW only")
    def test_real_windows_local_input_drive_type(self):
        from output_safety import _windows_drive_type
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.py"
            path.write_text("pass\n", encoding="utf-8")
            self.assertIn(_windows_drive_type(path), (2, 3, 6))
            self.assertEqual(validate_offline_input_path(path), path)


if __name__ == "__main__":
    unittest.main()
