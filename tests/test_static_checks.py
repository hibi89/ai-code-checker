from __future__ import annotations

import unittest

from code_input import bundle_from_text
from static_checks import run_static_checks


class StaticCheckTests(unittest.TestCase):
    def test_python_syntax_error_is_reported_with_exact_location(self) -> None:
        bundle = bundle_from_text("def broken(:\n    pass\n")
        findings = run_static_checks(bundle)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].title, "Python 구문 오류")
        self.assertEqual(findings[0].start_line, 1)
        self.assertTrue(findings[0].citation_verified)

    def test_risky_python_patterns_are_found_without_execution(self) -> None:
        code = (
            "import subprocess\n"
            "subprocess.run(command, shell=True)\n"
            "conn.execute(f\"SELECT * FROM users WHERE id={user_id}\")\n"
            "eval(user_input)\n"
        )
        bundle = bundle_from_text(code)
        findings = run_static_checks(bundle)
        titles = {finding.title for finding in findings}

        self.assertIn("셸 명령을 문자열로 실행함", titles)
        self.assertIn("SQL 질의 문자열을 동적으로 조합함", titles)
        self.assertIn("동적 코드 실행 호출: eval", titles)
        self.assertTrue(all(finding.citation_verified for finding in findings))

    def test_secret_warning_never_contains_original_value(self) -> None:
        secret = "ghp_" + "123456789012345678901234567890"
        bundle = bundle_from_text(f'TOKEN = "{secret}"')
        findings = run_static_checks(bundle)

        self.assertTrue(findings)
        self.assertNotIn(secret, bundle.render())
        self.assertIn("전송 전에 마스킹됨", findings[0].title)


if __name__ == "__main__":
    unittest.main()
