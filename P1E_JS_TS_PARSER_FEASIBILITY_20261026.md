# Phase2 P1-E — local JavaScript / TypeScript parser feasibility

Date: 2026-10-26 KST. Baseline main `bd4e7041a813fc599aa7cf51ae6d68158c64466c`, regular CI [16/16 successful](https://github.com/hibi89/ai-code-checker/actions/runs/40337436335).

## Decision and alternatives

| Option | Cost and packaging | Quality and trust |
|---|---|---|
| Own JavaScript/TypeScript text regex | No extra binary or charge | Misreads comments, strings, JSX and TS type syntax; not equivalent to parsing; avoid expanding marketing claims |
| Node TypeScript compiler `typescript` | No inference API fee; requires Node runtime or considerable bundled JS | Strong TS syntax semantics, but larger deployment/Node execution trust boundary and new package notices |
| **Python Tree-sitter native parser with JS/TS grammars** | Free local parse; **three native wheels** and binary size/licensing obligations if ever shipped | Structured syntax, no JS execution; not a vulnerability or dataflow engine |

Research selection: third option, **CI-only feasibility test**, not included in distributable `requirements-offline-build.txt`. The existing offline product remains Python-only AST with JS/TS `limited` status.

Official public metadata (not a lawyer clearance):
- Python `tree-sitter==0.26.0`, MIT, binary wheels: https://pypi.org/project/tree-sitter/
- `tree-sitter-javascript==0.25.0`, MIT, JS/JSX grammar: https://pypi.org/project/tree-sitter-javascript/
- `tree-sitter-typescript==0.23.2`, MIT, TS/TSX grammar: https://pypi.org/project/tree-sitter-typescript/

## Implemented

- `requirements-parser-probe.txt` pins CI-only versions; `--only-binary=:all:` avoids local source builds and grammar-generator scripts in CI.
- `scripts/probe_js_ts_parser.py` checks module metadata/version, builds JS, TS and TSX grammars as data parsers, and parses **12 hand-authored fixtures**, including malformed syntax, JSX/TSX and Korean UTF-8 offset. It fails closed on unexpected parse results. No code execution, source upload, model API or EXE change.
- `tests/test_js_ts_parser_probe.py` verifies test contract with pure mocks; default unit test suite needs no parser installed.
- Separate two-OS CI workflow `.github/workflows/js-ts-parser-feasibility.yml` tests Ubuntu and Windows Python 3.13 wheels independently. Does not upload parser wheels or executable assets.

## Acceptance and remaining gate

Only after observing live Ubuntu + Windows CI, report exact outcomes. If the wheels and grammar pass, parser *feasibility* is validated—not JS/TS analyzer integration, vulnerability accuracy, legal NOTICE adequacy, customer EXE functionality or release. Full third-party original LICENSE text/NOTICE chain, binary size increase, PyInstaller hidden-import inclusion, malformed/hostile-corpus bounds and offline privacy remain prerequisites for shipment. No commercialization approved.

### CI evidence

Pending exact GitHub final branch SHA/workflow results.

## Actual two-OS CI confirmation — 2026-10-26 KST

- Parser probe code SHA `4e4cd29bd511a7811098251fedceaaec16004db5`; [GitHub Actions 40341166881](https://github.com/hibi89/ai-code-checker/actions/runs/40341166881) **Windows 2025 and Ubuntu 24.04: 2/2 SUCCESS**. Each job installed the three exact-version prebuilt binary wheels, parsed 12 synthetic samples (**9 accepted, 3 malformed rejected**), and passed three scoped unit tests. Explicit tested grammars: JS, TS, TSX, including UTF-8 non-ASCII and JSX examples.
- The installed package metadata of `tree-sitter==0.26.0` advertised MIT via Python package classifier; JavaScript `0.25.0` and TypeScript `0.23.2` advertised MIT via license field. Each installed distribution had **one license-named path**. The original contents and downstream redistribution NOTICE text were **not reviewed or approved**; license metadata is only preliminary evidence. Original source rights and commercial status unchanged.
- Initial CI failure [40340542447](https://github.com/hibi89/ai-code-checker/actions/runs/40340542447) was a YAML scalar quoting issue in `--only-binary=:all:`; corrected. Next failure was an overly narrow license metadata equality test, not wheel/grammar incompatibility; updated recognition of license field/classifier and verified both OS. Do not remove these error histories.
- **Decision:** standalone grammar feasibility established, **DO NOT yet bundle** the parser into the product Windows EXE until dependency licenses/notices, static linking/packaging, incremental EXE size, plugin trust and security-rule accuracy have independent approval. Actual existing JS/TS coverage remains `limited`. Do not represent syntax parsing as security detection. Follow-on decision: small optional feature integration prototype with explicit fail-closed unsupported status, no customer product release.
- The latest handoff-document commit changes feature SHA; re-verify CI before merge. Physical consumer Windows, Defender/SmartScreen/OS network, Korean PDF visuals and original CPython/Tcl/Tk/VC/PyInstaller legal notice chains remain UNVERIFIED.

## Actual complete feature merge — 2026-10-26 KST

Final feature SHA `fdae1c6463da606e0377a277992081c12a4d9173` passed [regular Tests 16/16](https://github.com/hibi89/ai-code-checker/actions/runs/40341532660) and [Windows+Ubuntu parser research 2/2](https://github.com/hibi89/ai-code-checker/actions/runs/40341532563). P1-E [PR #15](https://github.com/hibi89/ai-code-checker/pull/15) merged at main `33d20ee5ffc94e72ee4f81d6b6c76ea5a60b46b9`. Syntax-only 9 valid/3 malformed fixed probes; no third-party parser bundled into current EXE, JS/TS `limited` and release/NOTICE still blocked. Check final docs/main CI separately.
