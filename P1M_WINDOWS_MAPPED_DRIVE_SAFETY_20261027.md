# P1-M Windows mapped output drive rejection — 2026-10-27 KST

## Verification / source
- [PR #24](https://github.com/hibi89/ai-code-checker/pull/24) source **MERGED** into `main` as `72c89d36828267ffb44edb1d9dd1ee47e65dc5b2`, feature `1eba94597ed6074d10db7feec41bf81f54fe55a4`. Base main `d73b2f71eabce091de22dc6f4f42f324f23dc6a6`. Revert PR #24 for recovery; no force push.
- [General Tests CI 40499792387](https://github.com/hibi89/ai-code-checker/actions/runs/40499792387): **16/16 SUCCESS**, Windows Python 3.11 logged **190 tests** and both mocked remote-drive refusal and real `GetDriveTypeW` local-drive cases PASS.
- [Windows packaged EXE/Tk/PDF/readonly integrity/provenance CI 40499792348](https://github.com/hibi89/ai-code-checker/actions/runs/40499792348): **1/1 SUCCESS**. It is a hosted synthetic runner, not a customer retail system acceptance.

## Gap and design decision
- Earlier P1-J blocked UNC-style destination paths and symlink/junction/reparse components, but **Windows mapped network shares via drive letters** are not recognizable from string/UNC tests alone. Reports written to an OS-mapped share could cause network traffic without any Python socket call.
- Option A keep UNC-only string rejection: zero new code, incomplete privacy guarantee, REJECTED.
- Option B use Windows API `GetDriveTypeW` *before* any `lstat`/`resolve` of the destination; allow 2/removable, 3/fixed, 6/RAM; refuse 4/remote and unknown/no-root/optical types 0/1/5, as well as query failure. SELECTED. Uses only Python standard-library ctypes; no new dependency or changes to system settings.
- `output_safety.py` has an OS-conditional drive-type probe used by existing `validate_output_location`. On Linux, it preserves original behavior. Path containment, paired report no-clobber writer and source read-only guarantees unchanged.
- `desktop_ui.py` visibly cautions that cloud-synchronized local folders such as OneDrive remain **not reliably detected**.
- `tests/test_output_safety.py` adds mocked remote/unknown/error/local drive-type cases and a Windows-only real `GetDriveTypeW` acceptance test.

## Limits and release gates
- **NOT a packet capture or proof of zero network traffic.** Windows drive-type classification can miss cloud-synchronized local folders and does not establish safety against hostile filesystem TOCTOU races. Inputs originating from a remote drive are not newly restricted; this improvement applies to output storage locations only.
- No real retail Windows user GUI/Defender malicious-file scan/SmartScreen/OS-level packet observation/Korean PDF visual proof, original frozen third-party legal NOTICE clearance, signed EXE distribution or owner release approval.
- No customer source upload, paid API, license/visibility/permission change or commercial release. CI synthetic success and mapped-drive blocking must not be described as a full security or privacy certification.
- Subsequent docs commits advance `main`; verify its latest SHA and any post-doc Actions separately.
