"""Synthetic, offline-only tests for a frozen runtime-option TOC classification."""
from __future__ import annotations

import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.classify_unmatched_carchive import classify_unmatched


class LastUnmatchedArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="cc-last-archive-option-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.exe = self.root / "inert.exe"
        self.exe.write_bytes(b"MZ" + b"never execute this fixture")
        sha = hashlib.sha256(self.exe.read_bytes()).hexdigest()
        self.audit = {
            "format": "code_checker_p0d_frozen_archive_audit_v1",
            "exe_sha256": sha,
            "customer_release_ready": False,
            "third_party_notice_ready_to_distribute": False,
            "license_compliance_certified": False,
            "archive": {"top_level": [
                {"name": "PYZ.pyz", "typecode": "z"},
                {"name": "pyi-contents-directory _internal", "typecode": "o"},
            ]},
        }
        self.pkg = {
            "format": "code_checker_p0h_pkg_toc_metadata_v1",
            "exe_sha256": sha,
            "customer_release_ready": False,
            "legal_notice_approved": False,
            "license_compliance_certified": False,
            "previously_unmatched_exe_toc": 1,
            "pkg_unique_record_claims": 0,
            "pkg_ambiguous_record_claims": 0,
            "pkg_no_record_claims": 1,
            "all_prior_unmatched_accounted_for": True,
            "records": [{
                "name": "pyi-contents-directory _internal",
                "carchive_typecode": "o",
                "pkg_toc_evidence": "no_pkg_toc_record",
                "copyright_owner_verified": False,
                "license_approved": False,
            }],
        }

    def inspect(self) -> dict:
        return classify_unmatched(self.audit, self.pkg, self.exe)

    def test_runtime_option_has_no_separate_file_and_no_license_approval(self):
        result = self.inspect()
        self.assertEqual(result["runtime_option_metadata_count"], 1)
        self.assertEqual(result["recognized_option_name_count"], 1)
        self.assertEqual(result["unresolved_payload_count"], 0)
        self.assertEqual(result["exe_sha256"], self.audit["exe_sha256"])
        row = result["records"][0]
        self.assertEqual(row["carchive_typecode"], "o")
        self.assertTrue(row["runtime_option_not_a_separate_embedded_file"])
        self.assertFalse(row["actual_archive_source_or_vendor_verified"])
        self.assertFalse(result["customer_release_ready"])
        self.assertFalse(result["customer_notice_ready"])
        self.assertNotIn("pyi-contents-directory", repr(result))
        self.assertNotIn(str(self.root), repr(result))

    def test_binary_payload_is_not_mislabeled_as_runtime_option(self):
        self.pkg["records"][0]["carchive_typecode"] = "b"
        self.audit["archive"]["top_level"][1]["typecode"] = "b"
        result = self.inspect()
        self.assertEqual(result["runtime_option_metadata_count"], 0)
        self.assertEqual(result["unresolved_payload_count"], 1)
        self.assertFalse(result["records"][0]["runtime_option_not_a_separate_embedded_file"])

    def test_unrecognized_option_name_is_not_whitelisted(self):
        self.pkg["records"][0]["name"] = "unfamiliar-embedded-option"
        self.audit["archive"]["top_level"][1]["name"] = "unfamiliar-embedded-option"
        result = self.inspect()
        self.assertEqual(result["runtime_option_metadata_count"], 1)
        self.assertEqual(result["recognized_option_name_count"], 0)
        self.assertFalse(result["records"][0]["option_name_matches_known_syntax"])

    def test_only_bounded_single_token_logical_archive_names_are_displayed(self):
        self.pkg["records"][0]["name"] = "mystery.dat"
        self.audit["archive"]["top_level"][1]["name"] = "mystery.dat"
        self.pkg["records"][0]["carchive_typecode"] = "x"
        self.audit["archive"]["top_level"][1]["typecode"] = "x"
        row = self.inspect()["records"][0]
        self.assertEqual(row["safe_single_token_archive_label"], "mystery.dat")
        self.pkg["records"][0]["name"] = "private/mystery.dat"
        self.audit["archive"]["top_level"][1]["name"] = "private/mystery.dat"
        self.assertIsNone(self.inspect()["records"][0]["safe_single_token_archive_label"])
        self.assertFalse(self.inspect()["customer_release_ready"])

    def test_same_size_binary_mutation_rejected(self):
        self.exe.write_bytes(self.exe.read_bytes().replace(b"never", b"NeVer"))
        with self.assertRaises(ValueError):
            self.inspect()

    def test_incorrect_sha_and_count_rejected(self):
        self.pkg["exe_sha256"] = "a" * 64
        with self.assertRaises(ValueError):
            self.inspect()
        self.pkg["exe_sha256"] = self.audit["exe_sha256"]
        self.pkg["pkg_no_record_claims"] = 2
        with self.assertRaises(ValueError):
            self.inspect()

    def test_duplicate_and_forged_license_approval_rejected(self):
        self.pkg["records"].append(copy.deepcopy(self.pkg["records"][0]))
        self.pkg["previously_unmatched_exe_toc"] = 2
        self.pkg["pkg_no_record_claims"] = 2
        with self.assertRaises(ValueError):
            self.inspect()
        self.pkg["records"].pop()
        self.pkg["previously_unmatched_exe_toc"] = 1
        self.pkg["pkg_no_record_claims"] = 1
        for target, field in (
            (self.pkg, "customer_release_ready"),
            (self.pkg["records"][0], "license_approved"),
            (self.audit, "license_compliance_certified"),
        ):
            with self.subTest(field=field):
                target[field] = True
                with self.assertRaises(ValueError):
                    self.inspect()
                target[field] = False

    def test_prevent_absolute_path_and_mismatched_archive_type(self):
        self.pkg["records"][0]["name"] = "C:/Users/private/source.bin"
        with self.assertRaises(ValueError):
            self.inspect()
        self.pkg["records"][0]["name"] = self.audit["archive"]["top_level"][1]["name"]
        self.pkg["records"][0]["carchive_typecode"] = "s"
        with self.assertRaises(ValueError):
            self.inspect()


if __name__ == "__main__":
    unittest.main()
