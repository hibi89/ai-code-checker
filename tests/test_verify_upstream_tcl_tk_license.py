"""Offline synthetic tests for exact upstream Tcl/Tk license blobs."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import verify_upstream_tcl_tk_license as target


class TaggedUpstreamLicenseTests(unittest.TestCase):
    def setUp(self):
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.root = Path(holder.name)
        self.exe = self.root / "CodeCheckerOffline.exe"
        self.exe.write_bytes(b"MZ-only-synthetic-not-an-executable")
        self.tcl = b"synthetic-tcl-license-original"
        self.tk = b"synthetic-tk-license-original"
        self.tcl_path = self.root / "tcl-license.terms"
        self.tk_path = self.root / "tk-license.terms"
        self.tcl_path.write_bytes(self.tcl)
        self.tk_path.write_bytes(self.tk)
        self.originals = {
            "tcl": {"8.6.15": ("core-8-6-15", target.git_blob_id(self.tcl))},
            "tk": {"8.6.15": ("core-8-6-15", target.git_blob_id(self.tk))},
        }
        self.receipt = {
            "format": target.RECEIPT_FORMAT,
            "exe_sha256": hashlib.sha256(self.exe.read_bytes()).hexdigest(),
            "exe_bytes": self.exe.stat().st_size,
            "frozen_process_runtime_observed": True,
            "python_runtime_version": "3.13.9",
            "tcl_runtime_patchlevel": "8.6.15",
            "tk_runtime_patchlevel": "8.6.15",
            **{key: False for key in target.BLOCKED},
        }

    def compare(self, *, receipt=None, tcl=None, tk=None):
        return target.compare_originals(
            self.receipt if receipt is None else receipt, self.exe,
            self.tcl if tcl is None else tcl,
            self.tk if tk is None else tk,
            pinned=self.originals)

    def test_tagged_originals_are_separate_and_no_release_is_approved(self):
        result = self.compare()
        self.assertEqual([item["component"] for item in result["source_originals"]],
                         ["tcl", "tk"])
        self.assertNotEqual(result["source_originals"][0]["upstream_license_git_blob_sha1"],
                            result["source_originals"][1]["upstream_license_git_blob_sha1"])
        self.assertFalse(result["third_party_notice_ready"])
        self.assertFalse(result["customer_release_ready"])
        self.assertFalse(result["frozen_receipt_independently_authenticated"])
        self.assertNotIn(str(self.root), repr(result))
        self.assertNotIn("synthetic-tcl-license-original", repr(result))

    def test_git_blob_id_not_plain_sha1_of_bytes(self):
        self.assertNotEqual(target.git_blob_id(self.tcl), hashlib.sha1(self.tcl).hexdigest())

    def test_wrong_tcl_and_tk_originals_are_rejected(self):
        with self.assertRaises(ValueError):
            self.compare(tcl=self.tk)
        with self.assertRaises(ValueError):
            self.compare(tk=self.tcl)

    def test_same_size_exe_tamper_does_not_reuse_receipt(self):
        before = self.exe.read_bytes()
        self.exe.write_bytes(before.replace(b"synthetic", b"synThetic"))
        self.assertEqual(self.exe.stat().st_size, len(before))
        with self.assertRaises(ValueError):
            self.compare()

    def test_unknown_exact_runtime_versions_are_rejected(self):
        for role in ("tcl", "tk"):
            with self.subTest(role=role):
                changed = dict(self.receipt)
                changed[role + "_runtime_patchlevel"] = "8.6.99"
                with self.assertRaises(ValueError):
                    self.compare(receipt=changed)

    def test_forged_preapproved_flags_are_rejected(self):
        for key in target.BLOCKED:
            with self.subTest(key=key):
                changed = dict(self.receipt)
                changed[key] = True
                with self.assertRaises(ValueError):
                    self.compare(receipt=changed)

    def test_receipt_extra_private_path_is_rejected(self):
        changed = dict(self.receipt)
        changed["private_path"] = "C:/customer"
        with self.assertRaises(ValueError):
            self.compare(receipt=changed)

    def test_wrong_exe_digest_is_rejected(self):
        changed = dict(self.receipt)
        changed["exe_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            self.compare(receipt=changed)

    def test_missing_original_file_fails_without_writing_report(self):
        self.tcl_path.unlink()
        output = self.root / "compare.json"
        receipt = self.root / "receipt.json"
        receipt.write_text(json.dumps(self.receipt), encoding="utf-8")
        with patch.object(target, "PINNED", self.originals):
            result = target.main([
                "--exe", str(self.exe), "--runtime-receipt", str(receipt),
                "--tcl-original", str(self.tcl_path),
                "--tk-original", str(self.tk_path), "--out", str(output)])
        self.assertEqual(result, 1)
        self.assertFalse(output.exists())

    def test_existing_output_is_not_overwritten(self):
        output = self.root / "compare.json"
        output.write_text("preserve", encoding="utf-8")
        receipt = self.root / "receipt.json"
        receipt.write_text(json.dumps(self.receipt), encoding="utf-8")
        with patch.object(target, "PINNED", self.originals):
            code = target.main([
                "--exe", str(self.exe), "--runtime-receipt", str(receipt),
                "--tcl-original", str(self.tcl_path),
                "--tk-original", str(self.tk_path), "--out", str(output)])
        self.assertEqual(code, 1)
        self.assertEqual(output.read_text(encoding="utf-8"), "preserve")

    def test_positive_cli_synthetic_evidence_stays_unapproved(self):
        receipt = self.root / "receipt.json"
        output = self.root / "compare.json"
        receipt.write_text(json.dumps(self.receipt), encoding="utf-8")
        with patch.object(target, "PINNED", self.originals):
            code = target.main([
                "--exe", str(self.exe), "--runtime-receipt", str(receipt),
                "--tcl-original", str(self.tcl_path),
                "--tk-original", str(self.tk_path), "--out", str(output)])
        self.assertEqual(code, 0)
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["exe_sha256"], self.receipt["exe_sha256"])
        self.assertEqual(len(report["source_originals"]), 2)
        self.assertFalse(report["customer_release_ready"])

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink unsupported")
    def test_symlinked_license_is_rejected(self):
        link = self.root / "linked.terms"
        try:
            link.symlink_to(self.tcl_path)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation unavailable")
        with self.assertRaises(ValueError):
            target._safe_read(link, target.MAX_LICENSE)


if __name__ == "__main__":
    unittest.main()
