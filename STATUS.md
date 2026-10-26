# CODE CHECKER — STATUS (2026-10-26 KST)

Repository: https://github.com/hibi89/ai-code-checker (Public/MIT). Production/Vercel: NOT APPLICABLE (offline Windows desktop app).

## Live merged source baseline
- Day1 PR #2: safe ingest/Python AST; Day2 PR #3: Korean HTML/Markdown offline report; Day3 PR #4: Tk desktop GUI + unsigned packaged EXE candidate.
- Verified Day3 main **merge SHA `f0c257058f43298167e6777f315db01ae294fd86`** with [post-merge Actions 16/16 PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40309370848).
- Windows PR #4 smoke: EXE built and synthetic scan/report PASS. Python CI baseline: 85 unit tests. **Actual GUI clicking/clean customer Windows, Defender/SmartScreen, printing, packet-capture privacy tests remain UNVERIFIED.** No customer-ready release.
- Prior code + v1 Gemini flow preserved. Offline local scan does not require AI API keys, a server, online account, subscription, customer code execution or external source transfer by design. Real network observation is pending.

## Current Phase2 work — not yet main
- Branch: `feature/blueprint-gap-phase2` based on main `f0c2570`. Feature work is not counted as main delivery before PR merge.
- [BLUEPRINT_GAP_MATRIX_20261026.md](BLUEPRINT_GAP_MATRIX_20261026.md): 25 evidence-based blueprint checks, priorities and acceptance.
- P0-A truthfulness fix: `offline_coverage.py` inventories names of policy-skipped subtrees without reading children or following symlinks. `offline_core.py` reports them separately, makes folder scans partial when any subtree is pruned, and states **child file counts UNKNOWN** rather than inventing exact discovered counts. `desktop_core.py`, `offline_report.py` surface that distinction. Existing legacy `code_input.py` unchanged.
- `tests/test_pruned_coverage.py` covers nested ignored subtrees, clean directories, depth limits and bounded walk refusal. GitHub CI for the feature head must be checked before completion.
- No new third-party runtime dependency, no provider/API calls, no customer data, no EXE artifact upload.

## Work board

| Phase | Verified status |
|---|---|
| MVP Day1 ingest | MERGED / CI PASS |
| MVP Day2 report | MERGED / CI PASS |
| MVP Day3 GUI code + EXE synthetic smoke | MERGED / CI PASS; real Windows interaction UNVERIFIED |
| Phase2 blueprint gap matrix | CREATED on feature branch; PR/main integration pending |
| Phase2 P0-A scan coverage truth | FEATURE CODE IMPLEMENTED; CI/PR integration pending |
| Phase2 P0-B clean Windows GUI/privacy/PDF | PENDING |
| Phase2 P0-C benchmarking, dependency licenses | PENDING |
| Phase2 P1 Python/JS/TS depth and report UX | PENDING |
| Phase3 final stability/privacy/security/accuracy | PENDING |
| Phase4 Kmong approval and sale | PENDING |

## Recovery and next run

- Stable recovery point: `main` f0c2570 (PR #4 merged + CI PASS). Never force push, remove historical Gemini source or expose customer data.
- Next **ㄱ** or **[코드체커 깃헙 확인해]**: check branch current SHA/open PR/CI; if Phase2 P0-A passes, merge PR non-force; verify main post-merge CI; then proceed to Windows E2E and measurable coverage/benchmark. Any unrun GUI, packet, PDF, antivirus checks must stay UNVERIFIED.
- Follow `HANDOFF.md`, `AGENTS.md`, `REQUIREMENTS.md`, final blueprint, and GAP matrix. Update handoff after relevant merge.
