"""Exact frozen EXE multi-receipt consolidation, synthetic offline tests."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.consolidate_windows_retail_evidence import GATES, consolidate, main
from scripts.runtime_version_receipt import FORMAT as RUNTIME_FORMAT, FLAGS
from scripts.windows_defender_scan_contract import FORMAT as DEFENDER_FORMAT
from test_windows_acceptance_contract import example as readonly_fixture
from test_windows_local_exe_smoke_contract import fixture as smoke_fixture


class CombinedRetailEvidenceTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.exe = self.root / "synthetic.exe"
        self.exe.write_bytes(b"MZ inert metadata fixture, never launched")
        self.readonly = readonly_fixture(self.exe)
        self.smoke = smoke_fixture(self.exe)
        self.sha = hashlib.sha256(self.exe.read_bytes()).hexdigest()
        self.runtime = {
            "format": RUNTIME_FORMAT,
            "exe_sha256": self.sha,
            "exe_bytes": self.exe.stat().st_size,
            "frozen_process_runtime_observed": True,
            "python_runtime_version": "3.13.16",
            "tcl_runtime_patchlevel": "8.6.15",
            "tk_runtime_patchlevel": "8.6.15",
            **{flag: False for flag in FLAGS},
        }
        self.defender = {
            "format": DEFENDER_FORMAT,
            "collection_method": "local_mpcmdrun_custom_file_scan_no_remediation",
            "scope": "local_developer_or_hosted_windows_binary_only",
            "exe_sha256": self.sha,
            "exe_bytes": self.exe.stat().st_size,
            "defender_availability": "UNVERIFIED",
            "scanner_available": False,
            "scan_attempted": False,
            "scan_command_status": "UNVERIFIED",
            "command_exit_code": None,
            "exe_unchanged": True,
            "malware_free_certified": False,
            "retail_defender_acceptance": "UNVERIFIED",
            "customer_release_ready": False,
        }

    def test_all_four_consistent_receipts_never_enable_customer_release(self):
        result = consolidate(self.exe, self.readonly, self.smoke,
                             runtime=self.runtime, defender=self.defender)
        self.assertEqual(result["exe_sha256"], self.sha)
        self.assertEqual(result["status"], "EXACT_BINARY_RECEIPTS_VALID_RELEASE_BLOCKED")
        self.assertEqual(result["observations_not_acceptance"]["frozen_tcl_patchlevel"], "8.6.15")
        self.assertEqual(result["receipt_evidence"]["defender_custom_scan_command"],
                         "RECEIPT_INTEGRITY_VERIFIED")
        self.assertEqual(set(result["human_release_gates"]), set(GATES))
        self.assertTrue(all(v == "UNVERIFIED" for v in result["human_release_gates"].values()))
        for key in ("customer_release_ready", "malware_free_certified",
                    "legal_notice_approved", "real_buyer_pc_test_certified"):
            self.assertIs(result[key], False)
        output = json.dumps(result)
        self.assertNotIn(str(self.root), output)
        self.assertNotIn("inert metadata fixture", output)

    def test_optional_receipts_missing_are_explicitly_not_provided(self):
        result = consolidate(self.exe, self.readonly, self.smoke)
        self.assertEqual(result["receipt_evidence"]["frozen_tcl_tk_patchlevels"], "NOT_PROVIDED")
        self.assertEqual(result["receipt_evidence"]["defender_custom_scan_command"], "NOT_PROVIDED")
        self.assertIsNone(result["observations_not_acceptance"]["defender_custom_scan_command_status"])
        self.assertFalse(result["customer_release_ready"])

    def test_defender_zero_exit_is_never_malware_free(self):
        self.defender.update(defender_availability="ENABLED", scanner_available=True,
                             scan_attempted=True, scan_command_status="ZERO_EXIT",
                             command_exit_code=0)
        result = consolidate(self.exe, self.readonly, self.smoke, defender=self.defender)
        self.assertEqual(result["observations_not_acceptance"]["defender_custom_scan_command_status"],
                         "ZERO_EXIT")
        self.assertFalse(result["malware_free_certified"])
        self.assertEqual(result["human_release_gates"]["defender_on_buyer_pc"], "UNVERIFIED")

    def test_same_length_exe_mutation_rejected_for_every_receipt(self):
        original = self.exe.read_bytes()
        self.exe.write_bytes(original.replace(b"metadata", b"meTadata"))
        self.assertEqual(self.exe.stat().st_size, len(original))
        with self.assertRaises(ValueError):
            consolidate(self.exe, self.readonly, self.smoke,
                        runtime=self.runtime, defender=self.defender)

    def test_mismatched_receipts_are_not_combined(self):
        for component in ("readonly", "smoke", "runtime", "defender"):
            with self.subTest(component=component):
                current = copy.deepcopy(getattr(self, component))
                current["exe_sha256"] = "0" * 64
                kwargs = {"runtime": self.runtime, "defender": self.defender}
                readonly, smoke = self.readonly, self.smoke
                if component == "runtime":
                    kwargs["runtime"] = current
                elif component == "defender":
                    kwargs["defender"] = current
                elif component == "readonly":
                    readonly = current
                else:
                    smoke = current
                with self.assertRaises(ValueError):
                    consolidate(self.exe, readonly, smoke, **kwargs)

    def test_forged_human_acceptance_or_license_is_rejected(self):
        for component, field in (
            ("readonly", "customer_release_ready"),
            ("smoke", "actual_customer_release_ready"),
            ("runtime", "customer_notice_ready"),
            ("defender", "malware_free_certified"),
        ):
            with self.subTest(component=component):
                record = copy.deepcopy(getattr(self, component))
                record[field] = True
                data = {"readonly": self.readonly, "smoke": self.smoke,
                        "runtime": self.runtime, "defender": self.defender}
                data[component] = record
                with self.assertRaises(ValueError):
                    consolidate(self.exe, data["readonly"], data["smoke"],
                                runtime=data["runtime"], defender=data["defender"])

    def test_no_trusted_os_version_inference_from_hosted_ci(self):
        result = consolidate(self.exe, self.readonly, self.smoke, runtime=self.runtime)
        self.assertEqual(result["human_release_gates"]["clean_consumer_windows_10_11"],
                         "UNVERIFIED")
        self.assertEqual(result["human_release_gates"]["korean_pdf_visual_inspection"],
                         "UNVERIFIED")
        self.assertEqual(result["human_release_gates"]["os_level_network_capture"],
                         "UNVERIFIED")

    def test_cli_output_created_only_once_and_is_local_metadata(self):
        files = []
        for name, value in (("readonly", self.readonly), ("smoke", self.smoke),
                            ("runtime", self.runtime), ("defender", self.defender)):
            path = self.root / (name + ".json")
            path.write_text(json.dumps(value), encoding="utf-8")
            files.append(path)
        output = self.root / "summary.json"
        argv = ["--exe", str(self.exe), "--readonly", str(files[0]),
                "--smoke", str(files[1]), "--runtime", str(files[2]),
                "--defender", str(files[3]), "--out", str(output)]
        self.assertEqual(main(argv), 0)
        result = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(result["exe_sha256"], self.sha)
        self.assertNotIn(str(self.root), output.read_text(encoding="utf-8"))
        self.assertFalse(result["customer_release_ready"])
        self.assertEqual(main(argv), 1)
        self.assertEqual(json.loads(output.read_text(encoding="utf-8")), result)

    def test_invalid_optional_receipt_rejects_no_output(self):
        a, b, c = (self.root / n for n in ("readonly.json", "smoke.json", "runtime.json"))
        for path, receipt in ((a, self.readonly), (b, self.smoke), (c, self.runtime)):
            path.write_text(json.dumps(receipt), encoding="utf-8")
        c.write_text('{"customer_release_ready":true}', encoding="utf-8")
        output = self.root / "no-output.json"
        self.assertEqual(main(["--exe", str(self.exe), "--readonly", str(a),
                               "--smoke", str(b), "--runtime", str(c),
                               "--out", str(output)]), 1)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
