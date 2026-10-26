from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from main import DEFAULT_MODEL, load_settings


class SettingsTests(unittest.TestCase):
    def test_default_model_uses_documented_default_prices(self) -> None:
        with patch("main.load_dotenv"), patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "test-key", "GEMINI_MODEL": DEFAULT_MODEL},
            clear=True,
        ):
            settings = load_settings()

        self.assertEqual(settings.model, DEFAULT_MODEL)
        self.assertEqual(settings.input_price, 0.25)
        self.assertEqual(settings.output_price, 1.50)
        self.assertEqual(settings.max_output_tokens, 4096)

    def test_custom_model_requires_both_explicit_price_rates(self) -> None:
        with patch("main.load_dotenv"), patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "test-key", "GEMINI_MODEL": "gemini-3.6-flash"},
            clear=True,
        ):
            with self.assertRaisesRegex(ValueError, "비용 과소 추정"):
                load_settings()

    def test_custom_model_uses_explicit_price_rates(self) -> None:
        with patch("main.load_dotenv"), patch.dict(
            os.environ,
            {
                "GEMINI_API_KEY": "test-key",
                "GEMINI_MODEL": "gemini-3.6-flash",
                "GEMINI_INPUT_USD_PER_MILLION": "0.75",
                "GEMINI_OUTPUT_USD_PER_MILLION": "3.75",
            },
            clear=True,
        ):
            settings = load_settings()

        self.assertEqual(settings.model, "gemini-3.6-flash")
        self.assertEqual(settings.input_price, 0.75)
        self.assertEqual(settings.output_price, 3.75)


if __name__ == "__main__":
    unittest.main()
