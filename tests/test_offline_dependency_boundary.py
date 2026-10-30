"""Offline v2 dependency isolation and legacy Gemini compatibility regressions."""
from __future__ import annotations

import copy
import subprocess
import sys
import unittest
from pathlib import Path

from offline_models import CodeFinding as OfflineCodeFinding
from review_models import AIReview, CodeFinding as LegacyCodeFinding
from scripts.check_offline_frozen_deps import check_boundary
from scripts.offline_dependency_inventory import DEFAULT_ROOTS

ROOT = Path(__file__).resolve().parents[1]


class OfflineDependencyBoundaryTests(unittest.TestCase):
    def test_offline_gui_imports_without_third_party_site_packages(self) -> None:
        source = (
            "import sys, desktop_core, desktop_ui, offline_report, offline_core, offline_models;"
            "assert 'pydantic' not in sys.modules;"
            "assert 'review_models' not in sys.modules;"
            "print('OFFLINE_STDLIB_IMPORT_PASS')"
        )
        proc = subprocess.run(
            [sys.executable, "-S", "-c", source],
            cwd=ROOT, capture_output=True, text=True, timeout=30, check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr[-1200:])
        self.assertIn("OFFLINE_STDLIB_IMPORT_PASS", proc.stdout)

    def test_legacy_gemini_schema_and_codefinding_remain_identical(self) -> None:
        self.assertIs(OfflineCodeFinding, LegacyCodeFinding)
        self.assertTrue(hasattr(AIReview, "model_validate"))
        self.assertEqual(DEFAULT_ROOTS, {"pyinstaller": "6.22.3"})

    def test_bundled_archive_metadata_fails_closed_on_gemini_imports(self) -> None:
        audit = {
            "format": "code_checker_p0d_frozen_archive_audit_v1",
            "license_compliance_certified": False,
            "third_party_notice_ready_to_distribute": False,
            "customer_release_ready": False,
            "archive": {
                "metadata_only": True,
                "no_bundle_entry_extracted_or_executed": True,
                "archive_read_errors": [],
                "top_level": [{"name": "python313.dll"}, {"name": "PYZ.pyz"}],
                "pyz_modules": [{"module": "os"}, {"module": "offline_models"}],
                "top_level_count": 2,
                "pyz_module_count": 2,
            },
        }
        self.assertFalse(check_boundary(audit)["gemini_pydantic_bundled"])
        for kind, name in [
            ("top", "pydantic_core/_pydantic_core.cp313-win_amd64.pyd"),
            ("top", "pydantic/version.json"),
            ("pyz", "pydantic.main"),
            ("pyz", "review_models"),
        ]:
            with self.subTest(name=name):
                modified = copy.deepcopy(audit)
                key = "top_level" if kind == "top" else "pyz_modules"
                modified["archive"][key].append(
                    {"name": name} if kind == "top" else {"module": name}
                )
                count_key = "top_level_count" if kind == "top" else "pyz_module_count"
                modified["archive"][count_key] += 1
                with self.assertRaises(ValueError):
                    check_boundary(modified)
        audit["customer_release_ready"] = True
        with self.assertRaises(ValueError):
            check_boundary(audit)


if __name__ == "__main__":
    unittest.main()
