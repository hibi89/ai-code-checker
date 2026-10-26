"""Synthetic acceptance for benchmark definitions and inventory output."""
from __future__ import annotations

import tempfile
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch

from scripts.benchmark_offline import boundary_cases, fixtures, one_case
from scripts.offline_dependency_inventory import _license_field, inventory


class BenchmarkTests(unittest.TestCase):
    def test_three_quick_synthetic_cases_with_local_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = fixtures(root, full=False)
            self.assertEqual(len(cases), 3)
            reports = root / "reports"
            for name, values in cases.items():
                result = one_case(name, *values, reports)
                self.assertEqual(result["status"], "complete")
                self.assertGreater(result["elapsed_seconds"], 0)
                self.assertGreater(result["tracemalloc_peak_mib"], 0)
                self.assertFalse(result["rss_measured"])
                self.assertTrue(result["report_html_bytes"] > 100)

    def test_fixture_bytes_are_platform_independent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = fixtures(root, full=False)
            txt = cases["txt_1200"][0].read_bytes()
            folder = cases["folder_200_12k"][0]
            self.assertEqual(len(txt), 12002)
            self.assertNotIn(b"\r\n", txt)
            self.assertEqual((folder / "module_000.py").read_bytes(), b"number = 1\n" * 60)

    def test_201_file_limit_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = boundary_cases(Path(tmp))
        self.assertEqual(result["result"], "blocked")

    def test_license_metadata_is_not_mistaken_for_license_audit(self):
        msg = Message()
        msg["Name"] = "pydantic"
        msg["License-Expression"] = "MIT"
        class DummyDist:
            version = "2.12.5"
            requires = []
            metadata = msg
        # Runtime inventory is only invoked on build workers which install packaging.
        # Test against a fake non-None parser to avoid adding packaging to
        # the original Gemini CLI's runtime dependency closure.
        with patch("scripts.offline_dependency_inventory.Requirement", lambda x: None), patch(
            "scripts.offline_dependency_inventory.metadata.distribution", return_value=DummyDist()
        ):
            report = inventory({"pydantic": "2.12.5"})
        self.assertEqual(report["status"], "INVENTORY_ONLY_REVIEW_REQUIRED")
        self.assertEqual(report["components_count"], 1)
        self.assertTrue(report["needs_full_bundled_binary_manifest"])
        self.assertFalse(report["includes_python_stdlib_tcl_tk"])
        self.assertEqual(report["unresolved"], [])

    def test_unknown_license_is_never_assumed_permissive(self):
        msg = Message()
        msg["Name"] = "example"
        class MissingLicense:
            metadata = msg
        label, origin = _license_field(MissingLicense())
        self.assertEqual(label, "UNKNOWN")
        self.assertEqual(origin, "Metadata-Missing")


if __name__ == "__main__":
    unittest.main()
