"""Dense synthetic findings and evidence validation must stay linear in lookup count."""
from __future__ import annotations

import unittest
from dataclasses import replace
from unittest.mock import PropertyMock, patch

from code_input import CodeBundle
from offline_core import scan_text
from offline_report import build_report, render_markdown


class DenseFindingReportTests(unittest.TestCase):
    def test_dense_single_source_reuses_lines_and_preserves_citations(self) -> None:
        source_text = "".join(f"eval(item_{index})\n" for index in range(1200))
        scan = scan_text(source_text, filename="dense.py")
        self.assertEqual(scan.status, "complete")
        self.assertEqual(len(scan.findings), 1200)
        source = scan.bundle.files[0]
        self.assertIs(source.source_lines, source.source_lines)
        self.assertEqual(source.line_count, 1200)
        self.assertEqual(source.text, source_text)

        real_map = scan.bundle.file_map
        with patch.object(CodeBundle, "file_map", new_callable=PropertyMock, return_value=real_map) as mocked:
            report = build_report(scan)
        self.assertEqual(mocked.call_count, 1)
        self.assertEqual(report.status, "complete")
        self.assertEqual(len(report.findings), 1200)
        self.assertEqual(report.verified_count, 1200)
        self.assertEqual(report.findings[0].origin_line, 1)
        self.assertEqual(report.findings[-1].origin_line, 1200)
        self.assertEqual(report.findings[-1].excerpt, "eval(item_1199)")

    def test_invalid_dense_evidence_still_fails_closed(self) -> None:
        scan = scan_text("eval(first)\neval(second)\n", filename="dense.py")
        original = scan.findings[1]
        scan.findings[1] = replace(original, evidence="fabricated-source", citation_verified=True)
        report = build_report(scan)
        self.assertEqual(report.status, "partial")
        self.assertEqual(report.verified_count, 1)
        self.assertEqual(len(report.validation_issues), 1)
        self.assertNotIn("fabricated-source", render_markdown(report))


if __name__ == "__main__":
    unittest.main()
