"""Exact-EXE manual license progress: synthetic-only, never certifies rights."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_notice_review_queue import build_review_queue
from scripts.track_notice_review import (
    STAGES, create_progress, main, summarize_progress,
)
from test_notice_gap_ledger import fixture


class ReviewProgressTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.exe = self.root / "synthetic.exe"
        self.exe.write_bytes(b"MZ synthetic inert EXE for provenance test")
        self.stages = fixture()
        sha = hashlib.sha256(self.exe.read_bytes()).hexdigest()
        for stage in self.stages:
            stage["exe_sha256"] = sha
        self.stages[2]["records"][0]["initial_category"] = (
            "unresolved_native_or_system_binary"
        )
        self.queue = build_review_queue(*self.stages, self.exe)

    def test_template_anchors_exact_binary_and_never_approves(self) -> None:
        progress = create_progress(self.queue, self.exe)
        self.assertEqual(progress["entry_count"], 1)
        self.assertEqual(progress["entries"], [{
            "archive_entry": "mystery.dll", "review_stage": "UNREVIEWED",
        }])
        self.assertEqual(progress["exe_sha256"], self.queue["exe_sha256"])
        self.assertFalse(progress["customer_release_ready"])
        self.assertFalse(progress["license_compliance_certified"])
        self.assertNotIn(str(self.root), json.dumps(progress))
        self.assertNotIn("MZ synthetic", json.dumps(progress))

    def test_editable_investigation_stages_never_unlock_release(self) -> None:
        progress = create_progress(self.queue, self.exe)
        for stage in STAGES:
            progress["entries"][0]["review_stage"] = stage
            report = summarize_progress(self.queue, self.exe, progress)
            self.assertEqual(sum(report["investigation_stage_counts"].values()), 1)
            self.assertEqual(report["investigation_stage_counts"][stage], 1)
            self.assertTrue(report["human_review_still_required"])
            self.assertFalse(report["customer_release_ready"])
            self.assertIn("RETAIL_RELEASE_BLOCKED", report["status"])

    def test_stale_queue_or_changed_binary_rejected(self) -> None:
        progress = create_progress(self.queue, self.exe)
        wrong_queue = copy.deepcopy(self.queue)
        wrong_queue["unresolved_entries_requiring_review"][0][
            "source_byte_match"
        ] = "byte_identical_to_recorded_build_source"
        with self.assertRaises(ValueError):
            summarize_progress(wrong_queue, self.exe, progress)
        original = self.exe.read_bytes()
        self.exe.write_bytes(original.replace(b"synthetic", b"synThetic", 1))
        self.assertEqual(len(original), self.exe.stat().st_size)
        with self.assertRaises(ValueError):
            summarize_progress(self.queue, self.exe, progress)

    def test_duplicate_missing_renamed_invalid_or_approved_rows_rejected(self) -> None:
        template = create_progress(self.queue, self.exe)
        cases = []
        for transform in (
            lambda p: p["entries"].clear(),
            lambda p: p["entries"].append(copy.deepcopy(p["entries"][0])),
            lambda p: p["entries"][0].update(archive_entry="other.dll"),
            lambda p: p["entries"][0].update(review_stage="APPROVED"),
            lambda p: p.update(customer_release_ready=True),
            lambda p: p.update(third_party_notice_ready=True),
            lambda p: p.update(extra_payload="secret"),
        ):
            candidate = copy.deepcopy(template)
            transform(candidate)
            cases.append(candidate)
        for candidate in cases:
            with self.subTest(progress=candidate):
                with self.assertRaises(ValueError):
                    summarize_progress(self.queue, self.exe, candidate)

    def test_cli_creates_private_template_and_summary_without_overwrite(self) -> None:
        queue = self.root / "queue.json"
        queue.write_text(json.dumps(self.queue), encoding="utf-8")
        template = self.root / "private-progress.json"
        args = ["--queue", str(queue), "--exe", str(self.exe), "--out", str(template)]
        self.assertEqual(main(args), 0)
        raw = template.read_bytes()
        self.assertEqual(main(args), 1)
        self.assertEqual(template.read_bytes(), raw)
        edited = json.loads(template.read_text(encoding="utf-8"))
        edited["entries"][0]["review_stage"] = "REFERENCES_FOUND"
        template.write_text(json.dumps(edited), encoding="utf-8")
        summary = self.root / "private-summary.json"
        summary_args = [
            "--queue", str(queue), "--exe", str(self.exe),
            "--progress", str(template), "--out", str(summary),
        ]
        self.assertEqual(main(summary_args), 0)
        output = json.loads(summary.read_text(encoding="utf-8"))
        self.assertEqual(output["investigation_stage_counts"]["REFERENCES_FOUND"], 1)
        self.assertFalse(output["customer_release_ready"])
        self.assertEqual(main(summary_args), 1)

    def test_cli_rejects_duplicate_json_keys_and_forged_queue(self) -> None:
        queue = self.root / "queue.json"
        queue.write_text('{"format":"x","format":"y"}', encoding="utf-8")
        output = self.root / "never-created.json"
        self.assertEqual(main([
            "--queue", str(queue), "--exe", str(self.exe), "--out", str(output),
        ]), 1)
        self.assertFalse(output.exists())

    def test_no_source_path_or_original_license_in_summary(self) -> None:
        tracker = create_progress(self.queue, self.exe)
        result = summarize_progress(self.queue, self.exe, tracker)
        text = json.dumps(result, ensure_ascii=False)
        self.assertNotIn("mystery.dll", text)
        self.assertNotIn(str(self.root), text)
        self.assertNotIn("LICENSE_TEXT", text)
        self.assertFalse(result["customer_release_ready"])


if __name__ == "__main__":
    unittest.main()
