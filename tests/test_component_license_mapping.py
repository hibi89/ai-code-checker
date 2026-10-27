"""Synthetic P0-E ownership and installed-license-text evidence tests.

Never load or execute customer binaries; mapping uses untrusted filenames only.
"""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.map_frozen_licenses import make_mapping, gather_original_license_texts


def sample_audit():
    return {
        "license_compliance_certified": False,
        "third_party_notice_ready_to_distribute": False,
        "customer_release_ready": False,
        "exe_sha256": "f" * 64,
        "archive": {
            "top_level": [
                {"name": "python313.dll", "typecode": "b"},
                {"name": "tcl86t.dll", "typecode": "b"},
                {"name": "pydantic_core/example.pyd", "typecode": "b"},
                {"name": "mystery.dll", "typecode": "b"},
            ],
            "pyz_modules": [
                {"module": "os"}, {"module": "pydantic.main"},
                {"module": "offline_core"}, {"module": "unknown.vendor"},
            ],
        },
        "python_build_distributions": [
            {"name": "pydantic", "version": "2.12.5", "license_metadata": "MIT",
             "license_files_in_installed_distribution": []},
            {"name": "pyinstaller", "version": "6.22.3", "license_metadata": "GPL-2.0-or-later",
             "license_files_in_installed_distribution": []},
        ],
    }


class ComponentOwnershipTests(unittest.TestCase):
    def test_all_embedded_names_are_accounted_for_without_claiming_certification(self):
        info = make_mapping(
            sample_audit(),
            package_claims={"pydantic": ["pydantic"]},
            installed_files={"pydantic": {"pydantic_core/example.pyd"}},
        )
        self.assertEqual(info["total_rows"], 8)
        self.assertTrue(info["all_items_accounted_for_in_metadata"])
        self.assertEqual(info["candidate_dist_count"], 1)
        self.assertIn("pydantic", info["installed_dist_candidates"])
        self.assertFalse(info["license_compliance_certified"])
        self.assertFalse(info["customer_release_ready"])
        self.assertFalse(info["embedded_binary_hash_matches_checked"])
        kinds = {x["name"]: x["mapping"] for x in info["entries"]}
        self.assertEqual(kinds["os"], "cpython_stdlib_name_candidate")
        self.assertEqual(kinds["pydantic.main"], "installed_dist_unique_name_claim")
        self.assertEqual(kinds["offline_core"], "first_party_candidate")
        self.assertEqual(kinds["unknown.vendor"], "unresolved")
        self.assertEqual(kinds["python313.dll"], "cpython_runtime_filename_candidate")
        self.assertEqual(kinds["tcl86t.dll"], "tcl_tk_filename_candidate")
        self.assertEqual(kinds["pydantic_core/example.pyd"],
                         "installed_native_exact_relative_filename_candidate")
        self.assertEqual(kinds["mystery.dll"], "unresolved_native_or_system_binary")

    def test_new_bundled_cleanup_module_is_recognized_as_first_party(self):
        audit = sample_audit()
        audit["archive"]["pyz_modules"].append({"module": "report_cleanup"})
        info = make_mapping(audit, package_claims={}, installed_files={})
        category = {row["name"]: row["mapping"] for row in info["entries"]}
        self.assertEqual(category["report_cleanup"], "first_party_candidate")
        baseline = make_mapping(sample_audit(), package_claims={}, installed_files={})
        self.assertEqual(info["unresolved_count"], baseline["unresolved_count"])
        self.assertFalse(info["license_compliance_certified"])
        self.assertFalse(info["customer_release_ready"])

    def test_ambiguous_package_cannot_be_assigned_a_single_owner(self):
        audit = sample_audit()
        audit["python_build_distributions"].append({
            "name": "pydantic-extra", "version": "1",
            "license_metadata": "UNKNOWN", "license_files_in_installed_distribution": [],
        })
        result = make_mapping(
            audit,
            package_claims={"pydantic": ["pydantic", "pydantic-extra"]},
            installed_files={},
        )
        row = next(x for x in result["entries"] if x["name"] == "pydantic.main")
        self.assertEqual(row["mapping"], "ambiguous_dist_name_claim")
        self.assertEqual(len(row["owner_candidates"]), 2)

    def test_preapproved_input_must_be_rejected(self):
        audit = sample_audit()
        audit["third_party_notice_ready_to_distribute"] = True
        with self.assertRaises(ValueError):
            make_mapping(audit, package_claims={}, installed_files={})

    def test_duplicate_archive_name_is_rejected(self):
        audit = sample_audit()
        audit["archive"]["top_level"].append(audit["archive"]["top_level"][0].copy())
        with self.assertRaises(ValueError):
            make_mapping(audit, package_claims={}, installed_files={})

    def test_original_installed_license_hash_and_text_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = Path("pyinstaller-6.22.3.dist-info/licenses/COPYING.txt")
            license_file = root / rel
            license_file.parent.mkdir(parents=True)
            original = b"Sample LICENSE text preserving exact\n  original indentation.\n"
            license_file.write_bytes(original)

            class Dist:
                files = [rel]
                def locate_file(self, name):
                    return root / str(name)

            audit = sample_audit()
            audit["python_build_distributions"][1]["license_files_in_installed_distribution"] = [{
                "installed_relative_path": rel.as_posix(),
                "bytes": len(original),
                "sha256": hashlib.sha256(original).hexdigest(),
            }]
            with patch("scripts.map_frozen_licenses.metadata.distribution", return_value=Dist()):
                notice, status = gather_original_license_texts(audit, {"installed_dist_candidates": []})
            self.assertIn(original.decode(), notice)
            self.assertEqual(status["staged_original_license_files"], 1)
            self.assertFalse(status["draft_for_distribution"])
            self.assertTrue(status["human_legal_review_pending"])

    def test_changed_license_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = Path("pyinstaller-6.22.3.dist-info/LICENSE")
            path = root / rel
            path.parent.mkdir(parents=True)
            path.write_text("modified after scan", encoding="utf-8")

            class Dist:
                files = [rel]
                def locate_file(self, name):
                    return root / str(name)

            audit = sample_audit()
            audit["python_build_distributions"][1]["license_files_in_installed_distribution"] = [{
                "installed_relative_path": rel.as_posix(),
                "bytes": 6, "sha256": "0" * 64,
            }]
            with patch("scripts.map_frozen_licenses.metadata.distribution", return_value=Dist()):
                with self.assertRaises(ValueError):
                    gather_original_license_texts(audit, {"installed_dist_candidates": []})


if __name__ == "__main__":
    unittest.main()
