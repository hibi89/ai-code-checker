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
