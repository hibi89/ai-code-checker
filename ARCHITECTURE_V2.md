# Code Checker v2 — Offline-First Architecture (Target Approved; Implementation Pending)

## Alternatives considered
A. Existing Gemini-first, report-only service: fastest to operate but provider/network dependence, uncertain structured output and recurring requests; buyer cannot reuse.
B. Offline local static checker with optional human report service: more GUI/packaging work and reduced semantic reasoning depth, but zero mandatory API/server cost, reusable customer value, controllable privacy. **Recommended.**
C. Eight independent AI agents: deeper deliberative potential, but nonzero calls and complex orchestration, unvalidated accuracy gain. Defer to separate premium experiment.

## Event and data flow
1. Local user selects folder/ZIP/file in Windows application.
2. Input manifest builder performs path validation, exclusions, type/size/encoding checks, and captures coverage manifest; no source execution.
3. Local analyzer executes deterministic checks with source maps; optional safe static analyzer integrations are disabled unless installed/bundled and verified.
4. Findings normalizer de-duplicates evidence-identical items, maps severity and rule identifiers, records uncertainty and coverage.
5. Report gate separates process success, scan completeness and human verification status. A report with missing files or unverified severe findings must visibly say so; never return 'security verified'.
6. Local HTML/Markdown report writer escapes all untrusted text, writes atomically to new paths, and exposes browser Print-to-PDF. File names must not collide. No web assets.
7. Optional **manual** AI mode must be separately selected and approved for explicit external data transfer and priced BYOK; no silent fallback, no retries without permission.
8. Optional seller-assisted report may be human-reviewed and delivered from a local workflow, not from the purchaser's scan automatically.

## Resource and error design
- Scanner manifest records each file's status: analyzed, ignored by policy, unsupported, over-limit, parse-error, cancelled.
- Core checks are CPU local with bounded memory / runtime; no URL fetch. Initial parser has no need to start interpreters executing the customer's files.
- On parser/optional integration errors, mark partial rather than clean, preserve old report, preserve diagnostic metadata without code content.
- No automatic resend, no job queue, no server, no account tokens.
- Scan outputs stored apart from source, with explicit delete control. Do not write to synced cloud storage by default.

## Python/JS-TS scope
- Phase 0: Python syntax/AST, file-risk patterns, secret patterns, existing CLI reuse.
- Phase 1: JS/TS syntax/lint integration with tested fixed configuration that doesn't run customer-controlled plugins. If safe integration can't be verified, mark JS/TS as basic-only or unsupported.
- Ruff (MIT) and Bandit (Apache-2.0) are optional, pending pinned versions, licensing notice and safe subprocess/parse-only testing.
- Semgrep community rules are NOT bundled by default; some registry rules have redistribution restrictions even when a CLI is free.
- OSV Scanner offline mode requires a previously downloaded database; disable default network/dependency-vulnerability scans unless explicitly updated by the customer.

## Product packaging
- Windows portable release or one-folder zip preferred. Initial UI candidate: stdlib tkinter with Python packaged using PyInstaller (commercial bundling permitted subject to dependency licenses).
- PDF v1: self-contained HTML and system/browser printing; no paid PDF library and no embedded licensed fonts.
- Unsigned Windows binaries can show SmartScreen warning or be blocked. Document the limitation and verify user installation; code signing is a later approval-gated cost decision.
- Build/release artifacts never contain raw customer code or secrets.

## Repository plan
- `main`: approved documentation baseline and working public MIT CLI; preserve historical implementation. Owner approved docs integration and MVP-first approach 2026-10-26; production code migrates through tested feature PRs only.
- `plan/offline-zero-cost-v2`: architecture/governance/proposed requirements and handoff only (this branch).
- Future implementation branches on actual need: `feature/offline-core`, `feature/offline-report-ui`, `feature/windows-portable`, `hardening/prelaunch`; create one at a time when work begins. Use PR/CI; no force pushes.
- GitHub Actions: on default branch currently runs a 15-case OS/Python matrix plus dependency audit; propose a lean PR smoke matrix and release-only full matrix after approval. No production keys or Gemini calls in CI.
- Public standard GitHub hosted Actions runtime is free, while GitHub Free private hosted quota is 2,000 minutes/month; other storage/large runner costs remain possible.
- A public branch cannot conceal proprietary code; a separate private product code repository would require owner approval and CI quota planning. Do NOT create another repo without permission.

## Revert and recovery
Keep baseline main SHA `8c72a6f3bc30f2a720c10f3a5a9dd366f0d059ab`; rollback by leaving proposal unmerged. Before any code migration, preserve an immutable tag or verified SHA and compare tests. Never force-push.

## Unified intake specification update (2026-10-26)
ZIP/folder, single TXT, delimited multi-file TXT and pasted code all produce normalized `VirtualSourceFile` entries and a `ScanManifest`. The latter records original container, logical path, original line provenance, language source/selection, analysis coverage, parsing failures and exclusions. Intake must not execute code or install dependencies.

Raw TXT uses exactly one source file with selected language; it cannot imply dependencies. Delimited TXT has explicit header lines `===== FILE: relative/path.ext =====`, strict parsing and collision handling. ZIP preserves relative paths, validates archive metadata and content limits, and is never unpacked as an executable project.

A result gate operates on all eligible files, not merely the existence of some findings. Large input must be fully processed within proven limits or marked `partial`/`blocked`. Do not claim comprehensive security analysis from file enumeration. Exact grammar, errors and test cases in [INPUT_SPEC_V2.md](INPUT_SPEC_V2.md).

## Binding product and delivery references
- [FINAL_PRODUCT_BLUEPRINT.md](FINAL_PRODUCT_BLUEPRINT.md) is the approved target vision; v2 source is not implemented yet.
- [MVP_3DAY_ROADMAP.md](MVP_3DAY_ROADMAP.md) details 3-day MVP and later gap/hardening/launch gates.
- [INPUT_SPEC_V2.md](INPUT_SPEC_V2.md) is normative for TXT / ZIP / folders / paste and exact coverage reporting.
