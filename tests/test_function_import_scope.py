"""P2-9 synthetic regressions for lexical function-local import provenance."""
from __future__ import annotations

import unittest

from offline_core import scan_text
from offline_report import build_report


def flagged(source: str) -> list[tuple[str, int]]:
    report = build_report(scan_text(source, filename="fixture.py"))
    if report.validation_issues:
        raise AssertionError("source evidence was not verified")
    return [(finding.rule_id, finding.finding.start_line) for finding in report.findings]


class FunctionScopedImportTests(unittest.TestCase):
    def test_function_scoped_sensitive_imports(self) -> None:
        samples = (
            ("def f():\n    import subprocess as p\n    p.run(cmd, shell=True)\n", [("PY-SHELL", 3)]),
            ("def f():\n    from os import system as cmd\n    cmd(value)\n", [("PY-SHELL", 3)]),
            ("async def f():\n    import asyncio as a\n    await a.create_subprocess_shell(cmd)\n", [("PY-SHELL", 3)]),
            ("def f():\n    import pickle as p\n    p.loads(data)\n", [("PY-PICKLE", 3)]),
            ("def f():\n    from requests import get as g\n    g(url, verify=False)\n", [("GEN-TLS-VERIFY", 3)]),
            ("def f():\n    from builtins import eval as e\n    e(data)\n", [("PY-DYNAMIC-EXEC", 3)]),
        )
        for source, expected in samples:
            with self.subTest(source=source):
                self.assertEqual(flagged(source), expected)

    def test_function_bindings_do_not_leak_across_scope_or_guards(self) -> None:
        sources = (
            "def one():\n    import subprocess as s\ndef two():\n    s.run(cmd, shell=True)\n",
            "def f():\n    import subprocess as s\ns.run(cmd, shell=True)\n",
            "def f():\n    s.run(cmd, shell=True)\n    import subprocess as s\n",
            "def f(s):\n    s.run(cmd, shell=True)\n",
            "def f():\n    import subprocess as s\n    s = other\n    s.run(cmd, shell=True)\n",
            "def f(enabled):\n    if enabled:\n        import subprocess as s\n    s.run(cmd, shell=True)\n",
            "def f(enabled):\n    if enabled:\n        import subprocess as s\n    else:\n        s.run(cmd, shell=True)\n",
            "def outer():\n    import subprocess as s\n    def inner():\n        s.run(cmd, shell=True)\n",
        )
        for source in sources:
            with self.subTest(source=source):
                self.assertEqual(flagged(source), [])

    def test_same_function_guard_and_pre_rebind(self) -> None:
        source = (
            "def f(cond):\n"
            "    import os as shell\n"
            "    shell.system(command)\n"
            "    shell = other\n"
            "    shell.system(command)\n"
            "    if cond:\n"
            "        import subprocess as s\n"
            "        s.run(command, shell=True)\n"
        )
        self.assertEqual(flagged(source), [("PY-SHELL", 3), ("PY-SHELL", 8)])

    def test_module_import_still_available_to_function(self) -> None:
        source = "import subprocess as sp\ndef f():\n    sp.run(cmd, shell=True)\n"
        self.assertEqual(flagged(source), [("PY-SHELL", 3)])


if __name__ == "__main__":
    unittest.main()
