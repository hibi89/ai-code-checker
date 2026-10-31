"""Folder scan containment: no Windows junction dereference or silent walk loss.

All payloads are inert synthetic text in local temporary directories.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import code_input
from code_input import InputError, InputLimits, load_directory
from desktop_core import ScanRequest, inspect_input
from offline_core import scan_path
from offline_coverage import list_pruned_subtrees


class FolderBoundaryTests(unittest.TestCase):
    def test_oswalk_failure_is_not_silent_complete_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "project"
            folder.mkdir()
            (folder / "safe.py").write_text("pass\n", encoding="utf-8")

            def broken_walk(*args, **kwargs):
                kwargs["onerror"](PermissionError("synthetic unreadable folder"))
                yield ("", [], [])

            with patch("code_input.os.walk", side_effect=broken_walk):
                with self.assertRaisesRegex(InputError, "완전히 열거"):
                    load_directory(folder)

    def test_symlinked_subfolder_is_not_read_and_is_pruned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, outside = root / "project", root / "outside"
            project.mkdir()
            outside.mkdir()
            (project / "safe.py").write_text("print('SAFE')\n", encoding="utf-8")
            (outside / "outside.py").write_text("print('DO_NOT_SCAN_OUTSIDE')\n", encoding="utf-8")
            alias = project / "external"
            try:
                alias.symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Directory symlinks are not permitted on this host")
            bundle = load_directory(project)
            self.assertEqual([item.path for item in bundle.files], ["safe.py"])
            self.assertNotIn("DO_NOT_SCAN_OUTSIDE", bundle.render())
            self.assertIn("external/", list_pruned_subtrees(project, limits=InputLimits()))
            scan = scan_path(project)
            self.assertEqual([item.path for item in scan.bundle.files], ["safe.py"])
            self.assertIn("external/", scan.pruned_subtrees)

    @unittest.skipUnless(os.name == "nt", "Actual NTFS junction test requires Windows")
    def test_real_windows_junction_is_pruned_not_followed(self):
        with tempfile.TemporaryDirectory(prefix="checker-junction-") as tmp:
            root = Path(tmp)
            project, outside = root / "project", root / "outside"
            project.mkdir()
            outside.mkdir()
            (project / "safe.py").write_text("print('SAFE')\n", encoding="utf-8")
            (outside / "outside.py").write_text("print('DO_NOT_SCAN_OUTSIDE')\n", encoding="utf-8")
            junction = project / "junction"
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(junction), str(outside)],
                capture_output=True, text=True, errors="replace",
                timeout=15, check=False,
            )
            if result.returncode != 0:
                self.skipTest("Windows test host did not permit NTFS junction creation")
            self.assertTrue(junction.exists())
            self.assertTrue(code_input._is_linked_or_reparse(junction))
            bundle = load_directory(project)
            self.assertEqual([item.path for item in bundle.files], ["safe.py"])
            self.assertNotIn("DO_NOT_SCAN_OUTSIDE", bundle.render())
            preview = inspect_input(ScanRequest("path", source=str(project)))
            self.assertIn("junction/", preview.pruned_subtrees)
            self.assertEqual(preview.files, 1)
            scan = scan_path(project)
            self.assertEqual([item.path for item in scan.bundle.files], ["safe.py"])
            self.assertIn("junction/", scan.pruned_subtrees)


if __name__ == "__main__":
    unittest.main()
