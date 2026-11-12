# P3-03 — One-command private retail candidate and original Windows receipt cross-check

**2026-11-12 KST · offline Windows Code Checker · not authorized for sale**

## Confirmed design and trade-off

This project already has a Python AST/Tk local static scanner, a PyInstaller candidate (previous Windows hosted smoke), and separate exact-EXE acceptance and license review controls. P3-01 required an owner to generate a fresh private candidate ZIP from actual, locally controlled README/LICENSE/NOTICE/component original texts. P3-02 bound that ZIP to the same EXE referenced in already-collected Windows receipt JSON. Both intentionally kept legal/customer release on HOLD.

- **A — automated license NOTICE generation, release-ready ZIP publishing:** fewer steps, but a package name/filename cannot establish binary vendor identity or actual redistribution rights; previous repo records have **71 unresolved EXE archive items**, not 71 distinct licenses. **Rejected.**
- **B — single explicitly invoked local preflight:** use existing independent validators, require original owner-controlled inputs and pre-existing exact-EXE Windows receipts, create only a **new**, private ZIP and **new** JSON metadata report, and verify the physical EXE/ZIP again. Any failure removes only newly created outputs; customer source and original license files are never modified. **Selected.**

## Commands on the owner's Windows machine (no release authorized)

Requires Python available on the owner's development PC, actual own frozen candidate EXE and two existing separately collected Windows receipts. Real original license/NOTICE files must be provided by the owner: do not use the synthetic placeholders from tests. The path is an example only.

```powershell
python -m scripts.prepare_private_retail_review `
  --exe "C:\Private\CodeCheckerOffline.exe" `
  --readme "C:\Private\README.txt" `
  --license "C:\Private\LICENSE" `
  --notice "C:\Private\NOTICE.txt" `
  --component-license "ExactVendor.terms=C:\Private\original-vendor-license.terms" `
  --readonly "C:\Private\windows-acceptance-readonly.json" `
  --smoke "C:\Private\windows-local-exe-smoke.json" `
  --runtime "C:\Private\runtime-version-receipt.json" `
  --defender "C:\Private\defender-custom-scan.json" `
  --out-zip "C:\Private\NEW-private-candidate.zip" `
  --out-report "C:\Private\NEW-private-review.json"
```

Optional `--runtime`/`--defender` must never be forged: omission remains explicit. `--component-license` is repeatable; at least one is required, but that is not proof that all actual frozen component rights are covered. Every path is explicit, absolute, local-only and distinct. Existing output paths are refused rather than overwritten. No EXE execution, code install, cloud services, automatic OS security changes or buyer data upload.

Valid outputs carry `PRIVATE_RETAIL_REVIEW_CANDIDATE_RELEASE_BLOCKED`, SHA256 of the exact EXE and private ZIP, count of entries and 8 `human_release_gates: UNVERIFIED`. Even success always has `original_license_texts_verified=false`, `vendor_redistribution_rights_verified=false`, `real_buyer_pc_test_certified=false`, `legal_notice_approved=false`, `owner_release_approval=false`, `customer_release_ready=false`. These are two **local review candidates**, not deliverables for sale or publication.

## Tested evidence (strict scope)

- Local Linux Python 3.13.5 exact P3-01, P3-02, P3-03 functional source and tests: **36 PASS / 0 FAIL / 0 SKIP** using `python -m unittest discover -s tests -p 'test_private*.py' -v`. Includes actual bounded ZIP creation, independent real local file ZIP reading+checksum match, existing independent local Windows receipt consolidation, altered binary, mismatch, rejected legal/sale flags, synthetic optional runtime/Defender receipt, source immutability, symlink destination and safe rollback. New commit source/test Git Blob SHA independently compared with local test bytes.
- For **original dependencies** reconstituted under local test harness, Git Blob checks match exact original GitHub `main`: `input_safety.py` 063a13ea, ZIP inspector e570ef3d, Windows receipt consolidator 54a2c0c0, Windows readonly validator 5cf09c7b, frozen smoke validator 69069b23, Defender validator f35a1c7e, runtime receipt 8e9faeb9, and upstream tagged-license helper 94edcd89. On Linux the unrelated `code_input.InputError` and `output_safety` Windows drive helper were **minimal test substitutes**, so this is **not a full repository checkout or Windows native acceptance**.
- Original full `python -m unittest discover -s tests -v`, actual GitHub PR head check, PyInstaller Windows test, real unsigned packaged EXE GUI/Defender/SmartScreen/OS packet inspection, Korean PDF visual, final customer support, and legal verification of actual embedded component LICENSE/NOTICE are **NOT VERIFIED by these Linux tests**. GitHub PR #82 tests were `queued` at initial observation; confirm current status at exact SHA.

## Internal 85% milestone rationale and limitations

This is an explicitly **provisional engineering scope estimate**, not an externally measured percentage or sales readiness. From prior Code Checker **78%**, new separately testable deliverables: **+2 percentage points** owner-only bounded ZIP creator; **+2** physical ZIP-to-EXE and Windows receipt coupling; **+2** one-command private preflight+cleanup; **+1** original-source-pinned 36-case regression/integration evidence = **85% provisional**. The final **15% and all commercial release gates remain** for independent customer Windows10/11 acceptance, exact Tcl/Tk/dll/71 archive original legal notice mapping, real customer delivery QA, and owner explicit sale approval. Full CI pending must not be portrayed as a pass. Do not release, send candidate ZIP or claim legal compliance based on this milestone.

## Recovery

Existing `main` remains unchanged. Work is isolated to `feature/retail-private-candidate-20261112` and draft PR #82; revert by resetting the feature branch to its previous committed parent (no force push without approval). Never include private actual original licenses/EXE/customer files in the public repository. Report exact GitHub feature SHA, main SHA, CI status and hub synchronization separately.
