"""Printable, offline manual review worksheet for an exact Windows EXE.

Reuses all five provenance stages; NEVER certifies third-party ownership,
NOTICE, legal compliance, or retail-release readiness. No network, source
execution, full license text, binary or customer data are exported.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter
from pathlib import Path

from scripts.build_notice_review_queue import (
    FORMAT as QUEUE_FORMAT,
    _BUILD_EVIDENCE,
    _BYTE_EVIDENCE,
    _EXE_EVIDENCE,
    _PKG_EVIDENCE,
    _SOURCE_CATEGORIES,
    build_review_queue,
)
from scripts.reconcile_notice_gaps import MAX_INPUT_BYTES, MAX_ROWS
from scripts.verify_upstream_tcl_tk_license import _safe_read

FORMAT = "code_checker_local_retail_manual_review_worksheet_v1"
MAX_HTML_BYTES = 8 * 1024 * 1024
SHA256 = re.compile(r"[a-f0-9]{64}\Z")
BLOCK_FLAGS = ("vendor_or_binary_ownership_certified",
               "third_party_notice_ready", "license_compliance_certified",
               "customer_release_ready", "original_license_texts_included")


def priority_for(row: dict) -> int:
    """Prioritize verification effort, not risk or actual license violations."""
    if (row["build_record_evidence"] != "recorded_build_source_path_candidate"
            or row["source_byte_match"] in (
                "different_bytes_review_required", "comparison_error_unverified")):
        return 0
    if row["source_byte_match"] != "byte_identical_to_recorded_build_source":
        return 1
    return 2


def render_review_worksheet(queue: dict) -> str:
    """Render a print-only HTML sheet from an exact, blocked EXE review queue."""
    if (not isinstance(queue, dict) or queue.get("format") != QUEUE_FORMAT
            or queue.get("actual_exe_hash_verified") is not True
            or queue.get("five_stage_evidence_reconciled") is not True
            or any(queue.get(key) is not False for key in BLOCK_FLAGS)
            or type(queue.get("unresolved_entry_count")) is not int
            or not 0 < queue["unresolved_entry_count"] <= MAX_ROWS
            or not isinstance(queue.get("exe_sha256"), str)
            or SHA256.fullmatch(queue["exe_sha256"]) is None
            or type(queue.get("exe_bytes")) is not int
            or queue["exe_bytes"] <= 0
            or queue.get("status") != "LOCAL_EVIDENCE_ONLY_RETAIL_RELEASE_BLOCKED"):
        raise ValueError("The EXE review queue must be exact and retail-blocked")

    rows = queue.get("unresolved_entries_requiring_review")
    if not isinstance(rows, list) or len(rows) != queue["unresolved_entry_count"]:
        raise ValueError("Incomplete owner/NOTICE review rows")
    names: set[str] = set()
    categories: Counter[str] = Counter()
    source_claims: Counter[str] = Counter()
    priorities: dict[int, list[dict]] = {0: [], 1: [], 2: []}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Invalid review entry")
        name = row.get("archive_entry")
        if (not isinstance(name, str) or not 0 < len(name) <= 512
                or any(ord(char) < 32 or ord(char) == 127 for char in name)
                or name in names):
            raise ValueError("Duplicate or unsafe archive entry")
        names.add(name)
        if (row.get("entry_kind") != "CArchive"
                or not isinstance(row.get("unresolved_category"), str)
                or not row["unresolved_category"].startswith("unresolved")
                or row.get("human_owner_version_and_license_review") != "REQUIRED"
                or row.get("redistribution_permission_verified") is not False
                or row.get("build_record_evidence") not in _BUILD_EVIDENCE
                or row.get("source_byte_match") not in _BYTE_EVIDENCE
                or row.get("source_location_category") not in _SOURCE_CATEGORIES
                or row.get("exe_toc_evidence") not in _EXE_EVIDENCE
                or row.get("pkg_toc_evidence") not in _PKG_EVIDENCE):
            raise ValueError("Unknown review evidence or prematurely approved row")
        categories[row["unresolved_category"]] += 1
        source_claims[row["build_record_evidence"]] += 1
        priorities[priority_for(row)].append(row)
    if (dict(sorted(categories.items()))
            != queue.get("unresolved_category_counts")
            or dict(sorted(source_claims.items()))
            != queue.get("build_source_candidate_counts")):
        raise ValueError("Source/category totals do not reconcile")

    def e(value: str | None) -> str:
        return html.escape(value if value is not None else "not observed", quote=True)

    labels = {
        0: ("01 — 출처 고유 연결 없음 또는 바이트 불일치", "Prioritize origin investigation, not a violation finding"),
        1: ("02 — 출처 후보 있으나 바이트 동일성 미확인", "Confirm actual embedded bytes and vendor license"),
        2: ("03 — 소스 후보와 바이트 동일", "Still verify owner, exact license, NOTICE and rights"),
    }
    sections = []
    count = 0
    for priority, (title, note) in labels.items():
        section_rows = priorities[priority]
        count += len(section_rows)
        tr = []
        for idx, row in enumerate(section_rows, 1):
            evidence = " | ".join([
                row["build_record_evidence"],
                row["source_byte_match"],
                row["source_location_category"] or "source-location unknown",
                row["exe_toc_evidence"] or "EXE-TOC not required",
                row["pkg_toc_evidence"] or "PKG-TOC not required",
            ])
            tr.append(
                "<tr><td>" + str(idx) + "</td>"
                "<td><code>" + e(row["archive_entry"]) + "</code></td>"
                "<td>" + e(row["unresolved_category"]) + "</td>"
                "<td class='small'>" + e(evidence) + "</td>"
                "<td class='blank'>Owner/version:<hr>Exact LICENSE source:<hr>NOTICE/copyright:<hr>Reviewer/date:</td>"
                "</tr>"
            )
        sections.append(
            "<section><h2>" + e(title) + " <small>(" + str(len(section_rows))
            + ")</small></h2><p>" + e(note) + "</p>"
            "<table><thead><tr><th>#</th><th>Archived item</th>"
            "<th>Unresolved class</th><th>Observed source claims (not rights)</th>"
            "<th>Human review / references — blank</th></tr></thead>"
            "<tbody>" + "".join(tr) + "</tbody></table></section>"
        )
    if count != queue["unresolved_entry_count"]:
        raise ValueError("Rendered review count mismatch")
    doc = (
        "<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
        "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; "
        "style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'\">"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>EXE owner and NOTICE review — NOT APPROVED</title>"
        "<style>body{font:13px/1.5 sans-serif;color:#202124;margin:25px}"
        "h1{font-size:22px}h2{font-size:17px;margin-top:34px}"
        "p{max-width:1040px}strong.block{color:#9b1c1c}"
        "code{font-size:11px;overflow-wrap:anywhere}"
        "table{width:100%;border-collapse:collapse;table-layout:fixed}"
        "th,td{border:1px solid #aaa;text-align:left;vertical-align:top;padding:7px;overflow-wrap:anywhere}"
        "th:nth-child(1){width:4%}th:nth-child(2){width:20%}"
        "th:nth-child(3){width:19%}th:nth-child(4){width:27%}"
        "th:nth-child(5){width:30%}tr{break-inside:avoid}"
        ".small{font-size:11px}.blank{font-size:11px;color:#555}"
        ".blank hr{border:0;border-top:1px solid #ccc;margin:10px 0}"
        "@media print{@page{size:A4 landscape;margin:11mm}"
        "body{margin:0}h2{break-after:avoid}table{font-size:10px}}</style>"
        "</head><body>"
        "<h1>EXE 수동 라이선스 / 저작권 검토표</h1>"
        "<p><strong class='block'>UNVERIFIED — NOT A LICENSE CLEARANCE OR "
        "CUSTOMER RELEASE APPROVAL.</strong> "
        "An EXE name or matched source bytes do NOT establish the binary owner, "
        "redistribution rights, copyright terms, or customer NOTICE.</p>"
        "<p>Exact candidate EXE SHA-256: <code>" + e(queue["exe_sha256"]) + "</code>; "
        "bytes: " + str(queue["exe_bytes"]) + "; items for human review: "
        + str(queue["unresolved_entry_count"]) + ".</p>"
        "<p>Priority buckets are investigation-order suggestions only. "
        "Do not publish this worksheet as a customer NOTICE. "
        "Do not copy original LICENSE texts or binary files into GitHub.</p>"
        + "".join(sections)
        + "<p><strong class='block'>Release remains blocked.</strong> "
        "Separate exact original licenses, human copyright/NOTICE signoff, "
        "consumer Windows GUI/Defender/SmartScreen/packet/PDF visual acceptance "
        "and owner approval are REQUIRED.</p></body></html>"
    )
    if len(doc.encode("utf-8")) > MAX_HTML_BYTES:
        raise ValueError("Worksheet would exceed bounded size")
    return doc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print-only exact-EXE license review worksheet")
    for key in ("audit", "mapping", "native", "exe-toc", "pkg-toc", "exe", "out"):
        parser.add_argument("--" + key, required=True, type=Path)
    args = parser.parse_args(argv)
    inputs = (args.audit, args.mapping, args.native, args.exe_toc, args.pkg_toc, args.exe)
    try:
        if (args.out.exists() or args.out.is_symlink()
                or not args.out.parent.is_dir() or args.out.parent.is_symlink()
                or args.out in inputs or len(set(inputs)) != len(inputs)
                or args.out.suffix.lower() != ".html"):
            raise ValueError("New distinct HTML output and exact separate inputs required")
        stages = [json.loads(_safe_read(path, MAX_INPUT_BYTES)) for path in inputs[:5]]
        queue = build_review_queue(*stages, args.exe)
        content = render_review_worksheet(queue)
        with args.out.open("x", encoding="utf-8", newline="\n") as output:
            output.write(content)
        print("OFFLINE_EXE_MANUAL_OWNER_REVIEW_WORKSHEET_CREATED")
        print("EXACT_EXE_SHA256_VERIFIED=True")
        print("REVIEW_ROWS=" + str(queue["unresolved_entry_count"]))
        print("LICENSE_COMPLIANCE_AND_CUSTOMER_RELEASE=False")
        return 0
    except (OSError, ValueError, TypeError, KeyError, AttributeError,
            json.JSONDecodeError):
        print("OFFLINE_EXE_MANUAL_OWNER_REVIEW_WORKSHEET_INVALID")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
