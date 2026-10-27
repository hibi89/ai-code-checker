"""P1-O: conservative SQL query local-binding regressions (synthetic only)."""
from __future__ import annotations

import unittest

from offline_core import scan_text
from offline_report import build_report


def sql_lines(code: str) -> list[int | None]:
    report = build_report(scan_text(code, filename="synthetic.py"))
    return [item.finding.start_line for item in report.findings
            if item.rule_id == "PY-SQL-CONCAT"]


class SqlLocalBindingTests(unittest.TestCase):
    def test_module_level_local_sql_query(self):
        code = 'query = f"SELECT * FROM users WHERE id={uid}"\nconn.execute(query)\n'
        self.assertEqual(sql_lines(code), [2])

    def test_function_level_local_sql_query(self):
        code = ('def get_record(uid):\n'
                '    query = f"SELECT * FROM users WHERE id={uid}"\n'
                '    return cursor.execute(query)\n')
        self.assertEqual(sql_lines(code), [3])

    def test_function_direct_expression_sql_query(self):
        code = ('def get_record(uid):\n'
                '    query = f"SELECT * FROM users WHERE id={uid}"\n'
                '    cursor.execute(query)\n')
        self.assertEqual(sql_lines(code), [3])

    def test_annotated_assignment_sql_query(self):
        code = ('query: str = "SELECT * FROM users WHERE id=" + uid\n'
                'cursor.execute(query)\n')
        self.assertEqual(sql_lines(code), [2])

    def test_safe_rebinding_and_conditional_shadow_do_not_alert(self):
        cases = (
            'query = f"SELECT * FROM users WHERE id={uid}"\n'
            'query = "SELECT * FROM users WHERE id=?"\n'
            'cursor.execute(query)\n',
            'query = f"SELECT * FROM users WHERE id={uid}"\n'
            'if flag:\n    query = safe_query\ncursor.execute(query)\n',
            'query = f"SELECT * FROM users WHERE id={uid}"\n'
            'query += " ORDER BY id"\ncursor.execute(query)\n',
            'query = f"SELECT * FROM users WHERE id={uid}"\n'
            'del query\ncursor.execute(query)\n',
            'query = f"SELECT * FROM users WHERE id={uid}"\n'
            'from config import query\ncursor.execute(query)\n',
            'query = f"SELECT * FROM users WHERE id={uid}"\n'
            'def caller(query):\n    cursor.execute(query)\n',
        )
        for code in cases:
            with self.subTest(code=code):
                self.assertEqual(sql_lines(code), [])

    def test_no_cross_scope_or_conditional_origin_guess(self):
        code = ('def prepare(uid):\n'
                '    query = f"SELECT * FROM t WHERE id={uid}"\n'
                'def consume(query):\n'
                '    cursor.execute(query)\n')
        self.assertEqual(sql_lines(code), [])

    def test_direct_if_arm_query(self):
        code = ('if enabled:\n'
                '    query = f"SELECT * FROM users WHERE id={uid}"\n'
                '    cursor.execute(query)\n')
        self.assertEqual(sql_lines(code), [3])

    def test_direct_else_arm_query(self):
        code = ('if enabled:\n'
                '    print("skip")\n'
                'else:\n'
                '    query = "DELETE FROM users WHERE id=" + uid\n'
                '    cursor.execute(query)\n')
        self.assertEqual(sql_lines(code), [5])

    def test_return_inside_if_arm(self):
        code = ('def read(uid):\n'
                '    if enabled:\n'
                '        query = f"SELECT * FROM users WHERE id={uid}"\n'
                '        return cursor.execute(query)\n')
        self.assertEqual(sql_lines(code), [4])

    def test_no_cross_arm_or_outer_scope_guess(self):
        cases = (
            'if enabled:\n    query = f"SELECT * FROM t WHERE x={v}"\n'
            'else:\n    cursor.execute(query)\n',
            'query = f"SELECT * FROM t WHERE x={v}"\n'
            'if enabled:\n    cursor.execute(query)\n',
            'if enabled:\n    query = f"SELECT * FROM t WHERE x={v}"\n'
            'cursor.execute(query)\n',
            'def outer(v):\n    query = f"SELECT * FROM t WHERE x={v}"\n'
            '    def inner():\n        cursor.execute(query)\n',
        )
        for code in cases:
            with self.subTest(code=code):
                self.assertEqual(sql_lines(code), [])

    def test_branch_reassignment_invalidates(self):
        code = ('if enabled:\n'
                '    query = f"SELECT * FROM t WHERE x={v}"\n'
                '    if override:\n'
                '        query = "SELECT * FROM t WHERE x=?"\n'
                '    cursor.execute(query)\n')
        self.assertEqual(sql_lines(code), [])

    def test_literal_only_sql_stays_quiet(self):
        cases = (
            'cursor.execute("SELECT * " + "FROM t WHERE id=?")\n',
            'query = "SELECT * FROM t" + " WHERE id=?"\ncursor.execute(query)\n',
            'query = f"SELECT * FROM t"\ncursor.execute(query)\n',
            'query = ("SELECT * FROM " + "t") + " WHERE id=?"\n'
            'cursor.execute(query)\n',
        )
        for code in cases:
            with self.subTest(code=code):
                self.assertEqual(sql_lines(code), [])

    def test_nested_return_expression_not_claimed(self):
        code = ('def f(v):\n'
                '    query = f"SELECT * FROM t WHERE x={v}"\n'
                '    return wrapper(cursor.execute(query))\n')
        self.assertEqual(sql_lines(code), [])

    def test_direct_interpolation_rule_stays_enabled(self):
        self.assertEqual(sql_lines('cursor.execute(f"DELETE FROM t WHERE x={value}")\n'), [1])


if __name__ == "__main__":
    unittest.main()
