# P1-V — actual frozen EXE NOTICE/license review-gap ledger (2026-10-27 KST)

## Goal
Prior P0-D/E/F/G/H runs already established archive/PYZ name accounting, candidate distribution ownership, local installed original license evidence and native build-file relationships. These are not evidence that required copyrights, binary vendor versions, redistribution obligations, and final customer NOTICE are known. P1-V adds a verifiable cross-document review queue rather than mistakenly treating name-based metadata as legal certification.

## Engineering choice
- **A: publish a NOTICE using installed metadata labels.** Quick and cheap but highly unsafe: overlooks actual packaged bootloader, Tcl/Tk/CPython/VC and vendor license conditions; would misrepresent approved redistribution. Rejected.
- **B: reconcile existing actual frozen EXE five-stage local evidence by binary SHA and original-license metadata.** No extra build/runtime dependencies, zero API cost, no untrusted source execution, bounded JSON. Produces local review tasks that cannot certify any component. Chosen.
- **C: full primary legal/clean consumer Windows acceptance.** Requires original applicable texts, component-owner confirmation and human review on actual distribution; still pending. Never inferred from B.

## Changed code and reproducible local Windows invocation
- `scripts/reconcile_notice_gaps.py`: checks the same EXE SHA-256 across P0-D, E, F, G and H; exact CArchive and PYZ name sets (Windows backslashes normalized to mapping forward slashes), exact per-category counts, distro candidate sets, original installed LICENSE metadata and collection gap counts, native/unmatched EXE/PKG build TOC accounting. Uses Python standard library only and refuses approved flags.
- `tests/test_notice_gap_ledger.py`: negative tests include forged legal-release approvals, changed SHA at each stage, tampered module name, omitted distribution, invalid LICENSE SHA, mismatched P0-F/G/H sets, sensitive paths and a **single Windows backslash** regression.
- `.github/workflows/windows-portable.yml`: after packaged unsigned EXE, existing Defender, P0-D/E/F/G/H checks, runs P1-V to `.build-windows/notice-review-gaps.json` in ignored workspace. Verifies no copyright owner, final NOTICE, license compliance or customer release is authorized; does not upload any original LICENSE or binary. Developer may run:
```powershell
python -m scripts.reconcile_notice_gaps --audit .build-windows/frozen-exe-evidence.json --mapping .build-windows/ownership-candidates.json --native .build-windows/native-provenance.json --exe-toc .build-windows/exe-toc-evidence.json --pkg-toc .build-windows/pkg-toc-evidence.json --out .build-windows/notice-review-gaps.json
```
Use an existing local build workspace and a NEW output path; do not overwrite receipts or publish them.

## Observed actual hosted Windows synthetic candidate
- Source SHA `b22db78cc8c840c6a8f87909308f6638d19f92b2`, [Windows portable run 40523678817](https://github.com/hibi89/ai-code-checker/actions/runs/40523678817) **SUCCESS**, [General 16/16 Tests 40523679110](https://github.com/hibi89/ai-code-checker/actions/runs/40523679110) **SUCCESS**.
- Log: `NOTICE_REVIEW_GAP_LEDGER_PASS`; `EXE_METADATA_ALL_ROWS_RECONCILED=True`; `INSTALLED_DISTRIBUTION_CANDIDATES=7`; `ORIGINAL_LICENSE_FILES_STAGED=26`; `ORIGINAL_LICENSE_FILE_GAPS=0`; `UNRESOLVED_ARCHIVE_NAMES=92`; `PKG_TOC_NO_CLAIMS=1`; `NOTICE_READY_TO_DISTRIBUTE=False`; `CUSTOMER_RELEASE_READY=False`.
- 92 is the tally of archive name *classification gaps*, not a list of 92 proven illegal/unlicensed binaries. Previous P0-F evidence had exact build-source bytes for 67 native files; still does not identify copyright owner or rights.
- The absence of missing original installed license texts on this CI runner **does not establish that originals cover every binary or are included within the EXE**; installed packages may be build-only. One unmatched TOC name means insufficient build metadata, not a demonstrated licensing violation.

## Failures and corrections
- [Windows 40522833807](https://github.com/hibi89/ai-code-checker/actions/runs/40522833807) initially failed new ledger; diagnostic improvement confirmed raw P0-D Windows backslash name and normalized P0-E forward slash mismatch in [40523200040](https://github.com/hibi89/ai-code-checker/actions/runs/40523200040). Normalized exactly one backslash in the input and added a test. Hash-only repeated installed license originals are legal duplicate text candidates and no longer rejected without basis.
- Final exact source SHA retested green; any subsequent docs change must rerun CI at new SHA and PR must be verified before merge.

## Outstanding customer release gates
Human source-backed check for CPython/PSF, Tcl/Tk, PyInstaller bootloader license exception, Microsoft/VC runtime and all actual bundled package original notices and copyrights. No final NOTICE assembled/approved. Independent clean physical Windows executable behavior, Defender/SmartScreen actual customer evidence, OS network packet observation, Korean PDF human visual, owner commercial signoff remain UNVERIFIED. No Vercel or binary distribution. 


## Actual feature merge evidence — 2026-10-27 KST

- Final P1-V feature SHA `3e5a8a6d5bf35cc59ce777585b82af8d16acb053`: [Tests 40524354220](https://github.com/hibi89/ai-code-checker/actions/runs/40524354220) **completed success 16/16** and [Windows portable run 40524354171](https://github.com/hibi89/ai-code-checker/actions/runs/40524354171) **completed success**.
- [PR #33](https://github.com/hibi89/ai-code-checker/pull/33) merged; actual GitHub main source SHA `83a98739dc966ab4ecf1213a37d7931d146b2057`. Main Tests #40524769112 pending on initial reading. Subsequent documentation SHA must be checked independently.
- No full legal compliance/approved NOTICE/customer binary/retail Windows, SmartScreen, OS packet or PDF human visual evidence is implied. The ledger remains a local diagnostic.
