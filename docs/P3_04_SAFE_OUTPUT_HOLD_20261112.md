# P3-04 — candidate output preserve-on-error (2026-11-12 KST)

## Decision / threat model
Candidate ZIP and JSON failure cleanup used pathname `unlink`. If another process replaced the path after exclusive creation, deletion could remove a third party's file. (A) Check inode before unlink: still time-of-check/time-of-use race. (B) On failure **do not delete anything automatically**; keep new unapproved outputs on HOLD, require fresh unique paths on retries (existing `O_EXCL`), and manual owner-only review: **selected**.

Modified `scripts/build_private_customer_candidate.py`, `scripts/prepare_private_retail_review.py`, `scripts/link_private_candidate_evidence.py`; tests under `tests/test_private_candidate_builder.py` and `tests/test_private_retail_review.py` cover late-path replacement of candidate ZIP and ZIP+JSON. No automatic sales, no authorization claims.

## Verification
Functional and test SHA: `41bb08b4c5dc5bab58a0402a4b38eef8bb4ec1ab` at [GitHub Actions #43220090428](https://github.com/hibi89/ai-code-checker/actions/runs/43220090428) — **16/16 jobs SUCCESS** (Ubuntu 24.04/26.04 + Windows 2025, Python3.11–3.15, dependency audit). Ubuntu24/3.13: **503 total / 482 pass / 21 skip / 0 fail**. Windows2025/3.13: **503 total / 501 pass / 2 skip / 0 fail**. Existing offline MVP PASS.

First code commit `fe2a7b52b39819b8fa8730c6e4dbbd0b644f900e` failed one old deletion-assumption assertion: 1 FAIL of 503, not a source-runtime failure. Changed assertion to validate HOLD, then full CI green at `41bb08b4c5dc5bab58a0402a4b38eef8bb4ec1ab`. Do not claim first run green.

## Status / blockers
Engineering **85% provisional unchanged, 95% not reached**, commercial RELEASE HOLD. Hosted CI synthetic/offline is not human Windows10/11 buyer acceptance. Need actual owner EXE and source-correct Tcl/Tk/frozen binary license/NOTICE rights mapping, real clean-device GUI/PDF/Defender/SmartScreen/network checks, customer support/sale terms, and explicit seller approval. Main and real owner originals preserved; no physical EXE/customer secrets uploaded. Failed output artifacts must never be delivered.
