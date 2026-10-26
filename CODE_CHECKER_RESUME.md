# CODE CHECKER — 즉시 재개

**트리거:** `[코드체커 깃헙 확인해]` 또는 `ㄱ`.

1. GitHub `hibi89/ai-code-checker`의 최신 `main` SHA/PR/feature branch/Actions 확인.
2. `HANDOFF.md` → `STATUS.md` → `AGENTS.md` → `REQUIREMENTS.md` → `FINAL_PRODUCT_BLUEPRINT.md` → `MVP_3DAY_ROADMAP.md` → `BLUEPRINT_GAP_MATRIX_20261026.md` → 실제 코드/테스트 순으로 확인.
3. **Days 1–3 MVP source merged** through PR #2/#3/#4. Verified last Day3 main SHA `f0c257058f43298167e6777f315db01ae294fd86` and CI [16/16 PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40309370848). This does not verify GUI clicks, packet traffic, customer machine or PDF printing.
4. Current Phase2 `feature/blueprint-gap-phase2`: 25-row gap matrix plus priority P0-A truthful skipped directory metadata/partial states across `offline_coverage.py`, `offline_core.py`, `desktop_core.py`, `offline_report.py`; synthetic tests `tests/test_pruned_coverage.py`. **Re-fetch actual head/CI and PR, not guaranteed merged.** If green and mergeable, merge non-force; verify new main CI; next P0-B Windows real UI/privacy/printing QA and P0-C benchmarks/licenses.
5. Approved process: working 3-day MVP → final blueprint gap fill → broad security/stability/performance/privacy/licensing hardening → clean device acceptance → explicit owner approval for Kmong sale. Product 0-required-API local scanning; v1 Gemini kept separate.
6. No external model calls/customer source transfer, paid spending, new private repo, change in GitHub visibility/permissions, proprietary sales code posted to public MIT, release or commercial listing without approval. Do not execute scanned code; never infer production success from GitHub CI.
7. Important developer commands: `python -m unittest discover -s tests -v`, `python desktop_ui.py --self-test`, `python desktop_ui.py` only on a system with Tk display. No Vercel/Production URL; local Windows desktop product.
