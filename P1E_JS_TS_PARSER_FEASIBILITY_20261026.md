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
