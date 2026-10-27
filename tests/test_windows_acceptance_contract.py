"""Synthetic contract tests for local read-only Windows acceptance receipts."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.windows_acceptance_contract import FORMAT, PENDING, validate_evidence


def example(executable: Path) -> dict:
    data = executable.read_bytes()
    return {
        "format": FORMAT,
        "collection_method": "win32_readonly_powershell",
        "scope": "local_binary_only",
        "exe_sha256": hashlib.sha256(data).hexdigest(),
        "exe_bytes": len(data),
        "signature_observation": "NotSigned",
        "defender": {
            "availability": "UNVERIFIED",
            "antivirus_enabled": None,
            "real_time_protection_enabled": None,
        },
        "pending_gates": {key: "UNVERIFIED" for key in PENDING},
        "customer_release_ready": False,
        "legal_notice_approved": False,
    }


class LocalWindowsAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.exe = Path(self.temp.name) / "CodeCheckerOffline.exe"
        # Bytes are synthetic and never executed as a real executable.
        self.exe.write_bytes(b"MZ\x00synthetic inert binary for receipt tests")
        self.proof = example(self.exe)

    def test_hash_matches_without_certifying_retail_acceptance(self):
        outcome = validate_evidence(self.proof, self.exe)
        self.assertTrue(outcome["local_exe_hash_verified"])
        self.assertFalse(outcome["customer_release_ready"])
        self.assertEqual(outcome["pending_gate_count"], len(PENDING))
        self.assertFalse(outcome["defender_settings_observed"])

    def test_report_invalid_if_executable_changed_same_size(self):
        self.exe.write_bytes(self.exe.read_bytes().replace(b"synthetic", b"synThetic", 1))
        with self.assertRaises(ValueError):
            validate_evidence(self.proof, self.exe)

    def test_report_invalid_if_executable_size_changes(self):
        self.exe.write_bytes(self.exe.read_bytes() + b"X")
        with self.assertRaises(ValueError):
            validate_evidence(self.proof, self.exe)

    def test_defender_settings_observed_is_not_executable_antivirus_pass(self):
        self.proof["defender"] = {
            "availability": "OBSERVED",
            "antivirus_enabled": True,
            "real_time_protection_enabled": True,
        }
        result = validate_evidence(self.proof, self.exe)
        self.assertTrue(result["defender_settings_observed"])
        self.assertFalse(result["customer_release_ready"])

    def test_missing_defender_observation_cannot_claim_true(self):
        self.proof["defender"]["antivirus_enabled"] = True
        with self.assertRaises(ValueError):
            validate_evidence(self.proof, self.exe)

    def test_manual_acceptance_cannot_be_forged_as_pass(self):
        for key in PENDING:
            with self.subTest(key=key):
                case = json.loads(json.dumps(self.proof))
                case["pending_gates"][key] = "PASS"
                with self.assertRaises(ValueError):
                    validate_evidence(case, self.exe)

    def test_release_or_legal_approval_cannot_be_asserted(self):
        for key in ("customer_release_ready", "legal_notice_approved"):
            with self.subTest(key=key):
                case = json.loads(json.dumps(self.proof))
                case[key] = True
                with self.assertRaises(ValueError):
                    validate_evidence(case, self.exe)

    def test_extra_path_or_personal_metadata_rejected(self):
        for key in ("username", "exe_full_path", "customer_source", "token"):
            with self.subTest(key=key):
                case = json.loads(json.dumps(self.proof))
                case[key] = "not collected"
                with self.assertRaises(ValueError):
                    validate_evidence(case, self.exe)

    def test_wrong_signature_enum_and_bad_hash_rejected(self):
        case = json.loads(json.dumps(self.proof))
        case["signature_observation"] = "verified safe for distribution"
        with self.assertRaises(ValueError):
            validate_evidence(case, self.exe)
        case = json.loads(json.dumps(self.proof))
        case["exe_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            validate_evidence(case, self.exe)

    def test_no_executable_or_symlink_is_accepted(self):
        missing = Path(self.temp.name) / "missing.exe"
        with self.assertRaises(ValueError):
            validate_evidence(self.proof, missing)
        alias = Path(self.temp.name) / "alias.exe"
        try:
            alias.symlink_to(self.exe)
        except (NotImplementedError, OSError):
            self.skipTest("Windows symlinks require optional privileges")
        with self.assertRaises(ValueError):
            validate_evidence(self.proof, alias)


if __name__ == "__main__":
    unittest.main()
