# Phase2 P1-G — Windows native grammar EXE and original wheel notice inventory

Date: 2026-10-26 KST. Baseline main `d4cc67eafc21edcef83b2eadc63595e7298e7010`. Feature code SHA `317777b874166e5e5e62c3678436d40a630e667c`.

## Engineering decision

Options compared: (A) directly add Tree-sitter to the real customer GUI build, which risks unreviewed NOTICEs, packaging changes and product misrepresentation; (B) use separate unsigned synthetic-only Windows frozen baseline and parser-native candidate plus installed original LICENSE text metadata, keeping shipped product untouched. **B chosen**. No paid API inference and no remote customer source upload.

## Actual observed CI

- [Parser packaging and original LICENSE CI run 40345534242](https://github.com/hibi89/ai-code-checker/actions/runs/40345534242): **3/3 jobs PASS** — Ubuntu license-text audit, Windows license-text audit, Windows two-binary PyInstaller 6.22.3 build and synthetic JS/TS/TSX execution.
- [Standard Tests run 40345533817](https://github.com/hibi89/ai-code-checker/actions/runs/40345533817): **16/16 jobs PASS**, 147 Python unittests PASS in observed Ubuntu Python 3.11 job (earlier baseline 142; 5 new).
- Windows-PyInstaller synthetic-only `P1GBaseline.exe`: **8,563,435 bytes**. Separate research-only native parser `P1GNative.exe`: **9,053,820 bytes**. **Delta +490,385 bytes** (about 0.49 decimal MB). Same synthetic test entrypoint, but native collection flags deliberately differ; this is NOT an actual CodeCheckerOffline.exe build-size delta. Windows candidate `--synthetic`: **4/4 fixed JS/TS/TSX rule observations** PASS, no network or customer code exercised. No GitHub artifacts uploaded, no EXE publication, no customer build changed.
- Original installed wheel LICENSE files were opened and hashed in each CI runner (not just package METADATA): canonical MIT permission/copyright wording tested with fixed guard. Each of 3 distribution versions provided 1 LICENSE path; contents never uploaded or committed.

## Original wheel files — locally examined metadata only

| Package, pinned version | Ubuntu LICENSE bytes / SHA256 | Windows LICENSE bytes / SHA256 |
|---|---|---|
| tree-sitter 0.26.0 | 1,088 / `1af0790543fffac99dd3bd290bf83ca963f4f8029065eb6f35638f4df863ae8e` | 1,109 / `c40a115b3d7d429c839bc51ace3464c2f37c9559bad6c6251a86281c27ea5431` |
| tree-sitter-javascript 0.25.0 | 1,080 / `2e0110e07abef7c2548b26ec9d6969775617ca539a0dc8dbeeb14d6452c711d1` | same |
| tree-sitter-typescript 0.23.2 | 1,080 / `49bf33cf78ef5897e4e161ce1517df7de1ae5042a65b6bcfd44401e0fc606559` | same |

**Important difference:** tree-sitter core wheel LICENSE has different hash/byte length between Ubuntu and Windows. A passing canonical MIT phrase check is not proof the exact notices are identical or sufficient for distribution. Keep both platform-specific originals for future human review; do not silently pick one as authoritative. The workflow prints only relative LICENSE filename, byte length and SHA256, NOT original full copyright text.

## Implementation and security boundary

- `scripts/p1g_notice_inventory.py`: local installed-wheel original license text read, exact pinned version, digest, basic MIT phrase checks; fail closed if LICENSE absent/drift/unreadable. Explicit false legal/certification/customer-release flags.
- `scripts/p1g_native_exe_entry.py`: synthetic-only CLI modes, baseline and frozen JS/TS/TSX grammar smoke; no input path or customer source parameter.
- `scripts/p1g_native_package_probe.ps1`: separate scratch `.build-p1g/`, PyInstaller pinned, baseline exclusion then candidate explicit hidden import and `--collect-all` 3 grammars. Executes both and prints size **metadata only**. No binary upload. `.build-p1g/` gitignored.
- `.github/workflows/p1g-parser-packaging.yml`: 2 OS original-wheel license check and Windows packaged native research; Windows runner no customer PC. 5 stdlib regression tests integrated with regular test matrix. The real GUI `CodeCheckerOffline.exe`, its `requirements-offline-build.txt`, core scanner/coverage, and existing third-party notice obligations are **unchanged**.
- PyInstaller official supported flags for binary/data collection: https://pyinstaller.org/en/stable/usage.html. Original Python Tree-sitter pinned project metadata: https://pypi.org/project/tree-sitter/0.26.0/.

## What remains unverified / not authorized

- Original LICENSE texts have been *programmatically read* for 3 new wheels, but human approval of correct attribution/NOTICE to end customers, copyright holders, transitive runtime licenses and actual inclusion of LICENSE text in eventual EXE has **not** happened. `license_compliance_certified`, `third_party_notice_ready_to_distribute`, `customer_release_ready` remain false.
- Existing frozen customer EXE still has independent legal obligations: CPython/Tcl/Tk/VC native resources, PyInstaller exception, Pydantic and other bundled packages, and 1 unexplained TOC name (metadata uncertainty, no proof of violation). Not resolved by these 3-wheel checks.
- Not yet tested: actual CodeCheckerOffline.exe parser inclusion/delta, opt-in GUI integration, trustworthy JS/TS source dataflow/accuracy, real end-user Windows Defender/SmartScreen/reputation, OS packet capture, complete Korean PDF visual and operator acceptance, licensing/release approval. Research baseline comparison is not a sales SKU.

## Next authorized GO

Perform fail-closed opt-in JS/TS adapter integration in source `offline_core` only when the missing wheel remains optional, ensuring partial/limited vs syntax-checked coverage is explicitly truthful, and validate on a separate Windows research EXE. Continue original full dependency-chain NOTICE and actual clean-user Windows gates. **Do not silently add Tree-sitter to customer `requirements-offline-build.txt` or distribute EXEs without approval.**