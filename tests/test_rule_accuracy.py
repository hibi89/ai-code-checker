"""P1-D tests: frozen synthetic labels, rule scope and no user source execution."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from offline_core import scan_text
from offline_report import build_report
from scripts.evaluate_rule_accuracy import JS_TS_LIMITED, PYTHON_CASES, evaluate


class RuleAccuracyTests(unittest.TestCase):
    def test_all_labeled_python_cases_are_counted_and_unsupported_cases_remain(self):
        result = evaluate()
        self.assertEqual(result["python_cases"], len(PYTHON_CASES))
        self.assertEqual(result["js_ts_limited_cases_excluded_from_metric"], len(JS_TS_LIMITED))
        self.assertGreaterEqual(result["tp"], 12)
        self.assertEqual(result["fp"], 0)
        self.assertGreaterEqual(result["fn"], 2)  # Remaining unsupported dynamic indirection.
        self.assertEqual(result["real_world_accuracy"], "UNVERIFIED")
        self.assertEqual(result["customer_release_ready"], False)

    def test_irrelevant_attribute_shell_true_not_a_subprocess_finding(self):
        report = build_report(scan_text("utility.run(cmd, shell=True)\n", filename="x.py"))
        self.assertFalse(any(x.rule_id == "PY-SHELL" for x in report.findings))

    def test_python_comment_or_string_verify_false_not_a_tls_finding(self):
        src = "# verify=False\nprint('verify=False')\nverify = False\n"
        report = build_report(scan_text(src, filename="x.py"))
        self.assertFalse(any(x.rule_id == "GEN-TLS-VERIFY" for x in report.findings))

    def test_actual_aliased_subprocess_and_requests_imports(self):
        code = ("import subprocess as sp\n"
                "from requests import get as fetch\n"
                "sp.run(cmd, shell=True)\n"
                "fetch(url, verify=False)\n")
        report = build_report(scan_text(code, filename="x.py"))
        self.assertEqual(
            [(item.rule_id, item.finding.start_line) for item in report.findings],
            [("PY-SHELL", 3), ("GEN-TLS-VERIFY", 4)],
        )
        self.assertEqual(report.status, "complete")
        self.assertEqual(report.verified_count, 2)

    def test_import_shadow_suppresses_false_positive(self):
        cases = (
            "import subprocess as sp\nsp = other\nsp.run(cmd, shell=True)\n",
            "from pickle import loads as loader\nloader = other\nloader(data)\n",
            "import requests as req\ndef check(req):\n    req.get(url, verify=False)\n",
            "import subprocess as sp\n[sp.run(cmd, shell=True) for sp in group]\n",
            "def f(exec):\n    exec(code)\n",
        )
        for code in cases:
            with self.subTest(code=code):
                report = build_report(scan_text(code, filename="fixture.py"))
                self.assertEqual(report.findings, ())

    def test_positive_before_rebinding_is_preserved(self):
        source = "import subprocess as sp\nsp.run(cmd, shell=True)\nsp = other\nsp.run(cmd, shell=True)\n"
        report = build_report(scan_text(source, filename="fixture.py"))
        self.assertEqual(
            [(item.rule_id, item.finding.start_line) for item in report.findings],
            [("PY-SHELL", 2)],
        )

    def test_unshadowed_function_call_keeps_module_provenance(self):
        source = "import subprocess as sp\ndef f():\n    sp.run(cmd, shell=True)\n"
        report = build_report(scan_text(source, filename="fixture.py"))
        self.assertEqual(
            [(item.rule_id, item.finding.start_line) for item in report.findings],
            [("PY-SHELL", 3)],
        )

    def test_sql_interpolation_improves_detection_without_constant_false_alarms(self):
        cases = (
            ('cursor.execute("SELECT * FROM users WHERE id=%s" % user)\n', ("PY-SQL-CONCAT", 1)),
            ('cursor.execute("SELECT * FROM users WHERE id={id}".format(id=user))\n', ("PY-SQL-CONCAT", 1)),
            ('cursor.execute("DELETE FROM users WHERE id={id}".format_map(data))\n', ("PY-SQL-CONCAT", 1)),
            ('sql = "SELECT * FROM users WHERE id=%s" % user\ncursor.execute(sql)\n', ("PY-SQL-CONCAT", 2)),
        )
        for code, expected in cases:
            with self.subTest(code=code):
                report = build_report(scan_text(code, filename="synthetic.py"))
                self.assertEqual(
                    [(r.rule_id, r.finding.start_line) for r in report.findings],
                    [expected],
                )
                self.assertEqual(report.verified_count, 1)

    def test_sql_literal_and_parameter_cases_are_not_false_positives(self):
        safe = (
            'cursor.execute("SELECT * FROM users WHERE id=%s", (user,))\n',
            'cursor.execute("SELECT * FROM users WHERE id=%s" % 42)\n',
            'cursor.execute("SELECT * FROM users WHERE id={}".format(42))\n',
            'cursor.execute("SELECT * FROM users WHERE id={id}".format_map({"id": 42}))\n',
            'cursor.execute("SELECT * FROM {{table}}".format(user))\n',
            'cursor.execute("SELECT * FROM users".format(user))\n',
            'cursor.execute("SELECT %% FROM users" % user)\n',
            'print("SELECT * FROM users WHERE id={}".format(user))\n',
        )
        for code in safe:
            with self.subTest(code=code):
                report = build_report(scan_text(code, filename="synthetic.py"))
                self.assertFalse(any(r.rule_id == "PY-SQL-CONCAT" for r in report.findings))

    def test_literal_dynamic_import_risks_use_exact_original_line(self):
        cases = (
            ('getattr(__import__("builtins"), "eval")(value)\n', "PY-DYNAMIC-EXEC"),
            ('__import__("builtins").eval(value)\n', "PY-DYNAMIC-EXEC"),
            ('getattr(__import__("builtins"), "exec")(code)\n', "PY-DYNAMIC-EXEC"),
            ('__import__("subprocess").run(cmd, shell=True)\n', "PY-SHELL"),
            ('getattr(__import__("subprocess"), "Popen")(cmd, shell=True)\n', "PY-SHELL"),
        )
        for sample, expected in cases:
            with self.subTest(sample=sample):
                report = build_report(scan_text("# harmless\n" + sample, filename="fixture.py"))
                self.assertEqual(
                    [(r.rule_id, r.finding.start_line) for r in report.findings],
                    [(expected, 2)],
                )
                self.assertEqual(report.verified_count, 1)
                self.assertEqual(report.status, "complete")

    def test_literal_dynamic_import_shadow_or_nonliteral_is_not_matched(self):
        safe = (
            '__import__("subprocess").run(cmd, shell=False)\n',
            '__import__(module).run(cmd, shell=True)\n',
            '__import__("another").run(cmd, shell=True)\n',
            '__import__("subprocess", globals()).run(cmd, shell=True)\n',
            'def f(__import__):\n    return __import__("subprocess").run(cmd, shell=True)\n',
            'def f(getattr):\n    return getattr(__import__("builtins"), "eval")(code)\n',
            '__import__ = other\n__import__("subprocess").run(cmd, shell=True)\n',
            'getattr = other\ngetattr(__import__("builtins"), "eval")(value)\n',
            'getattr(__import__("builtins"), "eval")\n',
            'getattr(__import__("builtins"), attr)(value)\n',
            'getattr(__import__("builtins"), "eval", fallback)(value)\n',
        )
        for sample in safe:
            with self.subTest(sample=sample):
                report = build_report(scan_text(sample, filename="fixture.py"))
                self.assertEqual(report.findings, ())

    def test_js_ts_do_not_claim_ast_analyzer(self):
        for filename, code in (("x.js", "fetch(url);\n"), ("x.ts", "let a: number = 1;\n")):
            scan = scan_text(code, filename=filename)
            self.assertEqual(scan.counts["limited"], 1)
            self.assertEqual(scan.status, "partial")

    def test_source_code_is_not_executed_and_no_provider_connection(self):
        # Parsing malicious-looking text must never execute the statement.
        with patch("socket.create_connection", side_effect=AssertionError("remote forbidden")):
            scan = scan_text("__import__('os').system('no-op')\n", filename="x.py")
        self.assertEqual(scan.status, "complete")


if __name__ == "__main__":
    unittest.main()
