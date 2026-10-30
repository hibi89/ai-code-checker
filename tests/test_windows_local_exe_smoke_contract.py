"""Synthetic validator contracts; no Windows executable is launched."""
from __future__ import annotations

import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.windows_local_exe_smoke_contract import (
    FORMAT, PENDING, validate_receipt,
)


def fixture(exe: Path) -> dict:
    raw = exe.read_bytes()
    return {
        "format": FORMAT,
        "collection_method": "two_synthetic_exe_modes_no_python_required",
        "scope": "existing_local_exe_only",
        "exe_sha256": hashlib.sha256(raw).hexdigest(),
        "exe_bytes": len(raw),
        "observed_synthetic": {
            "packaged_tk_gui_startup": "PASS",
            "packaged_preview_scan_report": "PASS",
            "executable_hash_stable": True,
        },
        "pending_gates": {name: "UNVERIFIED" for name in PENDING},
        "actual_customer_code_used": False,
        "actual_customer_release_ready": False,
        "legal_notice_approved": False,
    }


class SyntheticWindowsOwnerSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="code-checker-owner-smoke-")
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        self.exe = self.folder / "fixture.exe"
        self.exe.write_bytes(b"MZ" + b"synthetic bytes only; never executed")
        self.record = fixture(self.exe)

    def test_valid_local_synthetic_receipt_never_claims_customer_release(self) -> None:
        result = validate_receipt(self.record, self.exe)
        self.assertTrue(result["exe_hash_verified"])
        self.assertEqual(result["packaged_tk_and_synthetic_workflow"], "PASS")
        self.assertEqual(result["pending_manual_gates"], 7)
        self.assertFalse(result["customer_release_ready"])

    def test_same_size_executable_tamper_rejected(self) -> None:
        raw = self.exe.read_bytes()
        self.exe.write_bytes(raw.replace(b"synthetic", b"synThetic", 1))
        self.assertEqual(len(raw), self.exe.stat().st_size)
        with self.assertRaises(ValueError):
            validate_receipt(self.record, self.exe)

    def test_missing_symlink_or_wrong_size_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_receipt(self.record, self.folder / "missing.exe")
        self.record["exe_bytes"] += 1
        with self.assertRaises(ValueError):
            validate_receipt(self.record, self.exe)
        self.record["exe_bytes"] -= 1
        link = self.folder / "linked.exe"
        try:
            link.symlink_to(self.exe)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink creation unavailable")
        with self.assertRaises(ValueError):
            validate_receipt(self.record, link)

    def test_tampered_release_or_manual_gate_rejected(self) -> None:
        for name in ("actual_customer_code_used", "actual_customer_release_ready", "legal_notice_approved"):
            with self.subTest(flag=name):
                record = copy.deepcopy(self.record)
                record[name] = True
                with self.assertRaises(ValueError):
                    validate_receipt(record, self.exe)
        for name in PENDING:
            with self.subTest(gate=name):
                record = copy.deepcopy(self.record)
                record["pending_gates"][name] = "PASS"
                with self.assertRaises(ValueError):
                    validate_receipt(record, self.exe)

    def test_forged_success_missing_key_and_wrong_types_rejected(self) -> None:
        changes = [
            lambda r: r["observed_synthetic"].update(packaged_tk_gui_startup="UNVERIFIED"),
            lambda r: r["observed_synthetic"].update(executable_hash_stable=1),
            lambda r: r.update(exe_bytes=True),
            lambda r: r.update(format="different"),
            lambda r: r.pop("scope"),
            lambda r: r.update(unexpected_field="untrusted"),
        ]
        for index, update in enumerate(changes):
            with self.subTest(index=index):
                record = copy.deepcopy(self.record)
                update(record)
                with self.assertRaises(ValueError):
                    validate_receipt(record, self.exe)


if __name__ == "__main__":
    unittest.main()
