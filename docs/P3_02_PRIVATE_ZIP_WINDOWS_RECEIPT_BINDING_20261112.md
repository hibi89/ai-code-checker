# P3-02 — exact EXE + private candidate ZIP + existing Windows receipt cross-check

2026-11-12 KST · Code Checker v2. Owner-side offline *candidate* QA only.

## Gap and architecture

P3-01 can make an explicitly local, still-unapproved candidate ZIP from supplied original texts and EXE. The historical `scripts.verify_customer_zip_candidate` checks its exact EXE and structure; `scripts.consolidate_windows_retail_evidence` independently reconciles the same EXE against pre-existing Windows GUI smoke and OS read-only receipts. **Previously there was no cross-check tying both independent outcomes to the same physical binary/ZIP**.

A: accept self-declared ZIP/receipt JSON matching strings, auto-approve shipment. Rejected: forged/stale evidence and legal/customer rights remain unverified.

B: independently call the existing exact-source validators for actual physical ZIP/EXE and the original Windows receipt validators, match **sha256 + byte count**, then reread the ZIP/EXE after combining evidence and refuse changed evidence. Every human approval gate remains UNVERIFIED. Chosen: no new external dependencies, no Windows/Defender calls, no private data upload, no new executable distribution.

## Owner-only command (uses EXISTING receipts, never creates them)

```powershell
python -m scripts.link_private_candidate_evidence `
  --exe "C:\Private\CodeCheckerOffline.exe" `
  --zip "C:\Private\candidate-FRESH.zip" `
  --readonly "C:\Private\windows-acceptance-readonly.json" `
  --smoke "C:\Private\windows-local-exe-smoke.json" `
  --runtime "C:\Private\runtime-version-receipt.json" `
  --defender "C:\Private\defender-custom-scan.json" `
  --out "C:\Private\candidate-evidence-FRESH.json"
```

`--runtime`, `--defender`, and `--out` optional. Required paths absolute, all inputs distinct. Output path must be a new local `.json`; no overwrites. Never upload EXE/receipts/private LICENSE to this public GitHub repository.

Result: `PRIVATE_ZIP_AND_WINDOWS_RECEIPTS_LINKED_RELEASE_BLOCKED`, exact EXE+ZIP SHA256, number of package entries, available/omitted evidence and eight `human_release_gates=UNVERIFIED`. Both `customer_release_ready` and `owner_release_approval` always false. A valid Windows hosted-runner receipt does not become consumer Win10/11 GUI/SmartScreen/Defender/passive OS packet/PDF approval.

## Verification scope

- Linux Python3.13 isolated `python -m unittest discover -s tests -v` against **local synthetic only shims for the already existing Code Checker source validators**: 20 PASS, 0 FAIL, 0 SKIP (12 P3-01 + 8 P3-02). Tested exact SHA/size matching, altered same-size binary rejection, forged ZIP release states, forged buyer-gate states, stale ZIP after receipt validation, CLI no-overwrite/no-private-path disclosure.
- The new two source/test file Git Blob SHAs exactly matched the local executed bytes. Existing full `input_safety`, `inspect_candidate`, `consolidate`, Windows EXE packaging and the repository-wide unittest+dependency audit **are not verified by local shims**. A draft PR #82 was opened for real repository CI, which was queued at last observation.
- No original LICENSE/NOTICE was generated, authenticated, converted or sent. License/NOTICE authority for **71 unresolved EXE archive items** remains blocked; buyer Windows 10/11 physical acceptance, SmartScreen, Defender, Korean PDF visual, OS network/packet and owner-sale approval remain unverified. No Vercel/Production applies to offline customer EXE.

Engineering completion remains **78% provisional until same-SHA real integration/product acceptance evidence**. 85% requested is not achieved merely by creating these developer-side helpers; user-approved release is separate.
