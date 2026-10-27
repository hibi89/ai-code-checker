# P1-L Windows read-only acceptance — 2026-10-27 KST

## Source / authoritative CI
- [PR #23](https://github.com/hibi89/ai-code-checker/pull/23) **MERGED** as code commit `f7fccd8f1440b1ca562c341ca4a21f2dd124b363`; verified feature SHA `19496ba18e3b213d2589118407543b029dab6763`, previous main `17b9eb9d4ff66a803df9e2ac5593a746f96d8d29`.
- [General Tests 40498518599](https://github.com/hibi89/ai-code-checker/actions/runs/40498518599): **16/16 jobs PASS**, Windows Python 3.11 **185 unit tests PASS**, including 10 new local-receipt contract cases.
- [Windows EXE + Tk + PDF + provenance 40498518640](https://github.com/hibi89/ai-code-checker/actions/runs/40498518640): **1/1 job PASS**. Actual Windows job logs: `PACKAGED_TK_FULL_WORKFLOW_PASS`, `WINDOWS_ACCEPTANCE_LOCAL_READONLY_CAPTURED`, `DEFENDER_SETTINGS_OBSERVED=True`, `WINDOWS_ACCEPTANCE_READONLY_EVIDENCE_PASS`, `BINARY_HASH_MATCH=True`, `RETAIL_OS_PACKET_SMARTSCREEN_PDF_NOTICE=UNVERIFIED`, `CUSTOMER_RELEASE_READY=False`.
- CI confirms the *hosted runner's* Defender settings were readable. This **does not mean the EXE passed an actual antivirus scan**, Defender has judged it clean, SmartScreen accepted it, or network packets were captured.

## Implementation and acceptance semantics
- `scripts/windows_acceptance_readonly.ps1`: **only on explicit invocation**, reads existing EXE bytes/SHA-256 and read-only Authenticode and Defender settings, serializes minimal local data using CreateNew so no evidence overwrites. Does not change registry, Windows security services, firewall/packet configuration, browser state, operating-system policies or customer files. No full executable path, username, customer content, token or host identity in the JSON.
- `scripts/windows_acceptance_contract.py`: verifies exact evidence schema and signed-up binary SHA and size, rejects extra keys, invalid booleans, forged claimed PASS/approval and missing files. All actual retail, packet, Defender file scan, SmartScreen, visual PDF, legal NOTICE remain strictly UNVERIFIED; customer and legal releases stay false.
- `tests/test_windows_acceptance_contract.py`: 10 synthetic cases including unchanged receipt, tampered EXE bytes, altered length, missing Defender, pending-gate forgery, signature enum, extra PII fields and missing/symlink executable.
- `.github/workflows/windows-portable.yml`: after developer EXE build, runs PowerShell capture and Python receipt validator **before** existing component provenance / original-license review assertions. Receipts are retained locally on the runner; no artifact upload. The actual unsigned executable also stays local. This is **not commercial release**.

## Engineering tradeoffs
- Rejected an automatic firewall-rule, packet-monitor or SmartScreen/Defender scanning procedure, which may require administrator rights, touch user settings, execute unapproved machine-specific operations and still not establish retail-machine safety.
- Selected simple OS read-only observations and a fail-closed evidence contract. No recurring API cost or dependency added to the shipped EXE, and normal GUI/Gemini v1 behavior unchanged.

## Remaining release blockers
1. Actual clean retail Windows device GUI operation and user acceptance, not hosted GitHub CI.
2. Defender *specific EXE scan* result and observed SmartScreen behavior, without bypasses.
3. OS-level packet capture under owner-approved conditions; no network or exfiltration claims until tested, and local synced folders/mapped drives remain an environmental risk.
4. Human inspection of rendered Korean PDF across printers/page sizes.
5. Complete original binary third-party NOTICE and redistributed component license signoff, code signature and owner release approval.

No Vercel production applicable. No OS modifications or customer data uploads were conducted. Rollback: revert PR #23, never force push. Documentation commits following merge change main HEAD without implying a new CI run.
