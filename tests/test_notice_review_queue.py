"""Synthetic, offline EXE-bound component ownership review queue regression tests."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_notice_review_queue import build_review_queue
from test_notice_gap_ledger import fixture


class ExactBinaryNoticeQueueTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="code-checker-license-queue-")
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        self.exe = self.folder / "synthetic.exe"
        self.exe.write_bytes(b"MZ" + b"synthetic, nonexecutable metadata fixture")
        self.stages = fixture()
        sha = hashlib.sha256(self.exe.read_bytes()).hexdigest()
        for item in self.stages:
            item["exe_sha256"] = sha

    def queue(self) -> dict:
        return build_review_queue(*self.stages, self.exe)

    def test_legal_review_queue_is_complete_but_never_retail_approved(self) -> None:
        result = self.queue()
        self.assertEqual(result["exe_sha256"], hashlib.sha256(self.exe.read_bytes()).hexdigest())
        self.assertEqual(result["exe_bytes"], self.exe.stat().st_size)
        self.assertEqual(result["unresolved_entry_count"], 1)
        self.assertEqual(result["unresolved_entries_requiring_review"][0]["archive_entry"], "mystery.dll")
        self.assertEqual(len(result["distribution_review"]), 2)
        self.assertEqual(len(result["manual_review_tasks"]), 7)
        self.assertFalse(result["original_license_texts_included"])
        self.assertFalse(result["third_party_notice_ready"])
        self.assertFalse(result["license_compliance_certified"])
        self.assertFalse(result["customer_release_ready"])
        self.assertNotIn(str(self.folder), json.dumps(result))

    def test_binary_hash_mismatch_same_length_is_rejected(self) -> None:
        raw = self.exe.read_bytes()
        self.exe.write_bytes(raw.replace(b"synthetic", b"synThetic", 1))
        self.assertEqual(self.exe.stat().st_size, len(raw))
        with self.assertRaises(ValueError):
            self.queue()

    def test_missing_executable_and_symlink_are_rejected(self) -> None:
        self.exe.unlink()
        with self.assertRaises(ValueError):
            self.queue()
        self.exe.write_bytes(b"MZ" + b"synthetic, nonexecutable metadata fixture")
        link = self.folder / "link.exe"
        try:
            link.symlink_to(self.exe)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks unavailable")
        with self.assertRaises(ValueError):
            build_review_queue(*self.stages, link)

    def test_incomplete_evidence_and_forged_license_flag_are_rejected(self) -> None:
        self.stages[2]["records"].clear()
        with self.assertRaises(ValueError):
            self.queue()
        self.stages = fixture()
        sha = hashlib.sha256(self.exe.read_bytes()).hexdigest()
        for item in self.stages:
            item["exe_sha256"] = sha
        self.stages[0]["customer_release_ready"] = True
        with self.assertRaises(ValueError):
            self.queue()

    def test_tampered_absolute_archive_entry_is_never_copied(self) -> None:
        bad = "../private.dll"
        for row in self.stages[0]["archive"]["top_level"]:
            if row["name"] == "mystery.dll":
                row["name"] = bad
        for row in self.stages[1]["entries"]:
            if row["name"] == "mystery.dll":
                row["name"] = bad
        self.stages[2]["records"][0]["name"] = bad
        with self.assertRaises(ValueError):
            self.queue()

    def test_untrusted_build_location_string_is_not_exposed(self) -> None:
        self.stages[2]["records"][0]["source_location_category"] = (
            r"C:\\Users\\someone\\secret-build\\internal.dll"
        )
        with self.assertRaises(ValueError):
            self.queue()

    def test_review_row_has_build_metadata_not_build_source_path(self) -> None:
        self.stages[2]["records"][0].update({
            "source_location_category": "python_site_packages",
            "source_byte_match": "byte_identical_to_recorded_build_source",
        })
        result = self.queue()
        row = result["unresolved_entries_requiring_review"][0]
        self.assertEqual(row["source_location_category"], "python_site_packages")
        self.assertEqual(row["source_byte_match"], "byte_identical_to_recorded_build_source")
        self.assertEqual(row["human_owner_version_and_license_review"], "REQUIRED")
        self.assertFalse(row["redistribution_permission_verified"])


if __name__ == "__main__":
    unittest.main()
