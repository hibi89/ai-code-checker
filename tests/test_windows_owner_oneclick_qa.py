"""Owner one-command PowerShell QA: fail-closed path/overwrite contracts.

Positive candidate EXE execution is independently checked by the actual
Windows portable workflow. These unit tests NEVER execute synthetic EXEs.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "windows_owner_oneclick_qa.ps1"


@unittest.skipUnless(os.name == "nt", "PowerShell QA is Windows-only")
class OwnerOneClickWindowsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pwsh = shutil.which("pwsh")
        if self.pwsh is None:
            self.skipTest("PowerShell 7 is not installed")
        holder = tempfile.TemporaryDirectory(prefix="code-checker-owner-qa-")
        self.addCleanup(holder.cleanup)
        self.folder = Path(holder.name)
        self.exe = self.folder / "synthetic.exe"
        self.exe.write_bytes(b"MZ inert fixture -- NEVER LAUNCH")
        self.evidence = self.folder / "owner-evidence"

    def run_owner(self, exe: Path, output: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run([
            self.pwsh, "-NoProfile", "-NonInteractive", "-File", str(SCRIPT),
            "-ExePath", str(exe), "-EvidenceDir", str(output),
        ], capture_output=True, text=True, errors="replace", timeout=30, check=False)

    def test_script_parser_has_no_errors(self):
        # pwsh -Command does not reliably populate $args[0] for a trailing
        # positional path. Pass a quoted literal to the parser instead.
        quoted_source = str(SCRIPT).replace("'", "''")
        command = (
            "$tokens = $null; $errors = $null; "
            "[System.Management.Automation.Language.Parser]::ParseFile("
            f"'{quoted_source}', [ref]$tokens, [ref]$errors) | Out-Null; "
            "if ($errors.Count -ne 0) { $errors | Out-String | Write-Error; exit 1 }"
        )
        result = subprocess.run([
            self.pwsh, "-NoProfile", "-NonInteractive", "-Command", command,
        ], capture_output=True, text=True, timeout=30, errors="replace")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_existing_output_is_never_reused(self):
        self.evidence.mkdir()
        (self.evidence / "original.txt").write_text("preserve", encoding="utf-8")
        result = self.run_owner(self.exe, self.evidence)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.evidence / "original.txt").read_text(encoding="utf-8"),
                         "preserve")
        self.assertFalse((self.evidence / "owner-preflight.json").exists())

    def test_missing_executable_cannot_create_evidence(self):
        missing = self.folder / "missing.exe"
        result = self.run_owner(missing, self.evidence)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.evidence.exists())

    def test_unc_executable_is_rejected_before_any_start(self):
        result = self.run_owner(Path(r"\\fake-server\fake-share\input.exe"), self.evidence)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.evidence.exists())

    def test_linked_exe_is_rejected_without_execution(self):
        link = self.folder / "linked.exe"
        try:
            link.symlink_to(self.exe)
        except (OSError, NotImplementedError):
            self.skipTest("Windows symlink permission unavailable")
        result = self.run_owner(link, self.evidence)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.evidence.exists())

    def test_linked_output_parent_rejected(self):
        root = self.folder / "actual"
        root.mkdir()
        link = self.folder / "linked-parent"
        try:
            link.symlink_to(root, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Windows symlink permission unavailable")
        result = self.run_owner(self.exe, link / "owner-evidence")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((root / "owner-evidence").exists())


class ManualGateContractTests(unittest.TestCase):
    """The human worksheet must match the ten machine-readable blocked gates."""

    def test_checklist_has_exactly_one_row_per_manual_gate(self):
        import re

        source = SCRIPT.read_text(encoding="utf-8")
        gate_section = source.split("$gates = [ordered]@{", 1)[1].split("\n}", 1)[0]
        gates = re.findall(r"(?m)^    ([a-z_]+) = 'UNVERIFIED'$", gate_section)
        manual_section = source.split('$manual = @"', 1)[1].split('"@', 1)[0]
        checklist = re.findall(r"(?m)^- \\[ \\] \\[([a-z_]+)\\] ", manual_section)
        self.assertEqual(len(gates), 10)
        self.assertEqual(checklist, gates)
        self.assertEqual(manual_section.count("- [ ]"), 10)
        self.assertIn("MANUAL_CHECKS=10_UNVERIFIED", source)
        self.assertIn("customer_release_ready = $false", source)


if __name__ == "__main__":
    unittest.main()
