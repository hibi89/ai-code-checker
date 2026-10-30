"""Purely synthetic frozen Tcl/Tk runtime evidence contract tests."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.runtime_version_receipt import (
    capture_receipt, main, verify_receipt, write_frozen_receipt,
)


class FakeTk:
    destroyed = False

    def __init__(self):
        self.tk = self

    def withdraw(self):
        pass

    def call(self, *args):
        return {
            ("info", "patchlevel"): "8.6.15",
            ("set", "tk_patchLevel"): "8.6.15",
        }[args]

    def destroy(self):
        self.destroyed = True


class FrozenRuntimeReceiptTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.exe = Path(tmp.name) / "CodeCheckerOffline.exe"
        self.exe.write_bytes(b"MZ-synthetic-test-only")

    def receipt(self):
        return capture_receipt(self.exe, FakeTk, frozen=True, python_version="3.13.9")

    def test_exact_binary_and_runtime_versions(self):
        result = self.receipt()
        verify_receipt(result, self.exe)
        self.assertEqual(result["tcl_runtime_patchlevel"], "8.6.15")
        self.assertEqual(result["tk_runtime_patchlevel"], "8.6.15")
        self.assertFalse(result["customer_release_ready"])
        self.assertNotIn(str(self.exe.parent), str(result))

    def test_changed_binary_rejected(self):
        result = self.receipt()
        self.exe.write_bytes(b"MZ-synthetic-test-onlY")
        with self.assertRaises(ValueError):
            verify_receipt(result, self.exe)

    def test_premature_customer_approval_rejected(self):
        result = self.receipt()
        result["customer_release_ready"] = True
        with self.assertRaises(ValueError):
            verify_receipt(result, self.exe)

    def test_extra_source_paths_rejected(self):
        result = self.receipt()
        result["installed_absolute_source_path"] = "private"
        with self.assertRaises(ValueError):
            verify_receipt(result, self.exe)

    def test_non_frozen_run_rejected(self):
        with self.assertRaises(ValueError):
            capture_receipt(self.exe, FakeTk, frozen=False, python_version="3.13.9")

    def test_invalid_tcl_version_rejected(self):
        class BadTk(FakeTk):
            def call(self, *args):
                return "C:/secret" if args[0] == "info" else "8.6.15"
        with self.assertRaises(ValueError):
            capture_receipt(self.exe, BadTk, frozen=True, python_version="3.13.9")

    def test_normal_python_cannot_write_frozen_receipt(self):
        with self.assertRaises(ValueError):
            write_frozen_receipt(self.exe.with_suffix(".json"))

    def test_no_args_does_not_create_receipt(self):
        self.assertEqual(main([]), 2)


if __name__ == "__main__":
    unittest.main()
