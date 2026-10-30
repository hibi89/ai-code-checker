"""Offline human-review HTML: no release approval, no unsafe source names."""
from __future__ import annotations

import copy
import hashlib
import html
import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_notice_review_queue import build_review_queue
from scripts.render_notice_review_worksheet import (
    main, priority_for, render_review_worksheet,
)
from test_notice_gap_ledger import fixture


class ManualWorksheetTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)
        self.exe = self.folder / "synthetic-exe.exe"
        self.exe.write_bytes(b"MZ synthetic source only")
        self.stages = fixture()
        sha = hashlib.sha256(self.exe.read_bytes()).hexdigest()
        for stage in self.stages:
            stage["exe_sha256"] = sha
        self.stages[2]["records"][0]["initial_category"] = (
            "unresolved_native_or_system_binary"
        )
        self.queue = build_review_queue(*self.stages, self.exe)

    def test_exact_exe_review_produces_printable_unapproved_document(self):
        result = render_review_worksheet(self.queue)
        self.assertIn("<!doctype html>", result)
        self.assertIn("mystery.dll", result)
        self.assertIn(self.queue["exe_sha256"], result)
        self.assertIn("NOT APPROVED", result)
        self.assertIn("Release remains blocked", result)
        self.assertIn("Content-Security-Policy", result)
        self.assertIn("default-src 'none'", result)
        self.assertIn("Owner/version:", result)
        self.assertNotIn(str(self.folder), result)
        self.assertNotIn("LICENSE full text", result)

    def test_source_byte_match_is_only_lower_review_priority(self):
        row = copy.deepcopy(self.queue["unresolved_entries_requiring_review"][0])
        self.assertEqual(priority_for(row), 1)
        row["build_record_evidence"] = "recorded_build_source_path_candidate"
        row["source_byte_match"] = "not_tested"
        self.assertEqual(priority_for(row), 1)
        row["source_byte_match"] = "byte_identical_to_recorded_build_source"
        self.assertEqual(priority_for(row), 2)
        row["source_byte_match"] = "different_bytes_review_required"
        self.assertEqual(priority_for(row), 0)

    def test_archive_name_is_html_escaped_instead_of_executed(self):
        row = self.queue["unresolved_entries_requiring_review"][0]
        raw = "<img src=x onerror=alert(1)>.dll"
        row["archive_entry"] = raw
        result = render_review_worksheet(self.queue)
        self.assertIn(html.escape(raw), result)
        self.assertNotIn(raw, result)
        self.assertNotIn("<img ", result)

    def test_tampered_counts_or_missing_row_rejected(self):
        for edit in ("count", "row", "category", "source"):
            with self.subTest(edit=edit):
                q = copy.deepcopy(self.queue)
                if edit == "count":
                    q["unresolved_entry_count"] += 1
                elif edit == "row":
                    q["unresolved_entries_requiring_review"].clear()
                elif edit == "category":
                    q["unresolved_category_counts"] = {}
                else:
                    q["build_source_candidate_counts"] = {}
                with self.assertRaises(ValueError):
                    render_review_worksheet(q)

    def test_duplicate_names_and_untrusted_build_status_rejected(self):
        q = copy.deepcopy(self.queue)
        q["unresolved_entries_requiring_review"].append(
            copy.deepcopy(q["unresolved_entries_requiring_review"][0]))
        q["unresolved_entry_count"] += 1
        with self.assertRaises(ValueError):
            render_review_worksheet(q)
        q = copy.deepcopy(self.queue)
        q["unresolved_entries_requiring_review"][0]["build_record_evidence"] = "verified_licensed"
        with self.assertRaises(ValueError):
            render_review_worksheet(q)

    def test_forced_approval_flags_rejected(self):
        for key in (
            "vendor_or_binary_ownership_certified", "third_party_notice_ready",
            "license_compliance_certified", "customer_release_ready",
            "original_license_texts_included",
        ):
            with self.subTest(flag=key):
                q = copy.deepcopy(self.queue)
                q[key] = True
                with self.assertRaises(ValueError):
                    render_review_worksheet(q)
        q = copy.deepcopy(self.queue)
        q["unresolved_entries_requiring_review"][0]["redistribution_permission_verified"] = True
        with self.assertRaises(ValueError):
            render_review_worksheet(q)

    def test_cli_uses_actual_exe_and_all_five_stages(self):
        names = ["audit", "mapping", "native", "exe-toc", "pkg-toc"]
        paths = []
        for name, stage in zip(names, self.stages):
            path = self.folder / (name + ".json")
            path.write_text(json.dumps(stage), encoding="utf-8")
            paths.append(path)
        out = self.folder / "manual-review.html"
        argv = [option for name, p in zip(names, paths)
                for option in ("--" + name, str(p))]
        argv += ["--exe", str(self.exe), "--out", str(out)]
        self.assertEqual(main(argv), 0)
        result = out.read_text(encoding="utf-8")
        self.assertIn("mystery.dll", result)
        self.assertIn(self.queue["exe_sha256"], result)
        self.assertNotIn('"customer_release_ready": true', result)
        self.assertEqual(main(argv), 1)
        self.assertEqual(result, out.read_text(encoding="utf-8"))

    def test_cli_fails_closed_on_mutated_exe_without_worksheet(self):
        names = ["audit", "mapping", "native", "exe-toc", "pkg-toc"]
        argv = []
        for name, stage in zip(names, self.stages):
            path = self.folder / (name + ".json")
            path.write_text(json.dumps(stage), encoding="utf-8")
            argv += ["--" + name, str(path)]
        out = self.folder / "blocked.html"
        old = self.exe.read_bytes()
        self.exe.write_bytes(old.replace(b"synthetic", b"synThetic"))
        self.assertEqual(self.exe.stat().st_size, len(old))
        self.assertEqual(main(argv + ["--exe", str(self.exe), "--out", str(out)]), 1)
        self.assertFalse(out.exists())

    def test_unknown_review_category_or_filename_rejected(self):
        q = copy.deepcopy(self.queue)
        q["unresolved_entries_requiring_review"][0]["unresolved_category"] = "first_party_candidate"
        with self.assertRaises(ValueError):
            render_review_worksheet(q)
        q = copy.deepcopy(self.queue)
        q["unresolved_entries_requiring_review"][0]["archive_entry"] = "bad\nname"
        with self.assertRaises(ValueError):
            render_review_worksheet(q)


if __name__ == "__main__":
    unittest.main()
