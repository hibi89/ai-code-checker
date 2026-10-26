# CODE CHECKER v2 — Phase2 P0-C performance and dependency inventory

2026-10-26 KST. Public/MIT product. This is a measured **synthetic CI** acceptance gate, not a guarantee of every customer project size or an approval to resell bundled binaries.

## Benchmark scope and fixtures

Command: `python -m scripts.benchmark_offline` on a system with `requirements-offline.txt` installed. All inputs are deterministic/generated into a temporary folder; no original customer code, paid AI API, hosting or external inputs.

| Scenario | Source | Expected |
|---|---|---|
| txt_1200 | raw 1,200-line TXT with Python selected; dynamic call at last line | exactly 1 analyzed, 1,200 lines; HTML+Markdown |
| zip_12 | 12 in-memory-generated ZIP `.py` files × 100 lines | 12 analyzed, 1,200 lines; HTML+Markdown |
| folder_200_12k | 200 `.py` files × 60 code lines | 200 analyzed, 12,000 lines; complete |
| folder_multimeg_200_12k | 200 `.py` files × 59 long comment lines + one assignment | 200 analyzed, 12,000 lines; ~6 MB, below 8 MiB cap |
| folder_201_over_limit | 201 `.py` files | InputError, blocked; never truncate silently |

Measured wall time covers the scanner, findings, evidence checking, and completed HTML/Markdown file publication. `tracemalloc_peak_mib` is *tracked Python allocations*, NOT peak resident RAM; the run records platform, CPython version, bytes/lines, output sizes and elapsed seconds for each case. Fixture generation and initial import/setup are outside measurement, and clean Windows EXE startup & Edge PDF memory are not benchmarked. GitHub-hosted virtual runners vary; avoid permanent performance claims based on one machine.

The workflow `p0c-performance-inventory.yml` runs full workloads independently on Windows Server 2025 and Ubuntu 24.04 with Python 3.13. It tests correctness and reports measured numbers, without invented speed/memory acceptance cutoffs. Comparison across runs is informative, not deterministic performance regression certification. Because default folder caps are 200 *eligible* files/1 MiB each/8 MiB total, the benchmark must not be marketed as unrestricted project-size support.

## Dependency metadata inventory

Command: `python -m scripts.offline_dependency_inventory --strict`, inside a Windows build environment with `requirements-offline-build.txt` already installed (`pydantic==2.12.5`, `pyinstaller==6.22.3`). It enumerates recursively selected *installed* Python package dependencies, records versions, declared SPDX expression/legacy classifiers/license metadata and unresolved requirements, and fails if required roots don't match. It does not download any package. It always reports **INVENTORY_ONLY_REVIEW_REQUIRED**, regardless of metadata completeness.

The Windows workflow additionally runs `pip-audit -r requirements-offline-build.txt` in CI to check published vulnerabilities in pinned build dependencies. This is a network-backed CI advisory lookup for publicly known packages/versions, **not an app runtime call and not proof of no vulnerabilities**. If audit fails, inspect exact package/advisory and fix or document blocker rather than ignore. Avoid ever sending customer code or secrets to CI.

### Scope exclusions — still pending

- Installed-environment distribution closure is **not** a byte-for-byte PyInstaller EXE SBOM. PyInstaller hooks may add different modules, Tcl/Tk and system DLLs not included in the Python dependency closure.
- License metadata alone is **not** a redistributable copyright/license notices review. Inspect full wheel/EXE contents, license texts, runtime/bundled dynamic libraries, Python/Tcl/Tk notices, commercial obligations and attribution before release.
- `pip-audit` checks only published known vulnerabilities in Python packages at CI lookup time; Windows Defender/SmartScreen, malware scanner, remote traffic capture, code signing and clean-device UX still UNVERIFIED.
- There is no genuine user performance sample, representative mixed-language corpus, repeated-run variance study, system-level peak RSS or EXE/browser startup data yet.

## Decision and next acceptance gate

Measured runs create a reproducible development baseline, not a commercial SLA. Once both Ubuntu/Windows benchmarks and Windows installed-dependency/CVE check succeed, freeze evidence in STATUS/HANDOFF after CI and compare any later figures. Next priority is license-text and actual packaged-EXE SBOM audit, realistic Windows clean-device/security acceptance, then deeper Python rules and JS/TS coverage.
