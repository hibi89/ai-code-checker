"""Minimum operational Code Checker regression tests, no actual customer inputs."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts.mvp_acceptance import run_mvp_acceptance, main


class MVPContractTests(unittest.TestCase):
    def test_complete_local_user_journey(self):
        checks = run_mvp_acceptance()
        self.assertEqual(len(checks), 7)
        self.assertTrue(all(checks.values()))

    def test_cli_is_nonzero_if_any_step_fails(self):
        with patch("scripts.mvp_acceptance.run_mvp_acceptance",
                   side_effect=AssertionError("synthetic failure")):
            self.assertEqual(main(), 1)

    def test_cli_is_zero_if_full_acceptance_passes(self):
        with patch("scripts.mvp_acceptance.run_mvp_acceptance", return_value={
                "preview": True}):
            self.assertEqual(main(), 0)


if __name__ == "__main__":
    unittest.main()
