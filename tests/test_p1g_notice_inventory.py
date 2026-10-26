"""Pure standard library tests for license audit / research wrapper boundaries."""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import p1g_notice_inventory as target
from scripts import p1g_native_exe_entry as exe


class OriginalLicenseAuditTests(unittest.TestCase):
    def test_mit_original_text_markers(self):
        sample = (b"Copyright 2026 Sample Author\n"
                  b"Permission is hereby granted, free of charge, to any person obtaining a "
                  b"copy of this software to deal in the Software without restriction.\n")
        self.assertTrue(target._license_text_ok(sample))
        self.assertFalse(target._license_text_ok(b"MIT"))
        self.assertFalse(target._license_text_ok(sample + b"\x00"))

    def test_matching_license_filename_only(self):
        self.assertTrue(target._matching_file("pkg-1.dist-info/licenses/LICENSE"))
        self.assertTrue(target._matching_file("pkg-1.dist-info/NOTICE.txt"))
        self.assertFalse(target._matching_file("pkg-1.dist-info/metadata"))
        self.assertFalse(target._matching_file("src/lICENSE_UNRELATED.py"))

    def test_inventory_reads_original_files_and_reports_no_approval(self):
        mit = (b"Copyright 2026 Example\nPermission is hereby granted, free of charge, "
               b"to any person obtaining this Software without restriction\n")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            license_file = root / "LICENSE"
            license_file.write_bytes(mit)

            class Distribution:
                version = "any"
                files = ("dist-info/licenses/LICENSE",)
                def locate_file(self, name):
                    self.seen = name
                    return license_file

            dist = Distribution()
            def resolve(name):
                dist.version = target.PINNED[name]
                return dist

            with patch.object(target.metadata, "distribution", side_effect=resolve):
                report = target.inventory()
        self.assertEqual(report["packages_evaluated"], 3)
        self.assertFalse(report["dependency_chain_notice_approved"])
        self.assertFalse(report["customer_release_ready"])
        self.assertEqual(
            report["packages"]["tree-sitter"]["original_installed_license_files_read"], 1)

    def test_missing_original_license_fails(self):
        class Dist:
            version = target.PINNED["tree-sitter"]
            files = ()
        with patch.object(target.metadata, "distribution", return_value=Dist()):
            with self.assertRaisesRegex(AssertionError, "LICENSE file absent"):
                target.inventory()

    def test_baseline_entrypoint_never_calls_parser(self):
        with patch.object(exe.sys, "argv", ["probe", "--baseline"]), patch.object(
            exe.importlib, "import_module",
            side_effect=AssertionError("unexpected parser import"),
        ):
            self.assertEqual(exe.main(), 0)


if __name__ == "__main__":
    unittest.main()
