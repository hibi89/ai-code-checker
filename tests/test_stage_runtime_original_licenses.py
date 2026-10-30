"""Synthetic, local-only original license bytes and exact-EXE binding regressions."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.stage_runtime_original_licenses import stage_candidates


class FakePyInstaller:
    version = "6.22.3"

    def __init__(self, root: Path):
        self.root = root
        self.files = (Path("PyInstaller-6.22.3.dist-info/licenses/COPYING.txt"),)

    def locate_file(self, relative):
        return self.root / relative


class RuntimeOriginalLicenseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="cc-original-license-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.exe = self.root / "CodeCheckerOffline.exe"
        self.exe.write_bytes(b"MZ-synthetic-not-a-program")
        self.audit = {
            "format": "code_checker_p0d_frozen_archive_audit_v1",
            "exe_sha256": hashlib.sha256(self.exe.read_bytes()).hexdigest(),
            "customer_release_ready": False,
            "license_compliance_certified": False,
            "third_party_notice_ready_to_distribute": False,
        }
        self.runtime = self.root / "python-runtime"
        self.runtime.mkdir()
        (self.runtime / "LICENSE.txt").write_bytes(b"CPython original mock\r\n")
        for name, value in (("tcl8.6", b"tcl license\r\n"), ("tk8.6", b"tk license\n")):
            child = self.runtime / "tcl" / name
            child.mkdir(parents=True)
            (child / "license.terms").write_bytes(value)
        self.packages = self.root / "site-packages"
        license_file = self.packages / "PyInstaller-6.22.3.dist-info" / "licenses" / "COPYING.txt"
        license_file.parent.mkdir(parents=True)
        license_file.write_bytes(b"original PyInstaller COPYING bytes\r\n")
        self.dist = FakePyInstaller(self.packages)
        self.out = self.root / "staged-local-review"

    def test_exact_source_original_bytes_and_exe_hash_are_preserved(self):
        result = stage_candidates(self.exe, self.audit, self.runtime, self.dist, self.out)
        self.assertEqual(result["original_candidate_file_count"], 4)
        self.assertEqual(result["source_role_counts"], {
            "cpython": 1, "tcl": 1, "tk": 1, "pyinstaller": 1,
        })
        self.assertEqual(result["missing_source_roles"], [])
        self.assertEqual(result["exe_sha256"], self.audit["exe_sha256"])
        self.assertTrue(result["actual_exe_sha256_confirmed"])
        self.assertFalse(result["customer_notice_ready"])
        self.assertFalse(result["customer_release_ready"])
        self.assertFalse(result["copyright_and_redistribution_rights_verified"])
        persisted = json.loads((self.out / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(persisted["original_candidate_file_count"], 4)
        expected = {
            "cpython": b"CPython original mock\r\n",
            "tcl": b"tcl license\r\n",
            "tk": b"tk license\n",
            "pyinstaller": b"original PyInstaller COPYING bytes\r\n",
        }
        for row in result["originals"]:
            raw = (self.out / row["candidate_file"]).read_bytes()
            self.assertEqual(raw, expected[row["role"]])
            self.assertEqual(row["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertFalse(row["corresponding_frozen_entry_or_copyright_owner_verified"])
            self.assertTrue(row["human_review_required"])
        self.assertNotIn(str(self.root), repr(result))
        self.assertNotIn("CPython original mock", repr(result))

    def test_same_size_exe_tamper_is_rejected_before_writes(self):
        raw = self.exe.read_bytes()
        self.exe.write_bytes(raw.replace(b"synthetic", b"synThetic"))
        self.assertEqual(self.exe.stat().st_size, len(raw))
        with self.assertRaises(ValueError):
            stage_candidates(self.exe, self.audit, self.runtime, self.dist, self.out)
        self.assertFalse(self.out.exists())

    def test_forged_release_and_existing_output_fail_closed(self):
        for flag in ("customer_release_ready", "license_compliance_certified",
                     "third_party_notice_ready_to_distribute"):
            with self.subTest(flag=flag):
                audit = dict(self.audit)
                audit[flag] = True
                with self.assertRaises(ValueError):
                    stage_candidates(self.exe, audit, self.runtime, self.dist, self.out)
        self.assertFalse(self.out.exists())
        self.out.mkdir()
        sentinel = self.out / "keep.txt"
        sentinel.write_text("do not overwrite", encoding="utf-8")
        with self.assertRaises(ValueError):
            stage_candidates(self.exe, self.audit, self.runtime, self.dist, self.out)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "do not overwrite")

    def test_missing_tcl_and_tk_stay_unverified_not_silently_passed(self):
        for role in ("tcl8.6", "tk8.6"):
            (self.runtime / "tcl" / role / "license.terms").unlink()
        result = stage_candidates(self.exe, self.audit, self.runtime, self.dist, self.out)
        self.assertEqual(result["original_candidate_file_count"], 2)
        self.assertEqual(result["missing_source_roles"], ["tcl", "tk"])
        self.assertTrue(result["third_party_license_notice_human_review_required"])
        self.assertFalse(result["customer_notice_ready"])

    def test_alternate_lib_tcl_layout_recovers_original_tcl_license(self):
        """A Windows runtime may have tcl8.x below Lib rather than tcl."""
        original = self.runtime / "tcl" / "tcl8.6" / "license.terms"
        raw = original.read_bytes()
        original.unlink()
        alternate = self.runtime / "Lib" / "tcl8.6"
        alternate.mkdir(parents=True)
        (alternate / "license.terms").write_bytes(raw)
        result = stage_candidates(self.exe, self.audit, self.runtime, self.dist, self.out)
        self.assertEqual(result["source_role_counts"]["tcl"], 1)
        self.assertNotIn("tcl", result["missing_source_roles"])
        self.assertEqual(result["ambiguous_source_roles"], [])
        staged = next(row for row in result["originals"] if row["role"] == "tcl")
        self.assertEqual((self.out / staged["candidate_file"]).read_bytes(), raw)
        self.assertFalse(staged["corresponding_frozen_entry_or_copyright_owner_verified"])

    def test_conflicting_installed_tcl_licenses_fail_closed(self):
        alternate = self.runtime / "Lib" / "tcl8.6"
        alternate.mkdir(parents=True)
        (alternate / "license.terms").write_bytes(b"other Tcl release; not interchangeable")
        result = stage_candidates(self.exe, self.audit, self.runtime, self.dist, self.out)
        self.assertEqual(result["source_role_counts"]["tcl"], 0)
        self.assertIn("tcl", result["ambiguous_source_roles"])
        self.assertIn("tcl", result["missing_source_roles"])
        self.assertFalse(result["customer_notice_ready"])
        self.assertFalse(result["customer_release_ready"])

    def test_same_install_original_in_two_known_layouts_is_not_ambiguous(self):
        original = (self.runtime / "tcl" / "tcl8.6" / "license.terms").read_bytes()
        alternate = self.runtime / "Lib" / "tcl8.6"
        alternate.mkdir(parents=True)
        (alternate / "license.terms").write_bytes(original)
        result = stage_candidates(self.exe, self.audit, self.runtime, self.dist, self.out)
        self.assertEqual(result["source_role_counts"]["tcl"], 1)
        self.assertEqual(result["ambiguous_source_roles"], [])
        self.assertEqual(result["original_candidate_file_count"], 4)

    def test_linked_license_file_is_not_copied(self):
        target = self.root / "outside-license.txt"
        target.write_bytes(b"FAKE OUTSIDE SECRET")
        original = self.runtime / "LICENSE.txt"
        original.unlink()
        try:
            original.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink creation unavailable")
        result = stage_candidates(self.exe, self.audit, self.runtime, self.dist, self.out)
        self.assertIn("cpython", result["missing_source_roles"])
        for row in result["originals"]:
            self.assertNotEqual((self.out / row["candidate_file"]).read_bytes(),
                                target.read_bytes())

    def test_output_in_installed_runtime_tree_is_refused(self):
        out = self.runtime / "staging-not-allowed"
        with self.assertRaises(ValueError):
            stage_candidates(self.exe, self.audit, self.runtime, self.dist, out)
        self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
