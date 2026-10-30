"""Local private Windows build + owner QA opt-in contract.

Never installs dependencies or builds a real EXE inside unit tests.
The actual opt-in path is exercised by the Windows portable workflow.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


BUILDER = Path(__file__).resolve().parents[1] / "scripts" / "build_windows_portable.ps1"


class PrivateCandidateBuildContractTests(unittest.TestCase):
    def test_explicit_opt_in_and_release_guard_present(self):
        script = BUILDER.read_text(encoding="utf-8")
        self.assertIn("[switch]$OwnerAcceptance", script)
        self.assertIn("if ($OwnerAcceptance)", script)
        self.assertIn("$PSBoundParameters.ContainsKey('EvidenceDir')", script)
        self.assertIn("windows_owner_oneclick_qa.ps1", script)
        self.assertIn("$receipt.customer_release_ready -cne $false", script)
        self.assertIn("$gateProperties.Count -ne 10", script)
        self.assertIn("OWNER_PRIVATE_CANDIDATE_PREFLIGHT_PASS_CUSTOMER_RELEASE_BLOCKED", script)
        self.assertNotIn("Install-Package", script)
        self.assertNotIn("Invoke-WebRequest", script)


@unittest.skipUnless(os.name == "nt", "Windows PowerShell-only checks")
class PrivateCandidateBuildWindowsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pwsh = shutil.which("pwsh")
        if cls.pwsh is None:
            raise unittest.SkipTest("PowerShell 7 is not installed")

    def run_builder(self, *options):
        return subprocess.run(
            [self.pwsh, "-NoProfile", "-NonInteractive", "-File", str(BUILDER), *map(str, options)],
            text=True, capture_output=True, errors="replace", timeout=30, check=False,
        )

    def test_missing_evidence_dir_fails_before_build(self):
        result = self.run_builder("-OwnerAcceptance")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("-OwnerAcceptance requires -EvidenceDir.", result.stderr + result.stdout)

    def test_orphan_evidence_dir_fails_before_build(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.run_builder("-EvidenceDir", str(Path(folder) / "new-evidence"))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("-EvidenceDir requires explicit -OwnerAcceptance.", result.stderr + result.stdout)

    def test_existing_evidence_dir_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            old = root / "receipt.json"
            old.write_text("preserve", encoding="utf-8")
            result = self.run_builder("-OwnerAcceptance", "-EvidenceDir", str(root))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("EvidenceDir must be a new local directory.", result.stderr + result.stdout)
            self.assertEqual(old.read_text(encoding="utf-8"), "preserve")


if __name__ == "__main__":
    unittest.main()
