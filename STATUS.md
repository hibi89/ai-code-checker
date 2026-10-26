# CODE CHECKER — STATUS

Updated: 2026-10-26 KST. State: MVP Day 1 offline core implemented and CI tested; NOT a customer-ready product.
Repo: https://github.com/hibi89/ai-code-checker (public, MIT).
Main base used for feature: `4c1c10069c3ac20a3342648e3877f1aa1b5fca5f`.
Work branch: `feature/offline-core`; test evidence commit `6aea33852d40e296d44980a37cb9c9de0c994f9a`; final documentation commit must be checked from GitHub (no self-referential SHA).
Original pre-v2 baseline: `8c72a6f3bc30f2a720c10f3a5a9dd366f0d059ab`.

## Product direction (owner approved)
3-focused-day MVP -> gap comparison against [FINAL_PRODUCT_BLUEPRINT.md](FINAL_PRODUCT_BLUEPRINT.md) -> comprehensive stability/security/performance/privacy hardening -> reviewed Kmong release.
Primary sale: customer-operated offline Windows code risk checker with no mandatory AI API/account/server/subscription fees. Separate human report service. No 500-line commercial restriction in future software; do not claim unlimited file size or full security review.

## Confirmed implementation — Day 1
- New `offline_core.py` scans using existing `code_input.py` ZIP/folder/paste safe loaders, masked sources and existing Python static checks WITHOUT Gemini.
- Single TXT with user-selected language maps to virtual extension, preserving original TXT file/line references. Unknown language is generic-only, marked `limited`.
- Strict multi-file TXT headers `===== FILE: path.ext =====` split to individual logical files; guards duplicate case/Unicode paths, traversal, malformed headers, unsupported and sensitive sections; retains provenance.
- Explicit `FileCoverage` with `analyzed`, `limited`, `failed`, `excluded`, `unsupported`, plus aggregate `complete` or `partial`. Unsafe input raises local InputError; CLI returns blocked state. Status describes rule coverage, not code safety.
- Developer preview `python offline_core.py path.zip` (metadata-only JSON) or `python offline_core.py file.txt --language python`.
- Unit test file `tests/test_offline_core.py` contains synthetic tests for 1,200-line TXT, 12-file ZIP, 200-file/12,000-line folder, malformed headers, escaped marker, origin/source lines, duplicate paths, unsafe ZIP and no source execution.
- Existing `main.py` Gemini CLI and all historical v1 code remain unchanged; no API call, paid provider, real customer code or deployment used.

## Verification and known failure
- First feature CI `118ff8d`: FAILED with 1 incorrect *test fixture* that put a raw header-like line into Python source outside a string. 61 of 62 tests passed and the bad expectation was corrected to use valid Python triple-quoted code (no production logic changed).
- Next feature CI for `6aea338`: **GitHub Actions 16/16 jobs completed success** (15 OS/Python combinations + dependency audit), with 62 tests in Linux run. Historical v1 had 46 tests. An additional local TXT file-path fixture has since been added in this docs update; final head CI must still be verified independently.
- No local-container checkout available because git clone DNS resolution failed in this session; testing used GitHub Actions logs. Clean Windows EXE, customer UI, full offline network telemetry, accuracy benchmarking beyond small fixtures and PDF are NOT VERIFIED/IMPLEMENTED.

## Remaining milestones
| Stage | Status |
|---|---|
| Day 1 input/manifest/basic local rule runner | IMPLEMENTED; final commit CI pending |
| Day 2 normalize findings + local Korean HTML/Markdown report | NOT STARTED |
| Day 3 minimal Windows UI and portable candidate | NOT STARTED |
| Phase 2 blueprint gap filling / JS-TS | NOT STARTED |
| Phase 3 security/privacy/load/human acceptance | NOT STARTED |
| Phase 4 Kmong release | NOT STARTED |

## Next exact step / recovery
1. Verify latest feature commit and its Actions 16 jobs, create PR to `main` if no code conflict; merge only with CI green. Check main SHA after merge.
2. Read current [HANDOFF.md](HANDOFF.md), [AGENTS.md](AGENTS.md), blueprint and actual `offline_core.py`. On next `ㄱ`, start Day 2 on fresh `feature/offline-report-ui` after verifying main.
3. Preserve original source and secrets, no force pushes. Avoid repeat Gemini connection attempts. No Vercel/Production URL applies to offline product.
