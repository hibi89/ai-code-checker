"""P0-H: synthetic source-safe, no customer source, never executes bundled files."""
import tempfile
import unittest
from pathlib import Path

from scripts.reconcile_exe_toc import parse_exe_toc
from scripts.reconcile_pkg_toc import reconcile_pkg_toc


def evidence():
    return ({
        "exe_sha256": "a" * 64,
        "customer_release_ready": False,
        "legal_notice_approved": False,
        "license_compliance_certified": False,
        "previously_not_unique_analysis_claims": 2,
        "exe_toc_entry_claims": 1,
        "ambiguous_exe_toc_claims": 0,
        "without_exe_toc_claims": 1,
        "records": [
            {"name": "known.py", "carchive_typecode": "s",
             "exe_toc_evidence": "unique_exe_build_toc_entry_claim_only"},
            {"name": "pyi-unknown", "carchive_typecode": "o",
             "exe_toc_evidence": "no_exe_toc_entry_claim"},
        ]
    }, {
        "exe_sha256": "a" * 64,
        "customer_release_ready": False,
        "third_party_notice_ready_to_distribute": False,
        "license_compliance_certified": False,
        "archive": {"top_level": [
            {"name": "known.py", "typecode": "s"},
            {"name": "pyi-unknown", "typecode": "o"},
        ]},
    })


class PkgTocTests(unittest.TestCase):
    def test_unique_pkg_name_preserves_legal_blocks(self):
        p, a = evidence()
        out = reconcile_pkg_toc(p, a, [("pyi-unknown", "OPTION", False)])
        self.assertEqual(out["previously_unmatched_exe_toc"], 1)
        self.assertEqual(out["pkg_unique_record_claims"], 1)
        self.assertFalse(out["records"][0]["pkg_toc_source_path_present"])
        self.assertEqual(out["records"][0]["pkg_toc_record_types"], ["OPTION"])
        self.assertFalse(out["customer_release_ready"])
        self.assertFalse(out["legal_notice_approved"])
        self.assertFalse(out["records"][0]["copyright_owner_verified"])

    def test_missing_pkg_is_not_claimed_resolved(self):
        p, a = evidence()
        out = reconcile_pkg_toc(p, a, [])
        self.assertEqual(out["pkg_no_record_claims"], 1)
        self.assertEqual(out["pkg_unique_record_claims"], 0)

    def test_ambiguous_pkg_entries_remain_ambiguous(self):
        p, a = evidence()
        out = reconcile_pkg_toc(p, a, [
            ("pyi-unknown", "OPTION", False),
            ("pyi-unknown", "DATA", True),
        ])
        self.assertEqual(out["pkg_ambiguous_record_claims"], 1)
        self.assertEqual(out["pkg_unique_record_claims"], 0)

    def test_mismatched_exe_or_count_blocks(self):
        p, a = evidence()
        a["exe_sha256"] = "b" * 64
        with self.assertRaises(ValueError):
            reconcile_pkg_toc(p, a, [])
        p, a = evidence()
        p["without_exe_toc_claims"] = 0
        with self.assertRaises(ValueError):
            reconcile_pkg_toc(p, a, [])

    def test_wrong_archive_type_or_duplicated_prior_fails(self):
        p, a = evidence()
        p["records"][1]["carchive_typecode"] = "z"
        with self.assertRaises(ValueError):
            reconcile_pkg_toc(p, a, [])
        p, a = evidence()
        p["records"].append(dict(p["records"][1]))
        p["previously_not_unique_analysis_claims"] = 3
        p["without_exe_toc_claims"] = 2
        with self.assertRaises(ValueError):
            reconcile_pkg_toc(p, a, [])

    def test_preapproved_release_flags_are_rejected(self):
        for target, flag in (("prior", "customer_release_ready"),
                             ("prior", "legal_notice_approved"),
                             ("prior", "license_compliance_certified"),
                             ("audit", "third_party_notice_ready_to_distribute")):
            p, a = evidence()
            (p if target == "prior" else a)[flag] = True
            with self.assertRaises(ValueError):
                reconcile_pkg_toc(p, a, [])

    def test_pkg_parser_excludes_absolute_build_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "PKG-00.toc"
            path.write_text(repr([
                ("pyi-unknown", "C:/Users/tester/private", "OPTION"),
                ("trailing.bin", None, "DATA"),
            ]), encoding="utf-8")
            rows = parse_exe_toc(path)
            self.assertIn(("pyi-unknown", "OPTION", True), rows)
            self.assertNotIn("tester", repr(rows))


if __name__ == "__main__":
    unittest.main()
