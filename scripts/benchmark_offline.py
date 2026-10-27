"""Repeatable SYNTHETIC-ONLY Code Checker input/scan/report benchmarks.

No customer inputs, API keys, downloads or external code execution. Performance
figures are runner-specific, not universal Windows product guarantees.
tracemalloc covers traced Python allocations, not native/private RSS.
"""
from __future__ import annotations

import argparse
import json
import platform
import tempfile
import time
import tracemalloc
import zipfile
from pathlib import Path

from code_input import InputError, bundle_from_text
from offline_core import OFFLINE_LIMITS, scan_path
from offline_report import build_report, write_report


def fixtures(parent: Path, *, full: bool = True):
    """Generate fixed patterns, 0 source code execution, no personal files."""
    paths = {}
    text = parent / "synthetic_1200.txt"
    text.write_text("value = 1\n" * 1199 + "eval('1+1')\n", encoding="utf-8", newline="\n")
    paths["txt_1200"] = (text, "python", 1, 1200, "complete")

    archive_path = parent / "synthetic_12.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for n in range(12):
            archive.writestr(f"src/module_{n:02d}.py", "number = 1\n" * 100)
    paths["zip_12"] = (archive_path, None, 12, 1200, "complete")

    small = parent / "synthetic_200"
    small.mkdir()
    for n in range(200):
        (small / f"module_{n:03d}.py").write_text("number = 1\n" * 60, encoding="utf-8", newline="\n")
    paths["folder_200_12k"] = (small, None, 200, 12000, "complete")

    if full:
        dense = parent / "synthetic_dense_findings_1200.py"
        dense.write_text("eval(value)\n" * 1200, encoding="utf-8", newline="\n")
        paths["dense_findings_1200"] = (dense, None, 1, 1200, "complete")

        multi = parent / "synthetic_multimeg_200"
        multi.mkdir()
        # 60 lines * 512 B per line * 200 files = 6,144,000 bytes,
        # comfortably within current 8-MiB project / 1-MiB per-file bounds.
        source = ("#" + "a" * 510 + "\n") * 59 + "number = 1\n"
        assert len(source.splitlines()) == 60
        assert len(source.encode("utf-8")) > 30_000
        for n in range(200):
            (multi / f"module_{n:03d}.py").write_text(source, encoding="utf-8", newline="\n")
        paths["folder_multimeg_200_12k"] = (multi, None, 200, 12000, "complete")
    return paths


def one_case(label, source, language, expected_files, expected_lines, expected_status, out_dir):
    """Records scan+verified report+HTML/Markdown local file writing."""
    source_bytes_before = source.read_bytes() if source.is_file() else None
    tracemalloc.start()
    start = time.perf_counter()
    scan = scan_path(source, language=language)
    report = build_report(scan)
    html, md = write_report(report, out_dir, name="bench-" + label.replace("_", "-"))
    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    actual_lines = sum(file.line_count for file in scan.bundle.files)
    if not (
        scan.status == expected_status
        and report.status == expected_status
        and scan.counts["analyzed"] == expected_files
        and actual_lines == expected_lines
        and html.exists() and md.exists()
        and html.stat().st_size > 100 and md.stat().st_size > 50
    ):
        raise AssertionError(f"Synthetic acceptance mismatch in {label}")
    if source_bytes_before is not None and source.read_bytes() != source_bytes_before:
        raise AssertionError("Input mutated")
    return {
        "case": label, "status": scan.status, "analyzed_files": expected_files,
        "source_lines": actual_lines, "source_bytes": scan.bundle.source_bytes,
        "elapsed_seconds": round(elapsed, 4),
        "throughput_mib_per_second": round(
            (scan.bundle.source_bytes / (1024 * 1024)) / elapsed, 4
        ) if elapsed > 0 else None,
        "tracemalloc_peak_mib": round(peak / (1024 * 1024), 3),
        "rss_measured": False,
        "report_html_bytes": html.stat().st_size,
        "report_markdown_bytes": md.stat().st_size,
        "findings": len(report.findings),
    }


def dense_redaction_case():
    """Measure only local input normalization of dense synthetic PII, no scan/report."""
    count = 6000
    text = "".join(
        f"person_{n:05d} = 'user{n:05d}@synthetic.invalid'\\n"
        for n in range(count)
    )
    # The benchmark is synthetic and within the current 1 MiB per-file cap.
    tracemalloc.start()
    start = time.perf_counter()
    bundle = bundle_from_text(text, filename="synthetic.py", limits=OFFLINE_LIMITS)
    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    positions = tuple(item.line_number for item in bundle.files[0].redactions)
    if (len(positions) != count or positions != tuple(range(1, count + 1))
            or "synthetic.invalid" in bundle.files[0].text):
        raise AssertionError("Dense synthetic redaction did not preserve line citations")
    return {
        "case": "dense_redaction_6000",
        "scope": "input_normalization_only_no_scan_or_report",
        "input_bytes": len(text.encode("utf-8")),
        "redacted_items": count,
        "elapsed_seconds": round(elapsed, 4),
        "tracemalloc_peak_mib": round(peak / (1024 * 1024), 3),
        "rss_measured": False,
        "before_version_direct_comparison": False,
    }


def boundary_cases(parent: Path):
    """Fail-closed checks: no silent truncation, no 'complete' on limits."""
    folder = parent / "synthetic_201"
    folder.mkdir()
    for n in range(201):
        (folder / f"file_{n:03d}.py").write_text("print('ok')\n", encoding="utf-8", newline="\n")
    try:
        scan_path(folder)
    except InputError:
        return {"case": "folder_201_over_limit", "result": "blocked", "max_files": 200}
    raise AssertionError("201 eligible sources unexpectedly passed the 200-file cap")


def run_benchmark(*, full: bool = True):
    with tempfile.TemporaryDirectory(prefix="code-checker-bench-") as tmp:
        base = Path(tmp)
        inputs = fixtures(base, full=full)
        output = base / "output"
        cases = [
            one_case(label, *values, output)
            for label, values in inputs.items()
        ]
        checks = [boundary_cases(base)]
        return {
            "benchmark": "synthetic_offline_end_to_end_v1",
            "scope": "scan+normalize+rules+report_verification+HTML/Markdown filesystem write",
            "platform": platform.system(),
            "platform_machine": platform.machine(),
            "python_version": platform.python_version(),
            "python_traced_peak_not_rss": True,
            "tracemalloc_warning": "Only traced Python allocations; excludes native/private RSS and browser/EXE startup.",
            "benchmark_fixture_source_only": True,
            "limits": {"max_eligible_files": 200, "max_file_bytes": 1048576, "max_total_bytes": 8388608},
            "results": cases,
            "redaction_normalization": dense_redaction_case() if full else None,
            "limit_checks": checks,
            "marketing_capacity_certified": False,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Synthetic-only Code Checker performance acceptance")
    parser.add_argument("--quick", action="store_true", help="Skip multi-megabyte test (unit smoke only)")
    args = parser.parse_args()
    try:
        results = run_benchmark(full=not args.quick)
    except (OSError, InputError, AssertionError) as exc:
        print(json.dumps({"status": "BENCH_FAIL", "exception": type(exc).__name__}))
        return 1
    print(json.dumps(results, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
