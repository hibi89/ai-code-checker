"""Windows-only executable evidence preflight regression tests.

All EXE bytes are inert synthetic fixtures; the PowerShell tool reads their
metadata only and MUST NOT start them or alter Windows security settings.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "windows_acceptance_readonly.ps1"


@unittest.skipUnless(os.name == "nt", "Read-only PowerShell preflight is Windows-only")
class WindowsAcceptancePathsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pwsh = shutil.which("pwsh")
        if self.pwsh is None:
            self.skipTest("PowerShell 7 unavailable")
        self.folder = tempfile.TemporaryDirectory(prefix="checker-acceptance-")
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.exe = self.root / "synthetic.exe"
        self.exe.write_bytes(b"MZ" + b"inert fixture, never executed")

    def collect(self, exe: Path, output: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                self.pwsh, "-NoProfile", "-NonInteractive", "-File", str(SCRIPT),
                "-ExePath", str(exe), "-OutputPath", str(output),
            ],
            capture_output=True, text=True, timeout=45, check=False,
        )

    def test_regular_local_receipt_retains_unverified_release_gates(self) -> None:
        output = self.root / "evidence.json"
        process = self.collect(self.exe, output)
        self.assertEqual(process.returncode, 0, process.stderr[-1200:])
        evidence = json.loads(output.read_text(encoding="utf-8-sig"))
        self.assertEqual(evidence["exe_sha256"], hashlib.sha256(self.exe.read_bytes()).hexdigest())
        self.assertFalse(evidence["customer_release_ready"])
        self.assertFalse(evidence["legal_notice_approved"])
        self.assertTrue(all(gate == "UNVERIFIED" for gate in evidence["pending_gates"].values()))

    def test_rejects_unc_and_refuses_any_evidence_output(self) -> None:
        output = self.root / "denied.json"
        process = self.collect(Path(r"\\not-a-real-server\share\fake.exe"), output)
        self.assertNotEqual(process.returncode, 0)
        self.assertFalse(output.exists())

    def test_rejects_linked_parent_before_writing_receipt(self) -> None:
        destination = self.root / "actual"
        destination.mkdir()
        self.exe.rename(destination / "synthetic.exe")
        alias = self.root / "linked"
        try:
            alias.symlink_to(destination, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Directory symlink creation requires Windows permission")
        output = self.root / "not-written.json"
        process = self.collect(alias / "synthetic.exe", output)
        self.assertNotEqual(process.returncode, 0)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
