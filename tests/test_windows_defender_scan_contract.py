"""Synthetic-only P1-U Defender receipt schema and integrity regression tests."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.windows_defender_scan_contract import FORMAT, validate_scan_receipt


class DefenderScanEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.exe = Path(self.temp.name) / "CodeCheckerOffline.exe"
        self.exe.write_bytes(b"MZ\x00synthetic inert candidate not executed")
        self.proof = {
            "format": FORMAT,
            "collection_method": "local_mpcmdrun_custom_file_scan_no_remediation",
            "scope": "local_developer_or_hosted_windows_binary_only",
            "exe_sha256": hashlib.sha256(self.exe.read_bytes()).hexdigest(),
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

    def observed(self):
        self.proof.update(
            defender_availability="ENABLED", scanner_available=True,
            scan_attempted=True, scan_command_status="ZERO_EXIT",
            command_exit_code=0,
        )

    def test_unavailable_defender_cannot_claim_success(self):
        result = validate_scan_receipt(self.proof, self.exe)
        self.assertFalse(result["command_zero_exit_observed"])
        self.assertFalse(result["malware_free_certified"])

    def test_command_zero_exit_is_observation_not_security_certification(self):
        self.observed()
        result = validate_scan_receipt(self.proof, self.exe)
        self.assertTrue(result["command_zero_exit_observed"])
        self.assertFalse(result["customer_release_ready"])
        self.assertEqual(result["retail_defender_acceptance"], "UNVERIFIED")

    def test_nonzero_exit_is_retained_without_security_approval(self):
        self.observed()
        self.proof.update(scan_command_status="NONZERO_EXIT", command_exit_code=2)
        result = validate_scan_receipt(self.proof, self.exe)
        self.assertFalse(result["command_zero_exit_observed"])

    def test_timeout_never_invents_an_exit_code(self):
        self.observed()
        self.proof.update(scan_command_status="TIMEOUT", command_exit_code=None)
        self.assertTrue(validate_scan_receipt(self.proof, self.exe)["scan_attempted"])
        self.proof["command_exit_code"] = 0
        with self.assertRaises(ValueError):
            validate_scan_receipt(self.proof, self.exe)

    def test_incoherent_process_claims_rejected(self):
        for change in (
            {"scan_attempted": True},
            {"scan_command_status": "ZERO_EXIT"},
            {"scan_command_status": "NONZERO_EXIT", "command_exit_code": 2},
            {"scan_command_status": "TIMEOUT", "command_exit_code": 0},
            {"command_exit_code": True},
            {"scanner_available": "yes"},
        ):
            with self.subTest(change=change):
                copy = json.loads(json.dumps(self.proof))
                copy.update(change)
                with self.assertRaises(ValueError):
                    validate_scan_receipt(copy, self.exe)

    def test_forged_release_clearance_refused(self):
        for key, value in (
            ("malware_free_certified", True),
            ("customer_release_ready", True),
            ("retail_defender_acceptance", "PASS"),
            ("exe_unchanged", False),
            ("scan_command_status", "EXE_CHANGED"),
        ):
            with self.subTest(key=key):
                copy = json.loads(json.dumps(self.proof))
                copy[key] = value
                with self.assertRaises(ValueError):
                    validate_scan_receipt(copy, self.exe)

    def test_file_change_and_extra_metadata_refused(self):
        extra = json.loads(json.dumps(self.proof))
        extra["user_path"] = "C:\\private\\source"
        with self.assertRaises(ValueError):
            validate_scan_receipt(extra, self.exe)
        self.exe.write_bytes(self.exe.read_bytes().replace(b"synthetic", b"synThetic"))
        with self.assertRaises(ValueError):
            validate_scan_receipt(self.proof, self.exe)

    def test_incorrect_size_and_missing_file_refused(self):
        self.proof["exe_bytes"] += 1
        with self.assertRaises(ValueError):
            validate_scan_receipt(self.proof, self.exe)
        self.proof["exe_bytes"] -= 1
        self.exe.unlink()
        with self.assertRaises(ValueError):
            validate_scan_receipt(self.proof, self.exe)

    def test_disabled_defender_cannot_claim_scan(self):
        self.observed()
        self.proof["defender_availability"] = "DISABLED"
        with self.assertRaises(ValueError):
            validate_scan_receipt(self.proof, self.exe)


if __name__ == "__main__":
    unittest.main()
