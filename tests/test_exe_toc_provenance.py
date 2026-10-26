"""P0-G synthetic EXE build TOC tests; no real binaries or customer input."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.reconcile_exe_toc import parse_exe_toc, reconcile_exe_toc


def evidence():
    previous = {
        "exe_sha256": "a" * 64,
        "previous_unresolved_archive_entries": 3,
        "not_uniquely_recorded_in_build_toc": 2,
        "customer_release_ready": False,
        "legal_notice_approved": False,
        "records": [
            {"name": "linked.dll", "build_record_evidence": "recorded_build_source_path_candidate"},
            {"name": "pyi_rth_test", "build_record_evidence": "no_analysis_claim"},
            {"name": "missing.dat", "build_record_evidence": "basename_hypothesis_only"},
        ],
    }
    audit = {
        "exe_sha256": "a" * 64,
        "customer_release_ready": False,
        "license_compliance_certified": False,
        "third_party_notice_ready_to_distribute": False,
        "archive": {"top_level": [
            {"name": "linked.dll", "typecode": "b"},
            {"name": "pyi_rth_test", "typecode": "s"},
            {"name": "missing.dat", "typecode": "x"},
        ]},
    }
    return previous, audit


class ExeTocEvidenceTests(unittest.TestCase):
    def test_parse_literal_toc_without_leaking_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "EXE-00.toc"
            path.write_text(repr(([
                ("pyi_rth_test", "C:/Users/private/pyi_rth_test.py", "PYSOURCE"),
                ("missing.dat", None, "OPTION"),
            ], ("ignored", {"meta": True}))), encoding="utf-8")
            rows = parse_exe_toc(path)
        self.assertIn(("pyi_rth_test", "PYSOURCE", True), rows)
        self.assertIn(("missing.dat", "OPTION", False), rows)
        self.assertNotIn("private", repr(rows))

    def test_count_exact_and_missing_without_ownership_claims(self):
        previous, audit = evidence()
        result = reconcile_exe_toc(
            previous, audit, [("pyi_rth_test", "PYSOURCE", True)]
        )
        self.assertEqual(result["previously_not_unique_analysis_claims"], 2)
        self.assertEqual(result["exe_toc_entry_claims"], 1)
        self.assertEqual(result["without_exe_toc_claims"], 1)
        self.assertTrue(result["all_pending_entries_accounted_for"])
        self.assertFalse(result["customer_release_ready"])
        self.assertFalse(result["legal_notice_approved"])
        self.assertFalse(result["license_compliance_certified"])
        self.assertNotIn("C:/", repr(result))
        self.assertFalse(result["records"][0]["owner_or_license_verified"])

    def test_ambiguous_toc_type_does_not_count_as_unique(self):
        previous, audit = evidence()
        result = reconcile_exe_toc(previous, audit, [
            ("pyi_rth_test", "PYSOURCE", True),
            ("pyi_rth_test", "DATA", True),
        ])
        self.assertEqual(result["exe_toc_entry_claims"], 0)
        self.assertEqual(result["ambiguous_exe_toc_claims"], 1)

    def test_rejects_wrong_exe_identity_or_accounting(self):
        p, a = evidence()
        p["exe_sha256"] = "f" * 64
        with self.assertRaises(ValueError):
            reconcile_exe_toc(p, a, [])
        p, a = evidence()
        p["not_uniquely_recorded_in_build_toc"] = 999
        with self.assertRaises(ValueError):
            reconcile_exe_toc(p, a, [])

    def test_blocks_preapproved_license_or_notice(self):
        p, a = evidence()
        a["license_compliance_certified"] = True
        with self.assertRaises(ValueError):
            reconcile_exe_toc(p, a, [])
        p, a = evidence()
        p["legal_notice_approved"] = True
        with self.assertRaises(ValueError):
            reconcile_exe_toc(p, a, [])

    def test_duplicate_or_nonexistent_archive_rejected(self):
        p, a = evidence()
        p["records"].append({"name": "missing.dat", "build_record_evidence": "no_analysis_claim"})
        p["previous_unresolved_archive_entries"] += 1
        p["not_uniquely_recorded_in_build_toc"] += 1
        with self.assertRaises(ValueError):
            reconcile_exe_toc(p, a, [])

    def test_rejects_executable_literal_in_toc(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "EXE-00.toc"
            marker = Path(tmp) / "marker"
            path.write_text("__import__('pathlib').Path(" + repr(str(marker)) +
                            ").write_text('bad')", encoding="utf-8")
            with self.assertRaises((ValueError, SyntaxError)):
                parse_exe_toc(path)
            self.assertFalse(marker.exists())

    def test_oversized_toc_and_absolute_archive_name_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "EXE-00.toc"
            path.write_text(repr([
                ("/abs/resource", "C:/Users/private/file", "DATA"),
                ("../escape", "C:/private", "DATA"),
                ("safe/resource", "C:/private", "DATA"),
            ]), encoding="utf-8")
            self.assertEqual(parse_exe_toc(path), [("safe/resource", "DATA", True)])
            path.write_text("x" * (16 * 1024 * 1024 + 1), encoding="utf-8")
            with self.assertRaises(ValueError):
                parse_exe_toc(path)


if __name__ == "__main__":
    unittest.main()
