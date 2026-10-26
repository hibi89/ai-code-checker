"""Read-only synthetic PyInstaller TOC reconciliation tests; no binaries executed."""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.reconcile_native_build import parse_analysis_toc, reconcile, normalize, source_bucket


def sample_mapping():
    return {
        "exe_sha256": "f" * 64,
        "customer_release_ready": False,
        "third_party_notice_ready_to_distribute": False,
        "license_compliance_certified": False,
        "entries": [
            {"kind": "CArchive", "name": "alpha.dll",
             "mapping": "unresolved_native_or_system_binary"},
            {"kind": "CArchive", "name": "another.dll",
             "mapping": "unresolved_native_or_system_binary"},
            {"kind": "CArchive", "name": "sub/resource.dat",
             "mapping": "unresolved_archive_resource_or_bootloader"},
            {"kind": "CArchive", "name": "no-entry.dll",
             "mapping": "unresolved_native_or_system_binary"},
            {"kind": "PYZ", "name": "sys", "mapping": "cpython_stdlib_name_candidate"},
        ],
    }


class FakeReader:
    def extract(self, name):
        if name == "alpha.dll":
            return b"SYNTHETIC DLL BYTES"
        if name == "another.dll":
            return b"different bytes"
        raise KeyError(name)


class NativeProvenanceTests(unittest.TestCase):
    def test_parser_uses_ast_literal_eval_only_and_collects_realistic_toc(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Analysis-00.toc"
            path.write_text(repr((
                [("alpha.dll", "C:/Python/DLLs/alpha.dll", "BINARY")],
                {"datas": [("sub/resource.dat", "C:/tmp/resource.dat", "DATA")]},
                ("other", ["arbitrary", {"data": 1}], "misc"),
            )), encoding="utf-8")
            records = parse_analysis_toc(path)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0][0], "alpha.dll")
        self.assertEqual(records[1][0], "sub/resource.dat")

    def test_rejects_malicious_toc_expression_without_executing(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "Analysis-00.toc"
            marker = Path(tmp) / "should-not-exist"
            source.write_text("__import__('pathlib').Path(" + repr(str(marker)) +
                              ").write_text('unsafe')", encoding="utf-8")
            with self.assertRaises((ValueError, SyntaxError)):
                parse_analysis_toc(source)
            self.assertFalse(marker.exists())

    def test_exact_byte_provenance_is_distinct_from_license_certification(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "alpha.dll"
            b = Path(tmp) / "another.dll"
            resource = Path(tmp) / "resource.dat"
            a.write_bytes(b"SYNTHETIC DLL BYTES")
            b.write_bytes(b"build source differs")
            resource.write_bytes(b"resource")
            records = [
                ("alpha.dll", a, "BINARY"),
                ("another.dll", b, "BINARY"),
                ("sub/resource.dat", resource, "DATA"),
            ]
            result = reconcile(sample_mapping(), records, archive_reader=FakeReader())
        self.assertEqual(result["previous_unresolved_archive_entries"], 4)
        self.assertEqual(result["recorded_build_source_candidates"], 3)
        self.assertEqual(result["native_archive_exact_byte_matches"], 1)
        self.assertEqual(result["not_uniquely_recorded_in_build_toc"], 1)
        self.assertTrue(result["all_entries_counted"])
        self.assertFalse(result["legal_notice_approved"])
        self.assertFalse(result["customer_release_ready"])
        names = {entry["name"]: entry for entry in result["records"]}
        self.assertEqual(names["alpha.dll"]["source_byte_match"],
                         "byte_identical_to_recorded_build_source")
        self.assertEqual(names["another.dll"]["source_byte_match"],
                         "different_bytes_review_required")
        self.assertEqual(names["no-entry.dll"]["build_record_evidence"], "no_analysis_claim")
        self.assertNotIn(str(a.parent), repr(result))

    def test_ambiguous_same_archive_path_is_not_accepted_as_unique(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "a.dll"
            b = Path(tmp) / "b.dll"
            a.write_bytes(b"x")
            b.write_bytes(b"x")
            result = reconcile(sample_mapping(), [("alpha.dll", a, "BINARY"),
                                                   ("alpha.dll", b, "BINARY")])
        self.assertEqual(result["recorded_build_source_candidates"], 0)
        self.assertEqual(result["native_archive_exact_byte_matches"], 0)
        self.assertIn("ambiguous_multiple_source_records", result["evidence_counts"])

    def test_toc_path_traversal_and_overlong_name_rejected(self):
        for path in ("../escape.dll", "/root.dll", "x" * 800):
            with self.assertRaises(ValueError):
                normalize(path)

    def test_license_approved_input_fail_closed(self):
        mapping = sample_mapping()
        mapping["customer_release_ready"] = True
        with self.assertRaises(ValueError):
            reconcile(mapping, [("alpha.dll", Path("alpha.dll"), "BINARY")])

    def test_path_provenance_bucket_does_not_disclose_home_directory(self):
        bucket = source_bucket(Path("C:/Users/tester/AppData/Local/python/site-packages/abc/dll.pyd"))
        self.assertEqual(bucket, "python_site_packages")
        self.assertNotIn("tester", bucket)


if __name__ == "__main__":
    unittest.main()
