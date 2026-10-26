# CODE CHECKER Phase2 P0-E — Component ownership hypotheses and ORIGINAL license draft

Date: 2026-10-26 KST. This work improves the **evidence for a human legal review**; it never auto-certifies redistribution. Main parent baseline `e42d597ded7661f68f1760dfe49b352d82933b2e`, standard CI 16/16 PASS.

## What is inspected

- Inputs: local `.build-windows/frozen-exe-evidence.json`, created from the actual built PyInstaller EXE using P0-D. The manifest has 1,018 CArchive names, 544 embedded PYZ module names on the P0-D recorded runner; exact results may change with builds.
- `scripts/map_frozen_licenses.py` **accounts for each** top-level CArchive entry and PYZ module by metadata name. Its categories include first-party name candidate, installed Python distribution name candidate, ambiguous third-party name, CPython standard library name candidate, CPython runtime DLL candidate, Tcl/Tk resource/DLL candidate, installed native exact *relative filename* candidate, unknown native or system DLL, and unknown resource/bootloader. It never labels native ownership as proven from names.
- For candidate Python packages, uses installed package metadata `packages_distributions()` and the distribution's RECORD-reported native file paths. One installed distribution can claim a module, multiple can claim it, or none; all these distinctions are kept in the JSON. PYZ module names are not file hashes; no byte-for-byte source/library provenance has been established.
- Creates local `.build-windows/ownership-candidates.json` (all rows, mapping category, candidate owner list, unresolved counts). This file stays **local to the CI runner** and is not published.
- Creates local `.build-windows/NOTICE_REVIEW_DRAFT.md`, containing **original installed license text candidates** from only the mapped installed distributions plus PyInstaller's installed license evidence. Every read file is checked against both its installed Python distribution RECORD path and SHA256 from P0-D. Hash disagreement is a test **failure**; missing texts are explicitly counted. Texts are not assumed embedded in EXE, and the file is emphatically **NOT FOR DISTRIBUTION**.
- Windows CI checks no archive/PYZ entries silently omitted, at least one identified installed package candidate, at least one staged license original, and all false approval flags (`license_compliance_certified`, `third_party_notice_ready_to_distribute`, `customer_release_ready`). The review draft and unsigned EXE are **not uploaded**.

## What a human reviewer still must do

| Task | Status after P0-E | Why it remains |
|---|---|---|
| Metadata inventory and package owner candidates | Automated, with unresolved names retained | Name matching cannot prove exact binary owner/version |
| Original installed LICENSE text and SHA256 | Local staged candidates only | Some packages are build-only; shipped package versions/other vendored components can differ |
| CPython standard library and runtime license | REQUIRED | Python DLL / stdlib ownership, exact build and applicable PSF notice still need direct evidence |
| Tcl/Tk and any Tcl script resources | REQUIRED | Need exact Tcl/Tk distribution license/origin and notice obligations |
| Windows/VC and other `.dll`/`.pyd` | REQUIRED | Map system/native binaries, vendor, redistribution rights, and file hashes |
| PyInstaller bootloader/license exception | REQUIRED | Inspect full applicable license/exception and distribution contract; installed license is merely evidence |
| Final third-party NOTICE for customers | BLOCKED | Human component-by-component notice/legal sign-off has not occurred |
| Signed EXE/customer-PC/SmartScreen/offline packets/PDF visuals | UNVERIFIED | Needs actual independent device/observed acceptance |

## Commands (authorized CI or developer Windows)

1. Run `./scripts/build_windows_portable.ps1` after installing pinned `requirements-offline-build.txt`.
2. Run `python -m scripts.audit_frozen_exe --exe dist-windows/CodeCheckerOffline.exe --out .build-windows/frozen-exe-evidence.json`.
3. Run `python -m scripts.map_frozen_licenses --audit .build-windows/frozen-exe-evidence.json --mapping-out .build-windows/ownership-candidates.json --notice-draft-out .build-windows/NOTICE_REVIEW_DRAFT.md`.
4. Run `python -m unittest discover -s tests -v`; workflow `.github/workflows/windows-portable.yml` repeats the synthetic GUI/PDF/EXE acceptance as before.

## Interpretation

PASS means: **the built EXE manifest has an exhaustively recorded name-based ownership-candidate classification and original installed license text candidates in a local, hash-checked draft.** It does NOT mean final legal license compliance, binary hash-level provenance, complete CPython/Tcl/Tk/VC notices, or readiness to publish and sell. Next scope: direct native-file provenance/missing license resolution and real Windows product acceptance before owner-authorized commercialization.

## Observed Windows CI results and proof status (2026-10-26 KST)

- Source head `73341809baf06b30d5472dcb8dfeacaa7a2b03ec`: [Windows integration CI 40321463677](https://github.com/hibi89/ai-code-checker/actions/runs/40321463677) **PASS**. [Regular CI 40321463525](https://github.com/hibi89/ai-code-checker/actions/runs/40321463525) **16/16 PASS**, **104 unittest PASS**. [PR #9](https://github.com/hibi89/ai-code-checker/pull/9) merged main at `765ed9d4a9f183e749dfd78d0dc185d73694c609`. Always verify post-merge main separately.
- **1,562/1,562 names classified** (1,018 CArchive, 544 PYZ). Classification is by NAME only, not hash-level binary ownership or legally confirmed attribution.
- Identified *7 installed package ownership candidates*: `annotated-types`, `packaging`, `pydantic`, `pydantic-core`, `setuptools`, `typing-extensions`, `typing-inspection`. These are *candidates* only, not seven legally confirmed EXE component owners.
- Category counts: 276 CPython stdlib name candidates, 923 Tcl/Tk filename/resource candidates, 261 installed Python package name claims, 1 installed native exact-relative-filename candidate, 1 CPython runtime filename candidate, 8 first-party name candidates, **67 unresolved native/system binaries**, **25 unresolved archive resources/bootloader items**.
- **26 installed original license files** gathered locally into `NOTICE_REVIEW_DRAFT.md` and checked against P0-D SHA256 evidence; 0 missing/undecodable on this runner. Draft is explicitly `NOT FOR DISTRIBUTION`. No EXE/customer code/source, bundled manifests or draft license files were uploaded.
- The remaining 92 unresolved names and every binary owner/version/license proof remain manual-review tasks. No claim that 26 license originals are the required 26 notices or included in the EXE. `CUSTOMER_RELEASE_ALLOWED=False`, `LEGAL_NOTICE_REVIEW=REQUIRED`.
