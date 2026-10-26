"""Synthetic archive TOC tests. Never build or run an arbitrary executable."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.audit_frozen_exe import build_audit, inspect_archive, sha256_file


class _FakePYZ:
    toc = {"alpha": (0, 1, 8), "package.module": (0, 5, 10)}


class _FakeArchive:
    toc = {
        "PYZ.pyz": (0, 100, 200, 0, "z"),
        "python313.dll": (100, 500, 600, 1, "b"),
        "tcl86t.dll": (600, 50, 60, 1, "b"),
        "tk86t.dll": (660, 50, 60, 1, "b"),
        "main": (720, 10, 10, 0, "s"),
    }

    def open_embedded_archive(self, name):
        if name != "PYZ.pyz":
            raise ValueError("Unexpected archive")
        return _FakePYZ()


class ArchiveAuditorTests(unittest.TestCase):
    def test_manifest_realistic_nested_python_and_windows_dll(self):
        info = inspect_archive(_FakeArchive())
        self.assertEqual(info["top_level_count"], 5)
        self.assertEqual(info["pyz_module_count"], 2)
        self.assertTrue(info["framework_markers"]["python_runtime"])
        self.assertTrue(info["framework_markers"]["tcl_or_tk"])
        self.assertEqual(info["archive_read_errors"], [])
        self.assertTrue(info["no_bundle_entry_extracted_or_executed"])

    def test_missing_python_archive_fails_audit(self):
        class Missing:
            toc = {"python313.dll": (1, 10, 10, 0, "b")}
        info = inspect_archive(Missing())
        self.assertTrue(info["archive_read_errors"])
        self.assertEqual(info["pyz_module_count"], 0)

    def test_invalid_archive_entry_blocks_without_exec(self):
        class Malformed:
            toc = {"PYZ.pyz": (0, 1, 2, "z")}
        with self.assertRaises(ValueError):
            inspect_archive(Malformed())

    def test_license_notices_are_never_marked_certified(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / "fake.exe"
            exe.write_bytes(b"SYNTHETIC archive wrapper only")
            with patch("scripts.audit_frozen_exe.gather_installed_license_evidence",
                       return_value=[{
                           "name": "example", "version": "1",
                           "license_metadata": "MIT",
                           "license_files_in_installed_distribution": [],
                           "embedded_in_exe_not_individually_verified": True,
                       }]):
                result = build_audit(exe, _FakeArchive(), root_versions={"example": "1"})
            self.assertEqual(result["exe_sha256"], sha256_file(exe))
            self.assertEqual(result["status"], "BINARY_MANIFEST_OBSERVED_LICENSE_REVIEW_REQUIRED")
            self.assertFalse(result["license_compliance_certified"])
            self.assertFalse(result["third_party_notice_ready_to_distribute"])
            self.assertFalse(result["customer_release_ready"])


if __name__ == "__main__":
    unittest.main()
