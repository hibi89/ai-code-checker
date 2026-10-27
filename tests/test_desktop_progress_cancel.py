"""Synthetic cooperative progress/cancel regressions; no network, AI, or customer code."""
from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from desktop_core import ScanCancelled, ScanControl, ScanRequest, inspect_input, run_scan
from offline_core import scan_text


class CooperativeProgressTests(unittest.TestCase):
    def test_incremental_scan_matches_previous_findings_and_coverage(self) -> None:
        source = (
            "===== FILE: a.py =====\n"
            "eval('1+1')\n"
            "===== FILE: b.py =====\n"
            "import pickle\npickle.loads(b'data')\n"
            "===== FILE: web/client.js =====\n"
            "const x = 1;\n"
        )
        original = scan_text(source, filename="bundle.txt")
        events: list[tuple[int, int]] = []
        scanned = scan_text(
            source, filename="bundle.txt",
            on_progress=lambda done, total: events.append((done, total)),
            check_cancelled=ScanControl().check,
        )
        self.assertEqual(scanned.findings, original.findings)
        self.assertEqual(scanned.coverage, original.coverage)
        self.assertEqual(scanned.counts, original.counts)
        self.assertEqual(events, [(1, 3), (2, 3), (3, 3)])

    def test_cancel_at_first_scanned_file_leaves_no_reports(self) -> None:
        source = (
            "===== FILE: a.py =====\nprint('a')\n"
            "===== FILE: b.py =====\nprint('b')\n"
            "===== FILE: c.py =====\nprint('c')\n"
        )
        updates = []
        control = ScanControl()
        def update(item) -> None:
            updates.append(item)
            if item.phase == "scan" and item.completed == 1:
                control.cancel()
        control.on_update = update
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "fresh"
            with self.assertRaises(ScanCancelled):
                run_scan(ScanRequest("paste", text=source), output_dir, "cancelled", control=control)
            self.assertFalse(output_dir.exists())
        self.assertEqual(updates[0].phase, "reading")
        self.assertEqual(updates[-1].completed, 1)

    def test_cancel_at_publication_boundary_writes_no_partial_pair(self) -> None:
        control = ScanControl()
        seen: list[str] = []
        def update(item) -> None:
            seen.append(item.phase)
            if item.phase == "publishing":
                control.cancel()
        control.on_update = update
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "reports"
            with self.assertRaises(ScanCancelled):
                run_scan(ScanRequest("paste", text="eval('1')\n", language="python"),
                         dest, "not-published", control=control)
            self.assertFalse(dest.exists())
        self.assertEqual(seen[-1], "publishing")
        self.assertNotIn("done", seen)

    def test_complete_scan_emits_monotone_progress_and_writes_once(self) -> None:
        updates = []
        control = ScanControl(on_update=updates.append)
        with tempfile.TemporaryDirectory() as tmp:
            result = run_scan(
                ScanRequest("paste", text="eval('1')\n", language="python"),
                Path(tmp) / "reports", "success", control=control,
            )
            self.assertEqual(result.status, "complete")
            self.assertTrue(result.html_path.is_file())
            self.assertTrue(result.markdown_path.is_file())
        phases = [item.phase for item in updates]
        self.assertEqual(phases, ["reading", "scan", "report", "publishing", "done"])
        self.assertEqual((updates[1].completed, updates[1].total), (1, 1))

    def test_pre_cancelled_input_preview_does_not_read_files(self) -> None:
        control = ScanControl()
        control.cancel()
        with patch("desktop_core._base_bundle", side_effect=AssertionError("input unexpectedly read")):
            with self.assertRaises(ScanCancelled):
                inspect_input(ScanRequest("paste", text="print(1)"), control=control)

    def test_preview_cancel_after_read_does_not_claim_completion(self) -> None:
        control = ScanControl()
        control.on_update = lambda update: control.cancel() if update.phase == "reading" else None
        with self.assertRaises(ScanCancelled):
            inspect_input(ScanRequest("paste", text="print(1)"), control=control)

    def test_zip_remains_unchanged_when_cancelled_during_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "source.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("a.py", "print('a')\n")
                archive.writestr("b.py", "print('b')\n")
            raw = archive_path.read_bytes()
            control = ScanControl()
            control.on_update = (
                lambda item: control.cancel()
                if item.phase == "scan" and item.completed == 1 else None
            )
            with self.assertRaises(ScanCancelled):
                run_scan(ScanRequest("path", source=str(archive_path)),
                         Path(tmp) / "out", "cancel", control=control)
            self.assertEqual(archive_path.read_bytes(), raw)
            self.assertFalse((Path(tmp) / "out").exists())


if __name__ == "__main__":
    unittest.main()
