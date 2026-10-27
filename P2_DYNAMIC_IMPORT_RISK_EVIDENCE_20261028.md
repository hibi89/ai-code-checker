# P2-2 — literal dynamic-import risk regression evidence (2026-10-28 KST)

- 2026-10-28 P2-2 scanner capability merged: PR #36 https://github.com/hibi89/ai-code-checker/pull/36 into main source SHA 967ddbc2f42662da9c1f0f2136e2b5be00bb7314, exact tested feature SHA 0986772e59caf410c76076018d3054cead2af80d.
- Implementation files static_checks.py, tests/test_rule_accuracy.py, scripts/evaluate_rule_accuracy.py: AST-only recognition of unshadowed builtin literal __import__('builtins').eval/exec and __import__('subprocess').run/Popen/etc shell truthy, also unshadowed builtin getattr of a known literal module and literal function name. Dynamic/unknown names, shadowed __import__/getattr, unrelated modules, shell=False, bare attribute access excluded.
- Verified EXACT feature SHA: Tests https://github.com/hibi89/ai-code-checker/actions/runs/40532704038 16/16 success, Windows packaged EXE/Tk/Defender smoke https://github.com/hibi89/ai-code-checker/actions/runs/40532703707 success, performance/dependency inventory https://github.com/hibi89/ai-code-checker/actions/runs/40532703963 3/3 success.
- Measured on a fixed NONREPRESENTATIVE synthetic corpus: 103 Python cases, 41 TP, 0 FP, 0 FN, 100% in-corpus recall, NOT real-world detection accuracy. Ubuntu Python 3.11: 276 unit tests passed. Legacy model path unchanged.
- Initial feature CI failed only because an obsolete test asserted two known false negatives must remain; corrected test on next SHA. Re-run full final PR head clean. Prior failed jobs never counted toward final proof.
- After merge main Tests run https://github.com/hibi89/ai-code-checker/actions/runs/40533179753 was queued when recorded. Do not infer pass before checking same SHA.
- Functional developer MVP remains ready in synthetic CI scope. Customer EXE release still BLOCKED: independent real Windows acceptance, SmartScreen/Defender reputation, OS network packet verification, primary original LICENSE/NOTICE legal signoff, real Korean PDF visual and explicit owner commercialization approval. No customer code, paid API, model key, executable artifact upload or OS settings changes.
- Next GO: verify latest main CI and fix a genuinely measurable scanner or user-workflow defect; avoid planning-only/doc churn. Advance upstream design ahead of schedule only with a regression that proves the behavior.

## Meaning and scope

The scanner does not run imported modules, inspected customer Python, subprocesses, imports or source-defined helpers. It reads AST only. A syntactically literal unshadowed import target is a risk candidate, not proof that the runtime callable has not been monkeypatched or that a vulnerability exists. Narrowly recognized patterns close two known test misses while variable names, arbitrary dynamic imports, runtime aliases, lexical shadowing and custom `getattr` deliberately remain uncertain. The 103 fixture cases were developed with the implementation and cannot be used as a claim of complete real-world security coverage.

## Next validation

On any resumed work, check exact main SHA and postmerge/last docs CI result; independently record customer-device release gates. Do not push unsigned EXE or source data into release assets.
