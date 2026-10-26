# P1-F: JS / TS / TSX Tree-sitter syntax candidate research prototype

Date: 2026-10-26 KST. Baseline main 65a30e968cd6a329124cd696720ebe156ef7ae6f, prior Tests 16/16 PASS.

## Choice, cost and implementation

- Alternative A: immediately add native parser grammars to customer EXE and mark JS/TS analyzed. Rejected: source/license/NOTICE review, Windows binary size, real-world security precision and end-user test not verified.
- Alternative B (chosen): isolated opt-in grammar-based syntax-candidate prototype under scripts/, with no changes to offline_core, offline_report, main customer app or requirements-offline-build. Zero mandatory paid AI / model service; native binary wheels installed only in disposable research CI.
- scripts/prototype_js_ts_adapter.py handles JS, TS and TSX using pinned Tree-sitter research packages, imports native parser only inside call; returns syntax_checked/syntax_failed/blocked and a typed candidate tuple, not scanned-user code. Max input 512 KiB, max 25,000 AST nodes. Missing optional grammar has explicit UnsupportedParser. Never executes JS/TS, customers' script builds or untrusted plugins.
- Two observed syntax-only patterns: direct identifier eval(...) and direct new Function(...). Member expressions, strings and comments are intentionally excluded. The adapter cannot establish runtime binding, actual danger, source input, exploitability or completeness; builtins may be shadowed, dataflow/interprocedural cases missed. No vulnerability certification.

## Actual observed evidence

- Source CI SHA 6897da20193e936a3aed663fa8968a6a217727a4, PR #16 https://github.com/hibi89/ai-code-checker/pull/16.
- Parser research run https://github.com/hibi89/ai-code-checker/actions/runs/40343388339: Windows-2025 1/1 and Ubuntu-24.04 1/1 PASS, 17 deliberately constructed JS/TS/TSX synthetic cases, 8 TP / 0 FP / 0 FN by (candidate ID, source line). This is ONLY synthetic pattern matching, NOT real-world security rule precision or recall.
- Stdlib-only contract tests in tests/test_js_ts_adapter_contract.py run under default CI without extra native dependencies. Existing test and performance/Windows EXE packaging result to be checked on final PR SHA before merging; initial research CI 2/2 is proven.
- GitHub workflow .github/workflows/js-ts-parser-feasibility.yml includes research evaluator after pinned wheel install, does not publish or bundle any parser binary.

## Remaining commercial gates

- JS/TS production scan remains limited and the candidate experiment does NOT modify the customer scanner, GUI, EXE or PDF output.
- Third-party original LICENSE/NOTICE redistribution, cumulative dependency review, new EXE size and PyInstaller hidden import compatibility, legitimate large/hostile input, independent real-world labeled accuracy, physical user Windows Defender/SmartScreen, OS packet capture and Korean PDF visual inspection are unverified.
- No sale or binary release approval. No customer code uploaded, no recurring model API cost, no Vercel.

## Next work unit

After feature + standard and research CI prove green, merge normally and verify main; then prepare local Windows opt-in prototype package/NOTICE/size assessment before switching any customer JS/TS coverage from limited to analyzed. Do not falsely claim that grammar feasibility is feature integration.