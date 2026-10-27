"""Synthetic provenance chain and original LICENSE review-gap regression tests."""
from __future__ import annotations

import copy
import unittest

from scripts.map_frozen_licenses import make_mapping
from scripts.reconcile_notice_gaps import FORMAT, reconcile_notice_gaps


def fixture():
    sha = "f" * 64
    audit = {
        "exe_sha256": sha,
        "license_compliance_certified": False,
        "third_party_notice_ready_to_distribute": False,
        "customer_release_ready": False,
        "archive": {
            "top_level": [
                {"name": "python313.dll", "typecode": "b"},
                {"name": "tcl86t.dll", "typecode": "b"},
                {"name": "mystery.dll", "typecode": "b"},
            ],
            "pyz_modules": [{"module": "os"}, {"module": "pydantic.main"}],
        },
        "python_build_distributions": [
            {"name": "pydantic", "version": "2.12.5", "license_metadata": "MIT",
             "license_files_in_installed_distribution": [
                 {"installed_relative_path": "pydantic/LICENSE", "sha256": "a" * 64, "bytes": 80},
             ]},
            {"name": "pyinstaller", "version": "6.22.3", "license_metadata": "GPL",
             "license_files_in_installed_distribution": [
                 {"installed_relative_path": "pyinstaller/COPYING", "sha256": "b" * 64, "bytes": 92},
             ]},
        ],
    }
    mapping = make_mapping(
        audit, package_claims={"pydantic": ["pydantic"]}, installed_files={}
    )
    mapping["license_text_draft"] = {
        "selected_installed_distributions": ["pydantic", "pyinstaller"],
        "staged_original_license_files": 2,
        "unavailable_or_missing_texts": [],
        "draft_for_distribution": False,
        "human_legal_review_pending": True,
        "selected_dists_without_claim_of_exe_inclusion": True,
    }
    native = {
        "exe_sha256": sha, "previous_unresolved_archive_entries": 1,
        "records": [{"name": "mystery.dll",
                     "build_record_evidence": "recorded_build_source_path_candidate"}],
        "not_uniquely_recorded_in_build_toc": 0,
        "all_entries_counted": True,
        "source_path_not_a_license_or_vendor_proof": True,
        "customer_release_ready": False,
        "legal_notice_approved": False,
    }
    exe = {
        "exe_sha256": sha, "previously_not_unique_analysis_claims": 0,
        "records": [], "exe_toc_entry_claims": 0, "ambiguous_exe_toc_claims": 0,
        "without_exe_toc_claims": 0,
        "all_pending_entries_accounted_for": True,
        "customer_release_ready": False, "legal_notice_approved": False,
        "license_compliance_certified": False,
    }
    pkg = {
        "exe_sha256": sha, "previously_unmatched_exe_toc": 0,
        "records": [], "pkg_unique_record_claims": 0,
        "pkg_ambiguous_record_claims": 0, "pkg_no_record_claims": 0,
        "all_prior_unmatched_accounted_for": True,
        "customer_release_ready": False, "legal_notice_approved": False,
        "license_compliance_certified": False,
    }
    return [audit, mapping, native, exe, pkg]


