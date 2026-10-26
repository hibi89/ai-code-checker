# Phase2 P1-D2: import shadowing and reproducible rule coverage

Baseline: main c5df010b7b52643cab214989f50f2948795cb6cd (16/16 standard CI PASS). Date: 2026-10-26 KST.

## Alternative designs / decision

- Whole-file import-name denylist after any reassignment: trivial CPU/time cost, but loses legitimate true positives before subsequent reassignments.
- Chosen: AST-only direct-module import chronology plus conservative lexical local-shadow checks; no new dependencies, no execution or extra network/model cost. A source-line earlier binding is required to attribute module calls to imported subprocess, pickle or requests; Python built-in eval/exec detection also respects local and module shadowing.

## Implementation and boundaries

- static_checks.py contains _ImportResolver. Direct module imports establish candidate module/function identities; other imports, assignments and deletions invalidate them at the call position. Conditional and nested-scope ambiguities conservatively suppress unsafe identity assumptions. Scope-local parameters, rebinding in functions/classes, comprehension variables and imported alias overwrites are covered.
- Uncertain control-flow and runtime alias mutation are NOT analyzed. Some real issues will be missed; no function interprocedural call ordering, dynamic imports, JS/TS language parser or customer exploit confirmation. Source evidence and local reports are unchanged.
- scripts/evaluate_rule_accuracy.py adds 20 fixed hand-labeled positive and negative examples to the prior 28 Python cases. Two JS/TS limited-only status checks remain outside precision/recall calculations. tests/test_rule_accuracy.py adds 3 explicit regression methods.

## Observed preliminary evidence

- Source feature commit e86c2ac0c7ad1c793b54fece1d3d8b5b79c0691a. First verified ubuntu-24.04/3.11 job in Actions 40336616723 ran 135 tests PASS.
- Fixed Python cases: 48, TP=17, FP=0, FN=3. Artificial rule+line precision=17/17=100%; recall=17/20=85%. Never claim these ratios apply to other projects or any real-world vulnerability corpus. Earlier corpus baseline: 28 cases, TP13/FP0/FN3.
- Final full standard 16-job CI, packaged Windows smoke and performance/SBOM workflow outcomes must be verified on the exact final PR SHA; add only confirmed runs below.

## Release protection

No raw customer code or EXE is committed/uploaded; no paid AI API, external source execution, user data transfer or Vercel deployment. No commercial release. Original third-party NOTICE review, actual clean Windows GUI/Defender/SmartScreen/packet capture/Korean PDF visual review are UNVERIFIED. User approval required for any release or spend.

## Verified feature CI and final merge (2026-10-26 KST)
- Final feature head ef5038f25f98514c931f7bd524b669ce1d4721cf, PR #14 merged into main 545b751871b377cf52f245abb8efc6e602bd2682.
- Tests run 40336933987 16/16 jobs PASS, 135/135 unittests PASS, Windows EXE synthetic run 40336934413 PASS, performance/SBOM run 40336933977 3/3 PASS. Captured Python 48 fixed fixture cases TP17 FP0 FN3, only synthetic precision100%, recall85%. 2 JS/TS status probes excluded.
- Real-world accuracy and all commercial legal/privacy and genuine customer Windows gates still NOT VERIFIED. This documentation commit needs independently confirmed main SHA/CI; do not mistake packaging CI for human acceptance.