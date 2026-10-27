"""Regression: only proven os/asyncio shell APIs are risky (synthetic code)."""
from __future__ import annotations

import unittest

from offline_core import scan_text
from offline_report import build_report


def shell_lines(code: str) -> list[int]:
    report = build_report(scan_text(code, filename="synthetic.py"))
    return [row.finding.start_line for row in report.findings if row.rule_id == "PY-SHELL"]


class ShellApiProvenanceTests(unittest.TestCase):
    def test_direct_shell_apis_are_flagged_without_shell_keyword(self) -> None:
        cases = (
            ("import os\nos.system(command)\n", [2]),
            ("import os as shell\nshell.popen(command)\n", [2]),
            ("from os import system as execute\nexecute(command)\n", [2]),
            ("from os import popen\npopen(command)\n", [2]),
            ("import asyncio\nasync def work():\n    await asyncio.create_subprocess_shell(command)\n", [3]),
            ("from asyncio import create_subprocess_shell as launch\nlaunch(command)\n", [2]),
            ("__import__('os').system(command)\n", [1]),
            ("getattr(__import__('asyncio'), 'create_subprocess_shell')(command)\n", [1]),
        )
        for code, expected in cases:
            with self.subTest(code=code):
                self.assertEqual(shell_lines(code), expected)

    def test_unproven_calls_and_shadowed_imports_are_not_claimed(self) -> None:
        cases = (
            "service.system(command)\n",
            "from unrelated import system as execute\nexecute(command)\n",
            "import os as shell\nshell = other\nshell.system(command)\n",
            "import asyncio as a\ndef check(a):\n    a.create_subprocess_shell(command)\n",
            "if enabled:\n    import os as shell\nshell.system(command)\n",
            "if enabled:\n    import os as shell\nelse:\n    shell.system(command)\n",
            "getattr = other\ngetattr(__import__('os'), 'system')(command)\n",
            "__import__(module).system(command)\n",
            "import os\nos.getenv('NAME')\n",
            "import asyncio\nasyncio.create_subprocess_exec('echo', 'hi')\n",
        )
        for code in cases:
            with self.subTest(code=code):
                self.assertEqual(shell_lines(code), [])

    def test_nested_guard_preserves_real_call(self) -> None:
        code = "if enabled:\n    import os as shell\n    shell.system(command)\n"
        self.assertEqual(shell_lines(code), [3])


if __name__ == "__main__":
    unittest.main()
