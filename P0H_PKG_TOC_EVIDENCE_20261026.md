# Phase2 P0-H — last unmatched PyInstaller PKG build TOC item

Date: 2026-10-26 KST. Prior main baseline `491348598da42aba431302712d0c257efa5a7b1b` (16/16 Tests CI green). [P0-G](P0G_EXE_TOC_EVIDENCE_20261026.md) found 11 unique EXE-stage packaging-name claims from 12 remaining P0-F names, leaving one missing. This report tracks a further metadata-only step; no license or redistribution approval is implied.

## Alternatives / decision

- **Guess based on name/type:** zero runtime cost but produces unsupported copyright and dependency assumptions.
- **Compare generated `PKG-00.toc` from the same actual EXE build:** zero required external API cost, simple bounded literal parsing, verifiable exact-name matching. Chosen to avoid invented owner claims. PKG records still may not record runtime-generated entries.

## Method

`scripts/reconcile_pkg_toc.py` consumes P0-G and P0-D local ignored JSON (same EXE SHA), then safely parses a build-local PyInstaller `PKG-00.toc` with the P0-G bounded `ast.literal_eval` reader. It checks only prior nonmatching names, validates observed CArchive typecodes and counts, records exact-name PKG candidates, and suppresses all source absolute paths. Local evidence `.build-windows/pkg-toc-evidence.json` never leaves the CI runner; CI logs only summary category counts.

Classifications: `unique_pkg_toc_record_claim_only`, `ambiguous_pkg_toc_records`, `no_pkg_toc_record`. No classification means verified license, owner, release approval, or legitimate installed Python/Tcl/Tk/VC provenance. If the single entry is a PKG `OPTION` with source `None`, that is packaging metadata only; do not misreport a missing license. Missing records remain unresolved, not defects by default.

Synthetic tests cover exact/missing/ambiguous mapping, EXE identity, fail-closed approvals, duplicate entries, and source path suppression. New Windows CI step reuses an already built unsigned local EXE and is not a distribution/upload.

## Next evidence and remaining gates

Record actual Windows CI counts once run. Even if PKG metadata matches the final entry, CPython/Tcl/Tk/VC/PyInstaller notices and terms, real clean Windows behavior, Defender/SmartScreen, OS-level packet observation, interactive PDF visual review, and scanner accuracy are still UNVERIFIED. Customer EXE publication and monetization require explicit owner approval. No Vercel. Do not use customer code or paid model APIs.

## Actual Windows runner results (2026-10-26 KST)

- Feature implementation SHA `1a5dab52c3d5670004ff61a7b9cf4371f5810844`, [regular CI 16/16 PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40330934255), **126/126 unit tests PASS** ([push CI](https://github.com/hibi89/ai-code-checker/actions/runs/40330886695)), [Windows packaged P0-H CI PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40330934463). Post-documentation SHA must be verified again.
- The actual onefile rebuilt Windows EXE confirmed P0-G **1** unmatched CArchive item. P0-H exact PKG-stage metadata result: `PREVIOUS_NO_EXE_TOC_CLAIMS=1`, **`PKG_UNIQUE_NAME_CLAIMS=0`**, `PKG_AMBIGUOUS=0`, **`PKG_NO_CLAIM=1`**. No new build record match. The package build records cannot establish its origin from these two sources; classify as **unresolved**, not as a missing component/defect or approved license.
- **Stop & Pivot:** two separate TOC metadata scopes (EXE-00 and PKG-00) offer no record for this single entry. Do not repetitively relabel or re-run with no new evidence. Record specific local forensic follow-up only with actual artifact/type information available; prioritize P1-D reproducible scanner-accuracy labeled corpus / conservative Python and JS/TS rules next, without claiming exhaustive coverage or executing scanned code. Licensing and real clean Windows checks remain mandatory before sale.

## Final verified merge (2026-10-26 KST)

- Final P0-H feature `325d365d2731aaed271b8b6500193fbe4acfdb7b` passed [16/16 standard jobs, 126 unit tests](https://github.com/hibi89/ai-code-checker/actions/runs/40331433872), [Windows EXE packaged P0-H CI](https://github.com/hibi89/ai-code-checker/actions/runs/40331434064), merged [PR #12](https://github.com/hibi89/ai-code-checker/pull/12) to main at `07a358956264ef7488a5912aa3c970f9dd69d16d`. The original main post-merge CI `40331742286` was running when documented; newest document commit also requires CI verification.
- No added PKG-stage build name evidence for 1 remaining entry. Treat as unresolved evidence, not proven defect; future priority accuracy/testing then real Windows and primary licenses, not unlimited repeats of TOC scans. No customer release approval.
