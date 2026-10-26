# Phase2 P1-D — Fixed synthetic rule-accuracy gate

Date: 2026-10-26 KST. Source baseline main \`0129395f9ad896f8d947db73d5bca8d59eb0f138\`, [CI 16/16 PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40331876779). This is a **local synthetic benchmark only**. Its percentages never represent real customer-code precision or vulnerability detection completeness.

## Scope and alternatives

| Option | Cost/performance | Maintenance/accuracy |
|---|---|---|
| Add broad external parser / linter immediately | No AI fee but new redistribution/dependency and untrusted config risks, heavier Windows build | Real JS/TS accuracy needs parser plus licensing review; not yet verified |
| **Improve narrow Python AST rules + fixed labeled corpus, no deps** | CPU-only offline, no APIs or new build dependencies | Observable rule-level TP/FP/FN; Python-only and known missing dataflow remain explicit |

Selected the second path as the already approved P1-D incremental approach. Protect baseline CLI and report format, preserve no-code-execution and zero required AI API behavior.

## Changes under test

- Python shell detection only on module-level imported \`subprocess\` or named \`from subprocess import\` functions, supporting aliases. Arbitrary \`.run()\`/\`.call()\` no longer incorrectly implies a shell subprocess.
- Python \`pickle\` aliases and \`from pickle import loads\` imports recognized. Unrelated \`.loads()\` excluded.
- \`verify=False\` in Python is AST checked on directly imported \`requests\` HTTP calls; Python string/comment and unrelated keyword/variable no longer flag as TLS disabled. Non-Python generic pattern remains **generic-only** and may misfire.
- SQL concatenation candidates require a visible leading SQL verb; unknown dynamic query/dataflow still not verified.
- Fixed synthetic independent *asserted labels*: Python examples with expected rule ID + source line, explicit positives, negatives, and three known rule misses. JS/TS run only as \`limited\`/partial coverage checks; deliberately excluded from Python precision denominator.
- GitHub Tests CI runs \`python -m scripts.evaluate_rule_accuracy\` across the 16 Python/OS matrix jobs. Script outputs labels and counts only, no customer code/artifacts.

## Interpretation and product boundary

For this artificial corpus, TP/FP/FN counts are per (rule ID, line) and label, not total vulnerabilities. The labels are crafted for these narrow rules, small and not an independent sample. Known misses include dynamic builtins, dynamic subprocess import, and cross-line SQL dataflow. No claim of \`0 real-world FP\`, certified security, mature JS/TS support, high recall, runtime tests, or customer release is allowed.

Actual numeric counts / final CI / SHA must be filled in after execution. All original Windows/Defender/SmartScreen/OS packet, PDF visual, and third-party NOTICE obligations remain outstanding.

## Verified CI and corpus measurement (2026-10-26 KST)

- Feature pre-handoff SHA `a4e25b8f9992f9a6e4f703f32e2b25b4a372b82b`, [PR #13](https://github.com/hibi89/ai-code-checker/pull/13): [standard Tests run 40333097683](https://github.com/hibi89/ai-code-checker/actions/runs/40333097683) **16/16 PASS, 132 unit tests PASS**, [Windows EXE smoke run 40333096415](https://github.com/hibi89/ai-code-checker/actions/runs/40333096415) PASS, and [performance/inventory run 40333096368](https://github.com/hibi89/ai-code-checker/actions/runs/40333096368) **3/3 PASS**. The following documentation commit changes SHA; verify final checks before merging.
- Actual fixed synthetic Python set **28 cases**, deliberately limited JS/TS **2** additional (excluded). Per-rule/line **TP 13, FP 0, FN 3**. Derived fixed-fixture **precision 13/(13+0) = 100%**, **recall 13/(13+3) = 81.25%**. These are deterministic test-case results only, *not independent real-world/security-validity metrics*.
- Explicit known FNs: dynamic `getattr` builtins `eval`; indirect `__import__("subprocess")`; cross-line SQL query assembled into a variable. Import alias parsing is limited to module-level imports; JS/TS have no dedicated parser. The scanner does not establish actual exploitability, and its lack of a finding does not certify safety.
- Next improvements: broaden a representative labeled corpus independent of the new rule implementation, add safe JS/TS parser only after dependency/licensing/Windows size evaluation, and finish independent customer Windows GUI/Defender/SmartScreen/network/PDF visuals. Zero mandatory AI API maintained; no EXE/customer data uploaded, no commercial release approved.