class NoticeLedgerTests(unittest.TestCase):
    def test_valid_evidence_is_only_review_queue_never_license_clearance(self):
        args = fixture()
        report = reconcile_notice_gaps(*args)
        self.assertEqual(report["format"], FORMAT)
        self.assertEqual(report["mapped_exe_entries"], 5)
        self.assertEqual(report["candidate_distribution_count"], 1)
        self.assertEqual(report["selected_installed_distribution_count"], 2)
        self.assertEqual(report["staged_original_license_file_count"], 2)
        self.assertEqual(report["unresolved_archive_entry_count"], 1)
        self.assertFalse(report["license_compliance_certified"])
        self.assertFalse(report["notice_ready_to_distribute"])
        self.assertFalse(report["customer_release_ready"])
        self.assertFalse(report["original_license_texts_embedded_in_output"])
        self.assertEqual(len(report["manual_review_tasks"]), 7)
        self.assertTrue(all(t["human_original_text_and_notice_review"] == "REQUIRED"
                            for t in report["distribution_review"]))

    def test_one_original_license_missing_is_visible_not_silently_approved(self):
        args = fixture()
        args[1]["license_text_draft"]["staged_original_license_files"] = 1
        args[1]["license_text_draft"]["unavailable_or_missing_texts"] = ["pydantic: missing"]
        result = reconcile_notice_gaps(*args)
        self.assertEqual(result["missing_original_license_observation_count"], 1)
        self.assertEqual(result["staged_original_license_file_count"], 1)
        self.assertFalse(result["notice_ready_to_distribute"])

    def test_absent_license_rows_still_require_human_review(self):
        args = fixture()
        args[0]["python_build_distributions"][0]["license_files_in_installed_distribution"] = []
        args[1]["license_text_draft"]["staged_original_license_files"] = 1
        args[1]["license_text_draft"]["unavailable_or_missing_texts"] = ["pydantic: no listed original"]
        result = reconcile_notice_gaps(*args)
        item = next(i for i in result["distribution_review"] if i["candidate_distribution"] == "pydantic")
        self.assertEqual(item["original_license_file_metadata_count"], 0)
        self.assertFalse(item["binary_owner_and_inclusion_proven"])

    def test_sha_drift_in_any_staged_evidence_rejected(self):
        for i in (1, 2, 3, 4):
            with self.subTest(stage=i):
                args = fixture()
                args[i]["exe_sha256"] = "1" * 64
                with self.assertRaises(ValueError):
                    reconcile_notice_gaps(*args)

    def test_flags_cannot_be_promoted(self):
        for i, key in (
            (0, "customer_release_ready"),
            (1, "license_compliance_certified"),
            (1, "embedded_binary_hash_matches_checked"),
            (2, "legal_notice_approved"),
            (3, "customer_release_ready"),
            (4, "license_compliance_certified"),
        ):
            with self.subTest(stage=i, key=key):
                args = fixture()
                args[i][key] = True
                with self.assertRaises(ValueError):
                    reconcile_notice_gaps(*args)

    def test_windows_archive_separators_match_ownership_canonical_names(self):
        args = fixture()
        args[0]["archive"]["top_level"][-1]["name"] = r"nested\mystery.dll"
        args[1] = make_mapping(args[0], package_claims={"pydantic": ["pydantic"]}, installed_files={})
        args[1]["license_text_draft"] = fixture()[1]["license_text_draft"]
        args[2]["records"][0]["name"] = "nested/mystery.dll"
        result = reconcile_notice_gaps(*args)
        self.assertTrue(result["metadata_complete"])
        self.assertEqual(result["unresolved_archive_entry_count"], 1)

    def test_archive_rows_are_exhaustive_and_exact(self):
        args = fixture()
        args[1]["entries"].pop()
        with self.assertRaises(ValueError):
            reconcile_notice_gaps(*args)
        args = fixture()
        args[1]["entries"][0]["name"] = "different.dll"
        with self.assertRaises(ValueError):
            reconcile_notice_gaps(*args)

    def test_candidate_names_must_match_actual_names_not_manual_claim(self):
        args = fixture()
        args[1]["installed_dist_candidates"] = ["pyinstaller"]
        with self.assertRaises(ValueError):
            reconcile_notice_gaps(*args)
        args = fixture()
        args[1]["license_text_draft"]["selected_installed_distributions"] = ["pydantic"]
        with self.assertRaises(ValueError):
            reconcile_notice_gaps(*args)

    def test_missing_license_provenance_and_count_tampering_rejected(self):
        args = fixture()
        args[0]["python_build_distributions"][0]["license_files_in_installed_distribution"][0]["sha256"] = "bad"
        with self.assertRaises(ValueError):
            reconcile_notice_gaps(*args)
        args = fixture()
        args[1]["license_text_draft"]["staged_original_license_files"] = 40
        with self.assertRaises(ValueError):
            reconcile_notice_gaps(*args)

    def test_native_unresolved_set_must_match_mapping(self):
        args = fixture()
        args[2]["records"][0]["name"] = "ghost.dll"
        with self.assertRaises(ValueError):
            reconcile_notice_gaps(*args)

    def test_exe_and_pkg_followup_counts_must_match_provenance_chain(self):
        args = fixture()
        args[2]["records"][0]["build_record_evidence"] = "no_build_record"
        with self.assertRaises(ValueError):
            reconcile_notice_gaps(*args)
        args = fixture()
        args[4]["previously_unmatched_exe_toc"] = 1
        with self.assertRaises(ValueError):
            reconcile_notice_gaps(*args)

    def test_external_absolute_source_paths_and_full_license_text_not_written(self):
        args = fixture()
        args[0]["python_build_distributions"][0]["license_files_in_installed_distribution"][0]["installed_relative_path"] = r"C:\Users\somebody\private_LICENSE"
        output = str(reconcile_notice_gaps(*args))
        self.assertNotIn("C:\\Users", output)
        self.assertNotIn("private_LICENSE", output)


if __name__ == "__main__":
    unittest.main()
