"""PROOFQA P85: synthetic, fail-closed six-phase audit and report composer.

Developer-only proof of report mechanics; never execute a customer program,
promote Code Checker candidates to confirmed, or release a customer report.
Cloudflare security-audit-skill is methodology only, NOT installed or executed.
"""
from __future__ import annotations

import hashlib
import html
import io
import json
import os
import re
from pathlib import Path
from typing import Any

from code_input import InputError
from output_safety import validate_output_location

CONTRACT = "proofqa.p85.audit.v1"
GRAPH_VERSION = "0.9.108"
BROWSER_VERSION = "0.43.0"
SHA_RE = re.compile(r"^[a-f0-9]{64}$")
FILE_NAMES = (
    "audit.json", "coverage-ledger.json", "findings.json",
    "report.json", "report.html", "report.pdf",
)
PHASES = (
    "reconnaissance",
    "coverage_led_hunting",
    "candidate_validation",
    "structured_output",
    "independent_record_verification",
    "target_neutral_reporting",
)
COVERAGE_UNITS = (
    ("p50_static_candidates", "Static candidates observed in synthetic ZIP"),
    ("p70_python_ast", "Pinned Graphify Python source locations"),
    ("p70_javascript_ast", "Pinned Graphify JavaScript source locations"),
    ("p70_sql_ast", "Pinned Graphify SQL source locations"),
    ("p70_finding_graph_links", "Two P50 source candidates linked to real AST edges"),
    ("p70_browser_dom", "Synthetic localhost Chromium DOM and clicks"),
    ("p70_http_200_500", "Browser-generated HTTP 200 and 500 responses"),
    ("p70_save_reopen", "Synthetic write, refresh, and backend reopen"),
    ("raw_graph_independent_replay", "Original raw AST and source independently re-scanned"),
    ("independent_human_verifier", "Fresh independent reviewer disproves security candidate"),
    ("authorized_customer_staging", "Customer-authorized test staging validated"),
    ("windows10_11_real_device", "Real physical Windows10/11 Chrome/Edge QA"),
    ("os_enforced_network_sandbox", "Real OS enforced no-egress and resource sandbox"),
    ("manual_pdf_visual_review", "Human PDF raster/layout inspection"),
)
COMPLETE = {x[0] for x in COVERAGE_UNITS[:8]}
NOT_COVERED = {x[0] for x in COVERAGE_UNITS[8:]}


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False)
            + "\n").encode("utf-8")


def _valid_sha(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA_RE.fullmatch(value))


