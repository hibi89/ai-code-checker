"""P1-Q: option literal truthiness and SQL constant interpolation regressions."""
from __future__ import annotations

import unittest

from offline_core import scan_text
from offline_report import build_report


def rules(code: str) -> tuple[tuple[str, int | None], ...]:
    report = build_report(scan_text(code, filename="synthetic.py"))
    return tuple((row.rule_id, row.finding.start_line) for row in report.findings)


class OptionLiteralAccuracyTests(unittest.TestCase):
    def test_subprocess_truthy_literals_alert(self) -> None:
        for literal in ("True", "1", "-1", "1.0", "'yes'", "b'yes'"):
            with self.subTest(literal=literal):
                code = f"import subprocess\nsubprocess.run(cmd, shell={literal})\n"
                self.assertEqual(rules(code), (("PY-SHELL", 2),))

    def test_subprocess_false_and_unknown_values_do_not_alert(self) -> None:
        for literal in ("False", "0", "0.0", "''", "None", "shell_option"):
            with self.subTest(literal=literal):
                code = f"import subprocess\nsubprocess.run(cmd, shell={literal})\n"
                self.assertEqual(rules(code), ())

    def test_requests_explicit_falsey_literals_alert(self) -> None:
        for literal in ("False", "0", "0.0", "''", 'b""'):
            with self.subTest(literal=literal):
                code = f"import requests\nrequests.get(url, verify={literal})\n"
                self.assertEqual(rules(code), (("GEN-TLS-VERIFY", 2),))

    def test_requests_none_and_truthy_do_not_alert(self) -> None:
        for literal in ("None", "True", "1", "'custom-ca.pem'", "verify_option"):
            with self.subTest(literal=literal):
                code = f"import requests\nrequests.get(url, verify={literal})\n"
                self.assertEqual(rules(code), ())

    def test_only_known_imported_apis_match(self) -> None:
        code = ("service.run(cmd, shell=1)\n"
                "client.get(url, verify=0)\n")
        self.assertEqual(rules(code), ())

    def test_sql_literal_only_formatted_strings_stay_quiet(self) -> None:
        cases = (
            'cursor.execute(f"SELECT {1} FROM t")\n',
            'cursor.execute(f"SELECT {1:02d} FROM t")\n',
            'cursor.execute("SELECT " + f"{1}" + " FROM t")\n',
            'query = f"SELECT {1} FROM t"\ncursor.execute(query)\n',
            'query = "SELECT " + f"{1:02d}"\ncursor.execute(query)\n',
        )
        for code in cases:
            with self.subTest(code=code):
                self.assertEqual(rules(code), ())

    def test_sql_variable_interpolation_remains_flagged(self) -> None:
        code = 'cursor.execute(f"SELECT * FROM t WHERE id={user_id}")\n'
        self.assertEqual(rules(code), (("PY-SQL-CONCAT", 1),))

    def test_sql_batch_and_script_calls_detect_dynamic_queries(self) -> None:
        cases = (
            ('cursor.executemany(f"INSERT INTO t VALUES ({value})", rows)\n', 1),
            ('sql = "UPDATE t SET x=" + value\ncursor.executemany(sql, rows)\n', 2),
            ('db.executescript(f"DROP TABLE {table}")\n', 1),
            ('sql = "DELETE FROM t WHERE id=" + value\ndb.executescript(sql)\n', 2),
        )
        for source, line in cases:
            with self.subTest(source=source):
                self.assertEqual(rules(source), (("PY-SQL-CONCAT", line),))

    def test_sql_bound_and_static_batch_script_calls_stay_quiet(self) -> None:
        cases = (
            'cursor.executemany("INSERT INTO t VALUES (?)", rows)\n',
            'db.executescript("CREATE TABLE t(id INTEGER);")\n',
            'cursor.execute_many(f"DELETE FROM t WHERE x={value}", rows)\n',
            'not_sql.executemany(f"render {name}", rows)\n',
            'sql = "DELETE FROM t WHERE x=?"\ncursor.executemany(sql, rows)\n',
        )
        for source in cases:
            with self.subTest(source=source):
                self.assertEqual(rules(source), ())

    def test_sql_dynamic_format_width_stays_candidate(self) -> None:
        code = 'cursor.execute(f"SELECT {1:{width}} FROM t")\n'
        self.assertEqual(rules(code), (("PY-SQL-CONCAT", 1),))


    def test_literal_dynamic_import_pickle_loads_and_load_are_candidates(self) -> None:
        cases = (
            '__import__("pickle").loads(data)\n',
            'getattr(__import__("pickle"), "load")(stream)\n',
        )
        for code in cases:
            with self.subTest(code=code):
                self.assertEqual(rules(code), (("PY-PICKLE", 1),))

    def test_literal_dynamic_import_requests_verify_false_is_candidate(self) -> None:
        cases = (
            '__import__("requests").get(url, verify=False)\n',
            'getattr(__import__("requests"), "post")(url, verify=0)\n',
        )
        for code in cases:
            with self.subTest(code=code):
                self.assertEqual(rules(code), (("GEN-TLS-VERIFY", 1),))

    def test_dynamic_import_provenance_requires_unshadowed_literal_api(self) -> None:
        cases = (
            '__import__(module).loads(data)\n',
            '__import__("json").loads(data)\n',
            '__import__("pickle", globals()).loads(data)\n',
            '__import__ = fake\n__import__("pickle").loads(data)\n',
            'getattr = fake\ngetattr(__import__("pickle"), "loads")(data)\n',
            '__import__("requests").get(url, verify=True)\n',
            '__import__("requests").get(url, verify=option)\n',
            '__import__("other").get(url, verify=False)\n',
            'getattr(__import__("requests"), method)(url, verify=False)\n',
        )
        for code in cases:
            with self.subTest(code=code):
                self.assertEqual(rules(code), ())


if __name__ == "__main__":
    unittest.main()
