"""Synthetic output path privacy boundaries; never uses client data or internet."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from code_input import InputError
from desktop_core import ScanRequest, run_scan
from offline_core import scan_text
from offline_report import build_report, write_report
from output_safety import _windows_drive_type, validate_output_location


class OutputPathSafetyTests(unittest.TestCase):
    def test_known_cloud_synced_reports_are_refused_before_source_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for folder in ("OneDrive", "OneDrive - Contoso", "Dropbox", "Google Drive",
                           "iCloudDrive", "iCloud Drive"):
                with self.subTest(folder=folder):
                    target = root / folder / "reports"
                    with patch("desktop_core.scan_text", side_effect=AssertionError("source read")):
                        with self.assertRaisesRegex(InputError, "동기화"):
                            run_scan(
                                ScanRequest("paste", text="print('fixture')\n", language="python"),
                                target, "blocked",
                            )
                    self.assertFalse(target.exists())

    def test_windows_onedrive_env_root_prevents_reports_even_under_custom_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "My Custom Files"
            destination = root / "reports"
            for key in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
                with self.subTest(key=key):
                    with patch.dict(os.environ, {key: str(root)}, clear=True):
                        with self.assertRaisesRegex(InputError, "OneDrive"):
                            validate_output_location(destination)
                    self.assertFalse(destination.exists())

    def test_similar_names_and_adjacent_folders_still_work(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            candidate = root / "OneDrive-LocalNotSynced" / "reports"
            real_sync = root / "OneDrive"
            with patch.dict(os.environ, {"OneDrive": str(real_sync)}, clear=True):
                self.assertEqual(validate_output_location(candidate), candidate)
                report = build_report(scan_text("print('safe')\n", filename="main.py"))
                html, md = write_report(report, candidate, name="new-report")
                self.assertTrue(html.is_file())
                self.assertTrue(md.is_file())

    def test_direct_report_writer_blocks_cloud_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "Google Drive" / "reports"
            report = build_report(scan_text("eval('synthetic')\n", filename="fixture.py"))
            with self.assertRaisesRegex(InputError, "동기화"):
                write_report(report, destination, name="must-not-write")
            self.assertFalse(destination.exists())

    def test_folder_scan_refuses_same_root_before_reading(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            project.mkdir()
            source = project / "main.py"
            source.write_text("eval('1')\n", encoding="utf-8")
            before = source.read_bytes()
            with patch("desktop_core.scan_path", side_effect=AssertionError("source read")):
                with self.assertRaises(InputError):
                    run_scan(ScanRequest("path", source=str(project)), project, "must-not-write")
            self.assertEqual(source.read_bytes(), before)
            self.assertFalse((project / "must-not-write.html").exists())

    def test_folder_scan_refuses_nested_output_even_if_not_existing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            project.mkdir()
            (project / "main.py").write_text("pass\n", encoding="utf-8")
            destination = project / "generated" / "reports"
            with self.assertRaises(InputError):
                run_scan(ScanRequest("path", source=str(project)), destination, "no-write")
            self.assertFalse(destination.exists())

    def test_folder_scan_accepts_sibling_output_and_retains_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / "프로젝트"
            project.mkdir()
            source = project / "main.py"
            source.write_text("eval('1')\n", encoding="utf-8")
            before = source.read_bytes()
            result = run_scan(
                ScanRequest("path", source=str(project)), root / "검사결과", "safe-run"
            )
            self.assertEqual(result.status, "complete")
            self.assertTrue(result.html_path.is_file())
            self.assertTrue(result.markdown_path.is_file())
            self.assertEqual(source.read_bytes(), before)

    def test_symlink_component_blocks_output_without_writing_to_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            target.mkdir()
            alias = root / "alias"
            try:
                alias.symlink_to(target, target_is_directory=True)
            except (NotImplementedError, OSError):
                self.skipTest("creating directory symlinks unsupported")
            with self.assertRaises(InputError):
                run_scan(ScanRequest("paste", text="pass\n", language="python"),
                         alias / "reports", "blocked")
            self.assertEqual(list(target.iterdir()), [])

    def test_unsafe_network_style_paths_rejected(self) -> None:
        for path in (r"\\server\share\client-reports", "//server/share/client-reports", ""):
            with self.subTest(path=path):
                with self.assertRaises(InputError):
                    validate_output_location(path)

    def test_mapped_remote_drive_is_blocked_before_any_scan(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "remote-reports"
            with patch("output_safety._windows_drive_type", return_value=4):
                with patch("desktop_core.scan_text", side_effect=AssertionError("source read")):
                    with self.assertRaisesRegex(InputError, "네트워크 연결"):
                        run_scan(
                            ScanRequest("paste", text="print('synthetic')\n", language="python"),
                            dest, "blocked-network-drive",
                        )
            self.assertFalse(dest.exists())

    def test_unknown_or_unwritable_windows_drive_types_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "reports"
            for kind in (0, 1, 4, 5):
                with self.subTest(kind=kind):
                    with patch("output_safety._windows_drive_type", return_value=kind):
                        with self.assertRaises(InputError):
                            validate_output_location(dest)
                    self.assertFalse(dest.exists())

    def test_fixed_removable_and_ram_local_drive_types_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "reports"
            for kind in (2, 3, 6):
                with self.subTest(kind=kind):
                    with patch("output_safety._windows_drive_type", return_value=kind):
                        self.assertEqual(validate_output_location(dest), dest)
            self.assertFalse(dest.exists())

    def test_failed_drive_type_probe_fails_closed_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "reports"
            with patch("output_safety._windows_drive_type", side_effect=OSError("synthetic")):
                with self.assertRaises(InputError):
                    validate_output_location(dest)
            self.assertFalse(dest.exists())

    @unittest.skipUnless(os.name == "nt", "GetDriveTypeW is Windows-only")
    def test_real_windows_temporary_drive_is_local(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            observed = _windows_drive_type(Path(temp))
            self.assertIn(observed, (2, 3, 6))
            self.assertEqual(validate_output_location(Path(temp)), Path(temp))

    def test_existing_file_cannot_be_target_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "existing_file"
            dest.write_text("leave untouched", encoding="utf-8")
            with self.assertRaises(InputError):
                run_scan(ScanRequest("paste", text="pass\n", language="python"),
                         dest, "blocked")
            self.assertEqual(dest.read_text(encoding="utf-8"), "leave untouched")

    def test_report_writer_itself_refuses_linked_output_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            target.mkdir()
            alias = root / "reports-alias"
            try:
                alias.symlink_to(target, target_is_directory=True)
            except (NotImplementedError, OSError):
                self.skipTest("symlinks unsupported")
            report = build_report(scan_text("eval('1')\n", filename="main.py"))
            with self.assertRaises(InputError):
                write_report(report, alias, name="blocked")
            self.assertEqual(list(target.iterdir()), [])

    def test_default_nonlinked_report_writer_remains_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "results"
            report = build_report(scan_text("print('ok')\n", filename="main.py"))
            html, markdown = write_report(report, folder, name="한국어보고서")
            self.assertEqual(html.parent, folder)
            self.assertTrue(html.is_file())
            self.assertTrue(markdown.is_file())
            with self.assertRaises(FileExistsError):
                write_report(report, folder, name="한국어보고서")


if __name__ == "__main__":
    unittest.main()
