# P1-U Microsoft Defender file scan evidence and limits (2026-10-27 KST)

## Problem
Previous P1-L read-only Windows acceptance receipt reports installed Defender configuration, binary hash and signature status only. It did not cause or substantiate a scan of the EXE. Distinguishing these facts matters before any eventual retail product handoff.

## Implementation / architecture alternatives
1. Only read Windows Defender state through Get-MpComputerStatus: negligible risk but no proof of file scanning, already covered. Not selected.
2. Bounded explicit Microsoft Defender MpCmdRun custom scan of the freshly built synthetic candidate EXE with -DisableRemediation, no signature update or OS policy change, local fixed-schema receipt and SHA verification. Selected. This invokes an AV scanner on CI's EXE but never executes the code checker or untrusted customer code.
3. Full automatic OS Defender/SmartScreen/packet/per-user acceptance: cannot prove on hosted runner, needs owner-controlled clean retail Windows. Deferred.

## Source and command
- `scripts/windows_defender_file_scan.ps1`, PowerShell7+ Windows only, explicit -ExePath and CreateNew -OutputPath on local non-reparse volume, 30-300s bounded timeout.
- Official Microsoft Defender CLI: `MpCmdRun.exe -Scan -ScanType 3 -File <local exe> -DisableRemediation`.
- Availability and command exit, file digest before/after, no file overwrite, no cloud upload, no scanning native command output included in published GitHub logs. Output JSON generated in gitignored `.build-windows/` under Windows CI.
- `scripts/windows_defender_scan_contract.py` checks fixed receipt schema and exact EXE content, and blocks `malware_free_certified`, `retail_defender_acceptance` or `customer_release_ready` approval.
- `tests/test_windows_defender_scan_contract.py` synthetic cases for zero/nonzero/unavailable/timeout, unexpected fields, forged release, modified/missing EXE. `.github/workflows/windows-portable.yml` adds hosted scan and offline contract gates.

## Interpretation
- If scanner unavailable/disabled, `DEFENDER_SCAN_ATTEMPTED=False`, command status `UNVERIFIED`, **NOT PASS**.
- If scanner available and it returns zero, `DEFENDER_COMMAND_ZERO_EXIT=True` reflects command execution **only**, not malware-free certificate or user acceptance. Microsoft documents exit 0 can include detection plus remediation. Nonzero is error/detection ambiguous. With `-DisableRemediation` the tool requests no remediation, but real-time protection may still independently act.
- A change/quarantine or missing EXE after the command invalidates receipt when verifying by actual bytes.
- No evidence of actual retail Windows, customer perception, Defender or SmartScreen reputation, OS-level packet capture, third-party license redistribution rights, or Korean PDF visual.
- User OS configuration, Windows services, firewall, Defender settings and keys are never changed. No permission for commercial distribution.

## References and progress
- Microsoft official MpCmdRun switches/exit code: https://learn.microsoft.com/en-us/defender-endpoint/command-line-arguments-microsoft-defender-antivirus
- Microsoft scan completion/event ID context: https://learn.microsoft.com/en-us/defender-endpoint/troubleshoot-mdav-scan-issues
- [PR #32](https://github.com/hibi89/ai-code-checker/pull/32). The current source/CI status must be rechecked; do not infer a verified scan from this document itself.


## Final source/CI/Defender observation — 2026-10-27 KST

Feature 8ff471435e403b7b9a64e9077ad6ccf8d06c7468: https://github.com/hibi89/ai-code-checker/actions/runs/40520621886 General Tests 16/16 success and https://github.com/hibi89/ai-code-checker/actions/runs/40520621813 Windows EXE/Defender candidate workflow success.
Earlier actual Windows code workflow https://github.com/hibi89/ai-code-checker/actions/runs/40520257918 records DEFENDER_SCAN_ATTEMPTED=True, DEFENDER_SCAN_COMMAND_STATUS=ZERO_EXIT, DEFENDER_SCAN_RECEIPT_INTEGRITY_PASS, DEFENDER_COMMAND_ZERO_EXIT=True, MALWARE_FREE_CERTIFIED=False, CUSTOMER_RELEASE_READY=False.
PR #32 https://github.com/hibi89/ai-code-checker/pull/32 merged main source 0bd567c4f89df5230a6a6b767fa65f0c74e0a318. Main post-merge Tests 40521006809 was pending on initial check. No user retail OS malware/SmartScreen, OS packet proof, native NOTICE/legal, PDF human visual or product sale approval is inferred.
