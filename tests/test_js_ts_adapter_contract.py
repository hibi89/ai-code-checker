"""Default CI regression tests without optional native parser dependency."""
from __future__ import annotations
import unittest
from unittest.mock import patch
from scripts import prototype_js_ts_adapter as adapter


class SyntaxAdapterContractTests(unittest.TestCase):
    def test_unsupported_language_no_native_call(self):
        with patch.object(adapter, "_parser") as parse:
            with self.assertRaises(ValueError):
                adapter.inspect("eval(x)", "python")
            parse.assert_not_called()

    def test_large_source_blocks_before_import(self):
        with patch.object(adapter, "_parser") as parse:
            result = adapter.inspect("x" * (adapter.MAX_BYTES + 1), "js")
            self.assertEqual(result.status, "blocked")
            self.assertEqual(result.candidates, ())
            self.assertFalse(result.approved_for_sale)
            parse.assert_not_called()

    def test_unavailable_grammar_explicit(self):
        with patch.object(adapter, "_parser", side_effect=adapter.UnsupportedParser("missing")):
            with self.assertRaises(adapter.UnsupportedParser):
                adapter.inspect("eval(x)", "ts")

    def test_type_and_status_contract(self):
        with self.assertRaises(TypeError):
            adapter.inspect(b"code", "js")
        status = adapter.Analysis("syntax_checked", "js", (), 1)
        self.assertTrue(status.syntax_only)
        self.assertFalse(status.shipped)
        self.assertFalse(status.approved_for_sale)


if __name__ == "__main__":
    unittest.main()
