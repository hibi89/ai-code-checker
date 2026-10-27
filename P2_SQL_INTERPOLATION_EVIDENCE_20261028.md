# P2 scanner SQL dynamic Python interpolation — checked 2026-10-28 KST

## Problem and decision

Python f-strings and + SQL strings were recognized, but equivalent string percent / format syntax escaped narrow offline checks. Chosen AST-only literal prefix plus structural interpolation inspection, avoiding new Python dependencies, unsafe source evaluation, unknown ownership guesses, or GUI feature churn.

## What changed

- For visible leading SQL strings, percent-format operators are recognized only with actual formatting slots and non-constant arguments.
- Python str.format and str.format_map recognize actual format fields, not escaped double curly braces; structurally constant arguments are excluded.
- Direct cursor.execute and prior ordered same-scope query assignment analysis are both recognized.
- Source-line evidence still checked against masked source, risk label is PY-SQL-CONCAT candidate rather than proven vulnerability.
- 15 labeled cases added to fixed corpus plus scenario tests for dynamic and safe negatives; do not treat fixture labels as real-world prevalence.

## Observed GitHub source and CI

- PR #35 https://github.com/hibi89/ai-code-checker/pull/35 MERGED main source 2a1538a7f46dd3214ee054cdca4f0220dcdd8931, tested feature 88186ad59c10961be31c4b38d9b9feb9b4dd3d14.
- Feature Tests https://github.com/hibi89/ai-code-checker/actions/runs/40530106925 16/16 SUCCESS (Ubuntu Python 3.11: 274 unittests); Windows packaged candidate https://github.com/hibi89/ai-code-checker/actions/runs/40530107096 SUCCESS; synthetic performance/license inventory https://github.com/hibi89/ai-code-checker/actions/runs/40530106879 3/3 SUCCESS.
- Actual post-merge main Tests https://github.com/hibi89/ai-code-checker/actions/runs/40531103716 SUCCESS.
- Fixed synthetic labeled Python corpus 87 cases, TP36, FP0, FN2, precision 100% and recall 94.74% WITHIN FIXED SYNTHETIC CORPUS ONLY; never extrapolate to real-world security detection. Known indirection misses: dynamic getattr builtins eval and dynamic subprocess import.

## Unverified scope

SQL created using indirect builders, side-effected control flow, unsupported dynamic imports, actual exploitability/false-positive rate on independent customer code and JS/TS full parser depth remain outside this improvement. Retail clean Windows, SmartScreen, network packet evidence, original NOTICE/legal attribution and human PDF visual gates remain unverified. No EXE publication, source data upload, OS policy change or payment activity.
