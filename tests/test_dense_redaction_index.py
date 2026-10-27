"""P2-10: dense local redaction retains exact original source citations."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from code_input import InputLimits, bundle_from_text


class DenseRedactionLineIndexTests(unittest.TestCase):
    def test_6000_synthetic_email_matches_preserve_every_original_line(self) -> None:
        count = 6000
        text = "".join(
            f"person_{i:05d} = 'user{i:05d}@synthetic.invalid'\n"
            for i in range(count)
        )
        limits = InputLimits(max_file_bytes=1024 * 1024, max_total_bytes=1024 * 1024)
        bundle = bundle_from_text(text, filename="synthetic.py", limits=limits)
        source = bundle.files[0]
        self.assertEqual(len(source.redactions), count)
        self.assertEqual(source.line_count, count)
        self.assertEqual(
            [item.line_number for item in source.redactions],
            list(range(1, count + 1)),
        )
        self.assertEqual({item.kind for item in source.redactions}, {"email address"})
        self.assertNotIn("synthetic.invalid", source.text)
        self.assertEqual(source.text.count("<REDACTED>"), count)

    def test_newline_positions_reset_between_mutating_redaction_phases(self) -> None:
        source = (
            'pem = """\n'
            '-----BEGIN PRIVATE KEY-----\n'
            'FAKE_PRIVATE_KEY_MATERIAL\n'
            '-----END PRIVATE KEY-----\n'
            '"""\n'
            'API_KEY = "synthetic_credential_value_123456789"\n'
            'token = "ghp_' + 'A' * 24 + '"\n'
            'contact = "owner@synthetic.invalid"\n'
            'phone = "010-1234-5678"\n'
            'rrn = "900101-1234567"\n'
            'example = "user@example.com"\n'
        )
        bundle = bundle_from_text(source, filename="synthetic.py")
        file = bundle.files[0]
        self.assertEqual(file.line_count, 11)
        citations = {(item.kind, item.line_number) for item in file.redactions}
        self.assertIn(("private key", 2), citations)
        self.assertIn(("credential assignment", 6), citations)
        self.assertIn(("GitHub token", 7), citations)
        self.assertIn(("email address", 8), citations)
        self.assertIn(("Korean phone number", 9), citations)
        self.assertIn(("Korean resident number", 10), citations)
        self.assertIn("user@example.com", file.text)
        for literal in ("synthetic_credential_value_123456789", "owner@synthetic.invalid", "010-1234-5678"):
            self.assertNotIn(literal, file.text)

    def test_no_sensitive_matches_do_not_build_a_line_index(self) -> None:
        safe = "print('synthetic')\n" * 7000
        limits = InputLimits(max_file_bytes=1024 * 1024, max_total_bytes=1024 * 1024)
        with patch("code_input.re.finditer", side_effect=AssertionError("unexpected line indexing")):
            bundle = bundle_from_text(safe, filename="synthetic.py", limits=limits)
        self.assertEqual(bundle.redaction_count, 0)
        self.assertEqual(bundle.files[0].line_count, 7000)


if __name__ == "__main__":
    unittest.main()
