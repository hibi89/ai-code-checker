"""No third-party syntax package is needed for default project tests."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts import probe_js_ts_parser as target


class JSParserFeasibilityTests(unittest.TestCase):
    def test_hand_authored_language_and_expected_outcome_coverage(self):
        self.assertEqual(len(target.SAMPLES), 12)
        self.assertEqual({x.language for x in target.SAMPLES}, {"js", "ts", "tsx"})
        self.assertEqual(sum(x.valid for x in target.SAMPLES), 9)
        self.assertEqual(sum(not x.valid for x in target.SAMPLES), 3)

    def test_results_are_not_customer_product_or_security_certification(self):
        mocked = {
            name: {
                "version": version,
                "declared_license": "MIT",
                "installed_license_named_paths": 0,
                "notice_approval": False,
                "customer_exe_included": False,
            }
            for name, version in target.PINNED.items()
        }

        class DummyRoot:
            def __init__(self, content: bytes, valid: bool):
                self.has_error = not valid
                self.is_missing = False
                self.end_byte = len(content)

        class FakeParser:
            def __init__(self, lang: str):
                self.lang = lang

            def parse(self, source: bytes):
                case = next(
                    s for s in target.SAMPLES
                    if s.language == self.lang and s.text.encode("utf-8") == source
                )
                return type("Tree", (), {"root_node": DummyRoot(source, case.valid)})()

        with patch.object(target, "_assert_metadata", return_value=mocked), patch.object(
            target, "_parsers", return_value={
                k: FakeParser(k) for k in ("js", "ts", "tsx")
            }
        ):
            result = target.probe()

        self.assertFalse(result["shipped_exe_modified"])
        self.assertFalse(result["commercial_release_ready"])
        self.assertFalse(result["legal_notice_approved"])
        self.assertFalse(result["runs_scanned_program"])
        self.assertEqual(result["real_world_security_accuracy"], "UNVERIFIED")
        self.assertEqual(result["test_fixtures"], 12)

    def test_parser_rejects_falsely_marked_syntax_without_code_execution(self):
        class BadRoot:
            has_error = True
            is_missing = False
            end_byte = 0

        class BadParser:
            def parse(self, data):
                return type("T", (), {"root_node": BadRoot()})()

        with patch.object(target, "_assert_metadata", return_value={}), patch.object(
            target, "_parsers", return_value={
                "js": BadParser(), "ts": BadParser(), "tsx": BadParser()
            }
        ):
            with self.assertRaisesRegex(AssertionError, "Unexpected grammar parse"):
                target.probe()


if __name__ == "__main__":
    unittest.main()
