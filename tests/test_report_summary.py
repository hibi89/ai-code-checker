"""Synthetic report-summary regression tests; no external service or source execution."""
from __future__ import annotations

import unittest
from dataclasses import replace

from offline_core import scan_text
from offline_report import _breakdowns, build_report, render_html, render_markdown


class ReportSummaryTests(unittest.TestCase):
    def test_language_rule_and_severity_totals_are_consistent(self) -> None:
        source = (
            "===== FILE: app/main.py =====\n"
            "eval('1 + 1')\n"
            "===== FILE: web/client.js =====\n"
            "const answer = 42;\n"
            "===== FILE: web/types.ts =====\n"
            "const answer: number = 42;\n"
        )
        report = build_report(scan_text(source, filename="bundle.txt"))
        severity, rules, languages = _breakdowns(report)
        self.assertEqual(sum(n for _, n in severity), len(report.findings))
        self.assertEqual(sum(n for _, n in rules), len(report.findings))
        self.assertEqual(dict(languages), {"JavaScript": 1, "Python": 1, "TypeScript": 1})
        self.assertEqual(sum(n for _, n in languages), report.scan.counts["enumerated"])
        self.assertIn("PY-DYNAMIC-EXEC", dict(rules))
        for rendered in (render_html(report), render_markdown(report)):
            self.assertIn("심각도별 발견 후보", rendered)
            self.assertIn("규칙별 발견 후보", rendered)
            self.assertIn("언어별 파일 분포", rendered)
            self.assertIn("확장자", rendered)

    def test_no_findings_remains_zero_not_safe_certification(self) -> None:
        report = build_report(scan_text("pass\n", filename="main.py"))
        severity, rules, language = _breakdowns(report)
        self.assertFalse(severity)
        self.assertFalse(rules)
        self.assertEqual(language, [("Python", 1)])
        rendered = render_html(report)
        self.assertIn("<td>없음</td><td>0</td>", rendered)
        self.assertIn("안전 판정은 아닙니다", rendered)
        self.assertNotIn("<script", rendered)

    def test_unverified_candidate_stays_counted_but_is_not_certified(self) -> None:
        scan = scan_text("eval('1 + 1')\n", filename="main.py")
        scan.findings[0] = replace(scan.findings[0], evidence="forged-evidence")
        report = build_report(scan)
        self.assertEqual(report.status, "partial")
        self.assertEqual(report.verified_count, 0)
        severity, rules, _ = _breakdowns(report)
        self.assertEqual(sum(n for _, n in severity), 1)
        self.assertEqual(dict(rules)["PY-DYNAMIC-EXEC"], 1)
        self.assertIn("근거 대조 실패", render_html(report))
        self.assertNotIn("forged-evidence", render_html(report))

    def test_static_report_has_responsive_a4_print_without_remote_assets(self) -> None:
        report = build_report(scan_text("eval('1')\n", language="python"))
        page = render_html(report)
        self.assertIn("@page{size:A4;", page)
        self.assertIn("@media print{", page)
        self.assertIn("thead{display:table-header-group}", page)
        self.assertIn("@media(max-width:720px)", page)
        self.assertIn("break-inside:avoid", page)
        self.assertIn("font-family:", page)
        self.assertNotIn("@import", page)
        self.assertNotIn("url(", page)
        self.assertNotIn("http://", page)
        self.assertNotIn("https://", page)
        self.assertNotIn("<script", page)
        self.assertNotIn("<link", page)

    def test_report_does_not_load_external_assets(self) -> None:
        report = build_report(scan_text("eval('1')\n", filename="main.py"))
        page = render_html(report)
        self.assertIn("default-src 'none'", page)
        self.assertIn("script-src 'none'", page)
        self.assertNotIn("<script", page)
        self.assertNotIn("<link", page)


    def test_redaction_observations_are_separate_from_other_risks(self) -> None:
        token = "ghp_" + "123456789012345678901234567890"
        source = (
            f'api_key = "{token}"\n'
            'email = "synthetic@sample.invalid"\n'
            'eval("1")\n'
        )
        report = build_report(scan_text(source, filename="sample.py"))
        redactions = [row for row in report.findings if row.rule_id.startswith("GEN-REDACT-")]
        self.assertEqual(len(redactions), 2)
        self.assertEqual(len(report.findings) - len(redactions), 1)
        self.assertEqual(report.status, "complete")
        for rendered in (render_html(report), render_markdown(report)):
            self.assertIn("기타 규칙 후보 1", rendered)
            self.assertIn("로컬 마스킹 처리 관찰 2", rendered)
            self.assertIn("외부 전송", rendered)
            self.assertIn("실제 유출", rendered)
            self.assertIn("정적 규칙 일치 후보", rendered)
            self.assertNotIn(token, rendered)
        self.assertIn("GEN-REDACT-SECRET", {row.rule_id for row in report.findings})
        self.assertIn("GEN-REDACT-PII", {row.rule_id for row in report.findings})

    def test_clean_report_has_zero_redaction_observations(self) -> None:
        report = build_report(scan_text("eval('synthetic')\n", filename="sample.py"))
        for rendered in (render_html(report), render_markdown(report)):
            self.assertIn("기타 규칙 후보 1", rendered)
            self.assertIn("로컬 마스킹 처리 관찰 0", rendered)


if __name__ == "__main__":
    unittest.main()
