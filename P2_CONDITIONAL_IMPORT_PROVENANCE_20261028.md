# P2-3 — Conditional import provenance correctness (2026-10-28 KST)

## Issue

Bug: AST module binding chronology claimed imports nested in guarded if/else, try/except/finally, with, for/while and match suites as unconditional global provenance, causing false positive subprocess/requests/pickle attribution after conditional branch could have been skipped.

## Implemented

Source static_checks.py now attaches binding AST origin and matches exact guarded suite ancestry. Only within the import's same or nested arm may it assert sensitive API binding. Later unconditional direct imports remain recognized. Conditional-only origins outside the arm are UNKNOWN rather than falsely attributed. Maintains conservative shadow/alias behavior and no inspected code execution.

## Tests and observed results

Added 16 labeled, synthetic positive/negative cases in scripts/evaluate_rule_accuracy.py and 2 exhaustive scenario regression methods in tests/test_rule_accuracy.py; conditional inside-arm risks preserved.

First feature SHA 1e3a7748 failed CI because recursive AST traversal dropped module-origin metadata inside guarded suites, reducing true positives. Fixed by passing direct-provenance flag through module-level guarded blocks, while still stopping at function/class scopes; reran exact SHA successfully. Never count failed attempt as proof.

Feature exact SHA 4a8ae1ef CI: general Tests https://github.com/hibi89/ai-code-checker/actions/runs/40534409884 16/16 SUCCESS (one Ubuntu 3.11 job 278 unit tests pass); Windows packaged EXE and Tk synthetic https://github.com/hibi89/ai-code-checker/actions/runs/40534410635 SUCCESS; performance/dependency inventory https://github.com/hibi89/ai-code-checker/actions/runs/40534409912 3/3 SUCCESS.

Fixed 119 synthetic Python cases, 49 TP, 0 FP, 0 FN, 100% synthetic precision/recall WITHIN FIXED LABELED CORPUS ONLY. Does not measure real-world false positives/false negatives or vulnerability exploitability. JS/TS still limited, not full parser.

## Limitations

Current product status functional developer MVP remains CI-supported; consumer Windows, SmartScreen, actual OS packets, original bundled third-party NOTICE/legal, human Korean PDF visual and explicit owner distribution authorization are still UNVERIFIED/BLOCKED. No EXE distributed or signed; no paid APIs/secret/user data upload.

Next GO: verify latest main SHA and Actions, prioritize actual correctness/Windows user workflow gap instead of more design-only notes. Feature branch → regression → full CI → merge. Do not claim licensed sellable software from this improvement.