def _validate_actual_p70(graph: dict[str, Any], browser: dict[str, Any]) -> None:
    if (graph.get("contract") != "proofqa.p70.graph.acceptance.v1"
            or graph.get("status") != "PASS" or graph.get("release_state") != "HOLD"
            or graph.get("security_claim") != "NOT_A_SECURITY_CERTIFICATION"
            or graph.get("tools", {}).get("version") != GRAPH_VERSION
            or graph.get("tools", {}).get("backend") != "none"
            or graph.get("tools", {}).get("mode") != "code-only"
            or graph.get("source_files") != 3
            or graph.get("static_scan_status") not in {"complete", "partial"}):
        raise InputError("P70 Graphify 실제 로컬 합성 검증 증거가 불충분합니다.")
    hashes = graph.get("sha256")
    if not isinstance(hashes, dict) or not all(
        _valid_sha(hashes.get(key))
        for key in ("source_archive", "graph_json", "p50_case")
    ):
        raise InputError("P50/Graphify 출처 SHA256 근거가 없습니다.")
    ast = graph.get("ast_nodes")
    if not isinstance(ast, dict) or any(
        not isinstance(ast.get(suffix), int) or isinstance(ast.get(suffix), bool)
        or ast[suffix] < 1 for suffix in (".py", ".js", ".sql")
    ):
        raise InputError("Python/JS/SQL 실제 AST 범위가 불충분합니다.")
    summary = graph.get("finding_correlation")
    rows = graph.get("correlation_evidence")
    if (not isinstance(summary, dict) or not isinstance(rows, list)
            or summary.get("findings_total") != len(rows)
            or summary.get("source_linked") != len(rows)
            or summary.get("impact_linked") != len(rows)
            or summary.get("confirmed_security_findings") != 0
            or len(rows) < 2 or len(rows) > 12):
        raise InputError("P50 findings 연결 원본 요약/증거가 일치하지 않습니다.")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("finding_index"), int):
            raise InputError("finding index 증거 형식 오류.")
        idx = row["finding_index"]
        if idx in seen or idx < 0:
            raise InputError("중복되거나 음수 finding index.")
        seen.add(idx)
        if (row.get("source_path") != "app.py"
                or not isinstance(row.get("line"), int) or row.get("line") < 1
                or not _valid_sha(row.get("source_sha256"))
                or row.get("graph_status") != "SOURCE_FILE_CORRELATED"
                or row.get("confidence") not in {"SAME_START_LINE", "FILE_SCOPE_APPROXIMATE"}
                or not isinstance(row.get("impact_edges"), list)
                or not any(edge.get("confidence") == "EXTRACTED" for edge in row["impact_edges"])):
            raise InputError("P70 출처/라인/Graphify 신뢰 계약 위반.")
    source_shas = {row.get("source_sha256") for row in rows if isinstance(row, dict)}
    if len(source_shas) != 1:
        raise InputError("서로 다른 후보 소스 파일 digest는 한 검수에 혼용할 수 없습니다.")
    expected = [
        ("GET", "/api/ok", 200), ("GET", "/api/fail", 500),
        ("POST", "/api/save", 200), ("GET", "/api/reopen", 200),
    ]
    if (browser.get("contract") != "proofqa.p70.browser.acceptance.v1"
            or browser.get("status") != "PASS"
            or browser.get("release_state") != "HOLD"
            or browser.get("agent_browser_version") != BROWSER_VERSION
            or browser.get("scope") != "synthetic 127.0.0.1 only"
            or browser.get("customer_site_tested") is not False
            or browser.get("payment_or_destructive_actions") is not False
            or browser.get("persist_and_reopen_verified") is not True
            or browser.get("snapshot_confirmed") is not True
            or browser.get("http_requests_checked") != [list(e) for e in expected]):
        raise InputError("실 Chromium의 synthetic scope/network/DOM 교차증거가 불충분합니다.")


def canonical_lines(report: dict[str, Any], findings: list[dict[str, Any]]) -> list[str]:
    counts = report["counts"]
    coverage = report["coverage"]
    lines = [
        "PROOFQA AX P85 SYNTHETIC REPORT",
        "CONTRACT: " + CONTRACT,
        "SUBJECT_SHA256: " + report["subject_sha256"],
        "CASE_SOURCE: SYNTHETIC_ONLY",
        "RUN_STATUS: incomplete",
        "COVERAGE: planned={planned} completed={completed} not_covered={not_covered}".format(**coverage),
        "FINDINGS: total={total} confirmed={confirmed} needs_validation={needs_validation} rejected={rejected} not_covered={not_covered}".format(**counts),
    ]
    for row in findings:
        lines.append(
            "FINDING {id} STATUS {status} EVIDENCE {refs}".format(
                id=row["id"], status=row["status"], refs=",".join(row["evidence_refs"])
            )
        )
    lines.extend([
        "VERIFIER: code_contract_only; fresh_agent=NOT_RUN",
        "SECURITY_CERTIFICATION: FALSE",
        "CUSTOMER_ACCEPTED: FALSE",
        "RELEASE: HOLD",
    ])
    return lines


def _pdf_bytes(lines: list[str]) -> bytes:
    # Programmatic PDF. reportlab is installed only in the explicitly isolated
    # P85 CI; original CodeChecker runtime still has no PDF dependency.
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    except ImportError as exc:
        raise InputError("P85 PDF 생성 전용 reportlab 의존성을 설치해야 합니다.") from exc
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4, invariant=1, pageCompression=0)
    pdf.setTitle("PROOFQA AX P85 Synthetic Audit - RELEASE HOLD")
    pdf.setAuthor("PROOFQA AX deterministic synthetic CI")
    pagew, pageh = A4
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(36, pageh - 46, "PROOFQA AX - SYNTHETIC AUDIT")
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("HYGothic-Medium"))
        pdf.setFont("HYGothic-Medium", 10)
        pdf.drawString(36, pageh - 64, "합성 코드 검증 보고서 - 고객 검수 및 보안 인증 아님")
    except (KeyError, ValueError):
        # Korean glyph availability must be separately checked in a real client.
        pdf.setFont("Helvetica", 9)
        pdf.drawString(36, pageh - 64, "Synthetic report; not a customer or security certification")
    pdf.setFont("Courier", 7.5)
    y = pageh - 94
    for line in lines:
        if len(line) > 100:
            raise InputError("독립 검증 표준 행 길이 초과.")
        if y < 40:
            pdf.showPage()
            pdf.setFont("Courier", 7.5)
            y = pageh - 44
        pdf.drawString(36, y, line)
        y -= 17
    pdf.save()
    return buffer.getvalue()


