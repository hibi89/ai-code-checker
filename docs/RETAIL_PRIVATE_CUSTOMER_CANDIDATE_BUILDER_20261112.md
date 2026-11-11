# P3-01 — Owner-only private customer candidate ZIP builder (2026-11-12 KST)

## Purpose and architecture

The confirmed product is a customer-operated Windows 10/11 offline code checker. Its frozen EXE multi-input smoke and read-only candidate ZIP validator already exist on `main`; a **safe private ZIP construction path** was missing. This is an owner-side **candidate** tool, not a signed installer, legal approval or distribution command.

Two approaches:
- A: auto-compose LICENSE/NOTICE from package names, assume public license links cover exact binaries, ZIP and publish. Fast but fabricates redistribution evidence and risks unsupported legal claims; **rejected**.
- B: require the owner to supply **actual local README, main LICENSE, NOTICE and at least one separate original component license text** and an explicitly new output ZIP path. Recheck EXE SHA and original source bytes; construct deterministic allowed paths, checksums and then call the existing independent `inspect_candidate`. No Internet, EXE execution, customer source, or automatic release. **Chosen.**

The code does not certify the supplied text's authenticity/completeness or that the 71 frozen archive items have been legally attributed. Tests use synthetic non-legal text and inert bytes only. An empty or false NOTICE still leads to **RELEASE BLOCKED**.

## Optional owner workflow (no customer delivery permission)

Prepare the real owner-controlled local inputs **outside cloud-sync paths**. Never add private original files or candidate ZIP to the public repo.

```powershell
python -m scripts.build_private_customer_candidate `
  --exe "C:\Private\CodeCheckerOffline.exe" `
  --readme "C:\Private\README.txt" `
  --license "C:\Private\LICENSE" `
  --notice "C:\Private\NOTICE.txt" `
  --component-license "Example.terms=C:\Private\verified-original-license.terms" `
  --out "C:\Private\candidate-FRESH.zip"
```

The `--component-license` option can be repeated, with an exact safe target name. It **must not** be replaced with a guessed/generated text; the example name/text is documentation only and no original license is supplied in GitHub. The command requires all source paths and destination to be absolute. The destination must not exist and the parent directory must be local. The builder checks source symlink/hardlink, non-UTF8/NUL text, duplicate/colliding entries, SHA mismatch, source changes, ZIP traversal and existing-output overwrite. ZIP writes are streaming and fail closed. A build failure removes only its newly created candidate ZIP, not any input.

The generated ZIP layout matches the existing `verify_customer_zip_candidate.py` contract: `CodeCheckerOffline.exe`, `README.txt`, `LICENSE`, `NOTICE.txt`, explicit `LICENSES/<name>`, and `SHA256SUMS.txt` listing all other entries. The independent verifier runs after packaging on the **physical original EXE**; only structurally valid, SHA-matching, still-blocked candidates are kept.

Output indicates `PRIVATE_CANDIDATE_CREATED_RELEASE_BLOCKED` and exact EXE/ZIP SHA256. It does not print local paths, source text or customer data. Creating a candidate is **not sending or selling the product**.

## Test and release gates

- Scoped local Python 3.13 Linux `python -m unittest discover -s tests -p test_private_candidate_builder.py -v`: **12 PASS / 0 FAIL / 0 SKIP** after correcting a shared-file-descriptor offset bug. Unit test scaffolding for already existing `input_safety.py` and `inspect_candidate` was synthetic **local-only shim**, not the full source. New source and tests were transferred with exact Git Blob parity.
- **Full repository `python -m unittest discover -s tests -v` and original ZIP/EXE validator integration, Windows PyInstaller, real EXE, customer device, SmartScreen/Defender/network/PDF, exact Tcl/Tk legal rights and all 71 archive items are NOT VERIFIED by the local batch.** Run normal GitHub PR tests and Windows candidates at the new code SHA to validate integration.
- No original GitHub main, license, customer files, tokens, environment settings or public release changed by this feature.
- **Current engineering completion 78% retained** until same-SHA integration and real product scope check. 85% target is *not* reached from 12 synthetic tests. `customer_release_ready=false` on every valid output.

Next safe unit: exact-EXE match between a generated private ZIP and *already collected* Windows acceptance/smoke evidence, with existing validators reused, plus full cross-platform regression and an ordinary buyer Windows10/11 owner signoff. Rights/notice/legal review and release approval remain separate.
