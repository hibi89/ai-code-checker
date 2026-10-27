"""P2-7: imported builtins eval/exec must preserve alias provenance."""
from __future__ import annotations

import unittest

from offline_core import scan_text
from offline_report import build_report


def risks(code: str) -> list[tuple[str, int]]:
    report = build_report(scan_text(code, filename="synthetic.py"))
    if report.validation_issues:
        raise AssertionError("unverified synthetic source citation")
    return [
        (entry.rule_id, entry.finding.start_line)
        for entry in report.findings if entry.rule_id == "PY-DYNAMIC-EXEC"
    ]


class BuiltinsProvenanceTests(unittest.TestCase):
    def test_imported_builtins_calls_and_citations(self) -> None:
        cases = (
            ("import builtins\nbuiltins.eval(value)\n", 2),
            ("import builtins as b\nb.exec(src)\n", 2),
            ("from builtins import eval as evaluate\nevaluate(data)\n", 2),
            ("from builtins import exec as run_code\nrun_code(data)\n", 2),
            ("from builtins import eval\neval(value)\n", 2),
            ("import builtins as b\ndef f():\n    b.eval(value)\n", 3),
        )
        for code, line in cases:
            with self.subTest(code=code):
                self.assertEqual(risks(code), [("PY-DYNAMIC-EXEC", line)])

    def test_unrelated_names_rebinding_and_shadowing_are_not_risks(self) -> None:
        cases = (
            "service.eval(value)\n",
            "builtins.eval(value)\nimport builtins\n",
            "import builtins as b\nb = fake\nb.eval(value)\n",
            "from builtins import exec as x\nx = fake\nx(value)\n",
            "from fake import exec as command\ncommand(value)\n",
            "import builtins as b\ndef f(b):\n    b.exec(value)\n",
            "def run(eval):\n    eval(value)\n",
        )
        for code in cases:
            with self.subTest(code=code):
                self.assertEqual(risks(code), [])

    def test_guarded_import_provenance_stays_in_the_same_branch(self) -> None:
        self.assertEqual(
            risks("if enable:\n    import builtins as b\n    b.exec(value)\n"),
            [("PY-DYNAMIC-EXEC", 3)],
        )
        self.assertEqual(
            risks("if enable:\n    import builtins as b\nb.exec(value)\n"), [],
        )
        self.assertEqual(
            risks("if enable:\n    from builtins import eval as e\nelse:\n    e(value)\n"), [],
        )


if __name__ == "__main__":
    unittest.main()