def _html_bytes(lines: list[str], findings: list[dict[str, Any]], coverage: list[dict[str, Any]]) -> bytes:
    escaped = html.escape("\n".join(lines), quote=True)
    findings_rows = "\n".join(
        "<tr><td>" + html.escape(str(item["id"])) + "</td><td>"
        + html.escape(str(item["status"])) + "</td><td>"
        + html.escape(str(item["source_path"])) + ":" + str(item["line"])
        + "</td><td>NEEDS INDEPENDENT REVIEW</td></tr>"
        for item in findings
    )
    coverage_rows = "\n".join(
        "<tr><td>" + html.escape(str(unit["id"])) + "</td><td>"
        + html.escape(str(unit["status"])) + "</td></tr>"
        for unit in coverage
    )
    page = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; base-uri 'none'; form-action 'none'; style-src 'unsafe-inline'">
<meta name="referrer" content="no-referrer">
<title>PROOFQA AX P85 - SYNTHETIC HOLD</title>
<style>body{font-family:system-ui,sans-serif;max-width:1000px;margin:40px auto;padding:0 24px;color:#142030}
h1{font-size:28px}pre{white-space:pre-wrap;background:#f5f7fa;padding:20px;border:1px solid #ccd}
table{width:100%;border-collapse:collapse;margin:14px 0}td,th{padding:9px;border:1px solid #bdc9d2;text-align:left}
.warning{font-weight:700;color:#9d2400}</style></head><body>
<h1>PROOFQA AX P85 — 합성 검수 결과</h1>
<p class="warning">출시 보류 (RELEASE HOLD). 고객 실제 환경과 독립 인간 보안 검증은 미실시입니다.</p>
<h2>정규 증거 표시</h2><pre id="canonical">""" + escaped + """</pre>
<h2>후보 (취약점 확정 아님)</h2><table><thead><tr><th>ID</th><th>상태</th><th>소스 위치</th><th>독립 확인</th></tr></thead>
<tbody>""" + findings_rows + """</tbody></table>
<h2>범위 기록</h2><table><thead><tr><th>검수 단위</th><th>판정</th></tr></thead><tbody>""" + coverage_rows + """</tbody></table>
<p>Graphify 코드 관계는 런타임 보안취약점 증거가 아닙니다. 모든 finding의 severity는 미확정(null)입니다.</p>
</body></html>
"""
    return page.encode("utf-8")


def compose(graph: dict[str, Any], browser: dict[str, Any], output_root: str | Path) -> Path:
    """Create-only local contract. This is NOT an auditor or an approval engine."""
    _validate_actual_p70(graph, browser)
    hashes = graph["sha256"]
    sha = hashes["source_archive"]
    coverage = [
        {"id": unit, "description": desc,
         "status": "COMPLETED" if unit in COMPLETE else "NOT_COVERED",
         "scope": "SYNTHETIC", "reviewed_customer": False}
        for unit, desc in COVERAGE_UNITS
    ]
    actual_rows = sorted(graph["correlation_evidence"], key=lambda row: row["finding_index"])
    findings = [
        {
            "id": "PQ85-" + str(index + 1).zfill(3),
            "fingerprint": _digest(
                (sha + "|" + row["source_path"] + "|" + str(row["line"]) + "|" + str(row["finding_index"])).encode()
            ),
            "source_path": row["source_path"],
            "source_finding_index": row["finding_index"],
            "line": row["line"],
            "source_sha256": row["source_sha256"],
            "status": "NEEDS_VALIDATION",
            "category": "static_candidate",
            "severity": None,
            "evidence_refs": ["EV-CHECKER", "EV-GRAPH"],
            "unresolved_fact": "No independently observed boundary violation or actual customer runtime reproduction.",
            "graph_confidence": row["confidence"],
            "customer_scope_approved": False,
            "verified_by_fresh_independent_agent": False,
        }
        for index, row in enumerate(actual_rows)
    ]
    finding_ids = [row["id"] for row in findings]
    if len(finding_ids) != len(set(finding_ids)):
        raise InputError("후보 식별자 중복.")
    count = {
        "total": len(findings),
        "confirmed": 0,
        "needs_validation": len(findings),
        "rejected": 0,
        "not_covered": 0,
    }
    coverage_totals = {
        "planned": len(coverage),
        "completed": sum(x["status"] == "COMPLETED" for x in coverage),
        "not_covered": sum(x["status"] == "NOT_COVERED" for x in coverage),
    }
    evidence = [
        {"id": "EV-CHECKER", "origin": "real P50 offline synthetic ZIP case",
         "sha256": hashes["p50_case"], "source_file_sha256": actual_rows[0]["source_sha256"], "observed": True},
        {"id": "EV-GRAPH", "origin": "real pinned Graphify code-only AST graph",
         "sha256": hashes["graph_json"], "observed": True},
        {"id": "EV-BROWSER", "origin": "real agent-browser 127.0.0.1 synthetic HTTP/DOM",
         "sha256": _digest(_json_bytes(browser)), "observed": True},
    ]
    audit = {
        "contract": CONTRACT,
        "schema_version": 1,
        "subject_sha256": sha,
        "scope": "SYNTHETIC_ONLY",
        "run_status": "incomplete",
        "release_state": "HOLD",
        "architecture": {
            "trust_boundaries": [
                "synthetic ZIP -> P50 read-only static scanner",
                "synthetic files -> Graphify code-only local AST",
                "localhost ephemeral HTTP -> agent-browser synthetic Chromium",
                "evidence records -> separate read-only verifier",
            ],
            "customer_code_executed": False,
            "external_llm_called": False,
            "os_enforced_egress_sandbox": False,
        },
        "phases": [
            {"id": PHASES[0], "state": "COMPLETED_SYNTHETIC"},
            {"id": PHASES[1], "state": "COMPLETED_SYNTHETIC"},
            {"id": PHASES[2], "state": "LIMITED_STATIC_CANDIDATES"},
            {"id": PHASES[3], "state": "COMPLETED_SYNTHETIC"},
            {"id": PHASES[4], "state": "CODE_ONLY_FRESH_AGENT_NOT_RUN"},
            {"id": PHASES[5], "state": "COMPLETED_SYNTHETIC"},
        ],
        "evidence": evidence,
        "coverage": coverage_totals,
        "finding_counts": count,
        "independent_human_security_verification": "NOT_RUN",
        "limitations": [
            "Cloudflare method referenced; no Cloudflare skill execution or multi-agent delegation.",
            "Independent executable verifier checks records only, not actual human confirmation.",
            "Graphify graph original source files and live browser profile are ephemeral synthetic.",
            "Existing P50 static scan may be PARTIAL for JS/SQL; no security certification.",
            "PDF raster smoke is automated only; client visual/layout review NOT_RUN.",
        ],
    }
    report = {
        "contract": CONTRACT,
        "subject_sha256": sha,
        "scope": "SYNTHETIC_ONLY",
        "run_status": "incomplete",
        "release_state": "HOLD",
        "customer_accepted": False,
        "security_certification": False,
        "counts": count,
        "coverage": coverage_totals,
        "finding_ids": finding_ids,
    }
    report["canonical_lines"] = canonical_lines(report, findings)
    output_files = {
        "audit.json": _json_bytes(audit),
        "coverage-ledger.json": _json_bytes({
            "contract": CONTRACT, "subject_sha256": sha, "units": coverage,
            "totals": coverage_totals, "run_status": "incomplete",
        }),
        "findings.json": _json_bytes({
            "contract": CONTRACT, "subject_sha256": sha, "findings": findings,
            "counts": count, "run_status": "incomplete",
        }),
        "report.json": _json_bytes(report),
        "report.html": _html_bytes(report["canonical_lines"], findings, coverage),
        "report.pdf": _pdf_bytes(report["canonical_lines"]),
    }
    manifest = {
        "contract": CONTRACT, "input_sha256": sha, "release_state": "HOLD",
        "files": {name: _digest(value) for name, value in output_files.items()},
    }
    root = validate_output_location(output_root)
    root.mkdir(parents=True, exist_ok=True)
    target = root / ("proofqa-p85-" + sha[:16])
    target.mkdir(exist_ok=False)
    # Partial process failure leaves an unmistakable manifest/integrity failure,
    # never a release-ready report; no existing directories/files overwritten.
    for name, content in (*output_files.items(), ("manifest.json", _json_bytes(manifest))):
        with (target / name).open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    return target
