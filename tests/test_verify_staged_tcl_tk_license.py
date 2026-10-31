"""No network or customer files: staged Tcl/Tk source provenance gate tests."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import verify_staged_tcl_tk_license as target
from scripts import verify_upstream_tcl_tk_license as upstream


class StagedLicenseTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.exe = self.root / "synthetic.exe"
        self.exe.write_bytes(b"MZ synthetic codechecker")
        self.staged = self.root / "runtime-originals"
        self.staged.mkdir()
        self.sources = {"tcl": b"Tcl exact original\r\n", "tk": b"Tk exact original\n"}
        rows = []
        for role, raw in self.sources.items():
            name = role + "-01.original"
            (self.staged / name).write_bytes(raw)
            rows.append({
                "role": role, "candidate_file": name, "installed_source_basename": "license.terms",
                "source_kind": "installed_python_runtime_tree", "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "human_review_required": True,
                "corresponding_frozen_entry_or_copyright_owner_verified": False,
            })
        self.receipt = {
            "format": upstream.RECEIPT_FORMAT,
            "exe_sha256": hashlib.sha256(self.exe.read_bytes()).hexdigest(),
            "exe_bytes": self.exe.stat().st_size,
            "frozen_process_runtime_observed": True,
            "python_runtime_version": "3.13.9",
            "tcl_runtime_patchlevel": "8.6.15", "tk_runtime_patchlevel": "8.6.15",
            **{key: False for key in upstream.BLOCKED},
        }
        self.manifest = {
            "format": target.FORMAT,
            "exe_sha256": self.receipt["exe_sha256"],
            "exe_bytes": self.receipt["exe_bytes"],
            "frozen_tcl_tk_runtime_receipt_verified": True,
            "frozen_tcl_patchlevel": "8.6.15", "frozen_tk_patchlevel": "8.6.15",
            "source_role_counts": {"cpython": 0, "tcl": 1, "tk": 1, "pyinstaller": 0},
            "original_candidate_file_count": 2,
            "originals": rows,
            "missing_source_roles": ["cpython", "pyinstaller"],
            "ambiguous_source_roles": [],
            "actual_exe_sha256_confirmed": True,
            "customer_release_ready": False,
            "customer_notice_ready": False,
            "copyright_and_redistribution_rights_verified": False,
        }
        self.pinned = {
            role: {"8.6.15": ("core-8-6-15", upstream.git_blob_id(raw))}
            for role, raw in self.sources.items()
        }
        self.refresh()

    def refresh(self):
        (self.staged / "manifest.json").write_text(
            json.dumps(self.manifest), encoding="utf-8")

    def verify(self):
        with patch.object(upstream, "PINNED", self.pinned):
            return target.verify_staged(self.exe, self.receipt, self.staged)

    def test_source_matches_are_exe_bound_and_not_redistribution_approval(self):
        result = self.verify()
        self.assertEqual(result["exe_sha256"], self.receipt["exe_sha256"])
        self.assertEqual([r["component"] for r in result["source_originals"]], ["tcl", "tk"])
        self.assertTrue(result["staged_installed_source_hashes_verified"])
        self.assertFalse(result["installed_source_binary_copyright_owner_verified"])
        self.assertFalse(result["customer_release_ready"])
        self.assertFalse(result["license_compliance_certified"])
        self.assertNotIn(str(self.root), repr(result))
        self.assertNotIn("Tcl exact original", repr(result))

    def test_missing_or_conflicting_source_roles_fail_closed(self):
        for name, value in (
            ("missing", ["tcl"]), ("ambiguous", ["tk"]),
        ):
            with self.subTest(name=name):
                if name == "missing":
                    self.manifest["missing_source_roles"] = value
                else:
                    self.manifest["ambiguous_source_roles"] = value
                self.refresh()
                with self.assertRaises(ValueError):
                    self.verify()
                self.manifest["missing_source_roles"] = ["cpython", "pyinstaller"]
                self.manifest["ambiguous_source_roles"] = []

    def test_missing_source_no_approval_and_still_checks_present_tk_bytes(self):
        self.manifest["source_role_counts"]["tcl"] = 0
        self.manifest["original_candidate_file_count"] = 1
        self.manifest["originals"] = [self.manifest["originals"][1]]
        self.manifest["missing_source_roles"] = ["cpython", "pyinstaller", "tcl"]
        self.refresh()
        report = self.verify()
        self.assertEqual(report["missing_or_ambiguous_roles"], ["tcl"])
        self.assertEqual(report["status"], "MISSING_INSTALLED_SOURCE_REVIEW_REQUIRED")
        self.assertFalse(report["source_equality_verified"])
        self.assertFalse(report["customer_release_ready"])
        self.assertNotIn("source_originals", report)
        self.assertEqual(report["available_source_count"], 1)
        tk = report["available_installed_source_originals"][0]
        self.assertEqual(tk["component"], "tk")
        self.assertTrue(tk["upstream_original_bytes_match"])
        self.assertTrue(tk["lf_normalized_upstream_blob_match"])
        self.assertFalse(tk["line_endings_only_difference"])
        self.assertEqual(tk["upstream_license_git_blob_sha1"],
                         upstream.git_blob_id(self.sources["tk"]))
        self.assertTrue(report["available_upstream_original_bytes_match"])
        self.assertFalse(tk["exact_bundled_binary_owner_verified"])
        self.assertNotIn(str(self.root), repr(report))
        self.staged.joinpath("tk-01.original").write_bytes(b"changed text")
        with self.assertRaises(ValueError):
            self.verify()

    def test_installed_tk_mismatch_is_visible_even_if_staged_manifest_is_consistent(self):
        self.manifest["source_role_counts"]["tcl"] = 0
        self.manifest["original_candidate_file_count"] = 1
        self.manifest["originals"] = [self.manifest["originals"][1]]
        self.manifest["missing_source_roles"] = ["cpython", "pyinstaller", "tcl"]
        modified = b"Tk locally modified license terms\\n"
        (self.staged / "tk-01.original").write_bytes(modified)
        self.manifest["originals"][0]["sha256"] = hashlib.sha256(modified).hexdigest()
        self.manifest["originals"][0]["bytes"] = len(modified)
        self.refresh()
        result = self.verify()
        self.assertEqual(result["status"], "MISSING_INSTALLED_SOURCE_REVIEW_REQUIRED")
        self.assertFalse(result["available_installed_source_originals"][0]["upstream_original_bytes_match"])
        self.assertFalse(result["available_installed_source_originals"][0]["lf_normalized_upstream_blob_match"])
        self.assertFalse(result["available_installed_source_originals"][0]["line_endings_only_difference"])
        self.assertFalse(result["available_upstream_original_bytes_match"])
        self.assertFalse(result["customer_release_ready"])

    def test_tk_upstream_mismatch_is_explained_only_by_line_endings_when_proven(self):
        self.manifest["source_role_counts"]["tcl"] = 0
        self.manifest["original_candidate_file_count"] = 1
        self.manifest["originals"] = [self.manifest["originals"][1]]
        self.manifest["missing_source_roles"] = ["cpython", "pyinstaller", "tcl"]
        changed = self.sources["tk"].replace(b"\n", b"\r\n")
        (self.staged / "tk-01.original").write_bytes(changed)
        self.manifest["originals"][0]["sha256"] = hashlib.sha256(changed).hexdigest()
        self.manifest["originals"][0]["bytes"] = len(changed)
        self.refresh()
        report = self.verify()
        tk = report["available_installed_source_originals"][0]
        self.assertFalse(tk["upstream_original_bytes_match"])
        self.assertTrue(tk["lf_normalized_upstream_blob_match"])
        self.assertTrue(tk["line_endings_only_difference"])
        self.assertFalse(report["source_equality_verified"])
        self.assertFalse(report["customer_release_ready"])

    def test_unknown_installed_tk_version_does_not_claim_upstream_match(self):
        self.manifest["source_role_counts"]["tcl"] = 0
        self.manifest["original_candidate_file_count"] = 1
        self.manifest["originals"] = [self.manifest["originals"][1]]
        self.manifest["missing_source_roles"] = ["cpython", "pyinstaller", "tcl"]
        self.receipt["tk_runtime_patchlevel"] = "8.6.99"
        self.manifest["frozen_tk_patchlevel"] = "8.6.99"
        self.refresh()
        result = self.verify()
        item = result["available_installed_source_originals"][0]
        self.assertIsNone(item["upstream_license_git_blob_sha1"])
        self.assertFalse(item["upstream_original_bytes_match"])
        self.assertFalse(item["lf_normalized_upstream_blob_match"])
        self.assertFalse(item["line_endings_only_difference"])
        self.assertFalse(result["customer_release_ready"])

    def test_missing_source_does_not_skip_exact_exe_receipt_verification(self):
        self.manifest["source_role_counts"]["tcl"] = 0
        self.manifest["original_candidate_file_count"] = 1
        self.manifest["originals"] = [self.manifest["originals"][1]]
        self.manifest["missing_source_roles"] = ["cpython", "pyinstaller", "tcl"]
        self.refresh()
        self.exe.write_bytes(b"same name but different exact EXE")
        with self.assertRaises(ValueError):
            self.verify()

    def test_staged_original_tampering_and_wrong_manifest_digest_fail(self):
        raw = self.sources["tcl"]
        (self.staged / "tcl-01.original").write_bytes(b"X" * len(raw))
        with self.assertRaises(ValueError):
            self.verify()
        (self.staged / "tcl-01.original").write_bytes(raw)
        self.manifest["originals"][0]["sha256"] = "0" * 64
        self.refresh()
        with self.assertRaises(ValueError):
            self.verify()

    def test_wrong_receipt_exe_hash_and_runtime_version_fail(self):
        self.exe.write_bytes(b"MZ different executable")
        with self.assertRaises(ValueError):
            self.verify()
        self.exe.write_bytes(b"MZ synthetic codechecker")
        self.receipt["tk_runtime_patchlevel"] = "8.6.99"
        with self.assertRaises(ValueError):
            self.verify()

    def test_manifest_must_not_preapprove_redistribution(self):
        for key in ("customer_release_ready", "customer_notice_ready",
                    "copyright_and_redistribution_rights_verified"):
            with self.subTest(key=key):
                self.manifest[key] = True
                self.refresh()
                with self.assertRaises(ValueError):
                    self.verify()
                self.manifest[key] = False

    def test_unexpected_role_source_or_path_is_rejected(self):
        for key, bad in (
            ("candidate_file", "../outside.terms"),
            ("source_kind", "untrusted_download"),
            ("human_review_required", False),
            ("corresponding_frozen_entry_or_copyright_owner_verified", True),
        ):
            with self.subTest(key=key):
                original = self.manifest["originals"][0][key]
                self.manifest["originals"][0][key] = bad
                self.refresh()
                with self.assertRaises(ValueError):
                    self.verify()
                self.manifest["originals"][0][key] = original

    def test_symlinked_staged_folder_is_refused(self):
        alias = self.root / "alias"
        try:
            alias.symlink_to(self.staged, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlink unsupported")
        with self.assertRaises(ValueError):
            target.verify_staged(self.exe, self.receipt, alias)

    def test_existing_receipt_is_never_overwritten(self):
        receipt = self.root / "receipt.json"
        receipt.write_text(json.dumps(self.receipt), encoding="utf-8")
        out = self.root / "result.json"
        out.write_text("preserve", encoding="utf-8")
        with patch.object(upstream, "PINNED", self.pinned):
            rc = target.main(["--exe", str(self.exe),
                              "--runtime-receipt", str(receipt),
                              "--staged-dir", str(self.staged),
                              "--out", str(out)])
        self.assertEqual(rc, 1)
        self.assertEqual(out.read_text(encoding="utf-8"), "preserve")


if __name__ == "__main__":
    unittest.main()
