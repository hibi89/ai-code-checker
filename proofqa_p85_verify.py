"""Separate read-only P85 delivery verifier.

Independently interprets JSON, validates counts/coverage/approvals and compares
the canonical text extracted from the actual PDF and HTML. It does not import
the P85 composer and does not certify vulnerabilities or customer acceptance.
"""
from __future__ import annotations

import hashlib
import html
import io
import json
import re
from pathlib import Path
from typing import Any

from code_input import InputError

CONTRACT = "proofqa.p85.audit.v1"
FILES = frozenset({
    "audit.json", "coverage-ledger.json", "findings.json", "report.json",
    "report.html", "report.pdf", "manifest.json",
})
PHASES = (
    "reconnaissance", "coverage_led_hunting", "candidate_validation",
    "structured_output", "independent_record_verification",
    "target_neutral_reporting",
)
COVERED = frozenset({
    "p50_static_candidates", "p70_python_ast", "p70_javascript_ast",
    "p70_sql_ast", "p70_finding_graph_links", "p70_browser_dom",
    "p70_http_200_500", "p70_save_reopen",
})
UNCOVERED = frozenset({
    "raw_graph_independent_replay", "independent_human_verifier",
    "authorized_customer_staging", "windows10_11_real_device",
    "os_enforced_network_sandbox", "manual_pdf_visual_review",
})
HEX64 = re.compile("^[a-f0-9]{64}$")
IDS = re.compile("^PQ85-[0-9]{3}$")
REFS = frozenset({"EV-CHECKER", "EV-GRAPH", "EV-BROWSER"})
MAX_BYTES = {"audit.json": 65536, "coverage-ledger.json": 65536,
             "findings.json": 65536, "report.json": 65536,
             "report.html": 256000, "report.pdf": 1024 * 1024,
             "manifest.json": 65536}


def reject(message: str) -> None:
    raise InputError("P85 독립 납품 계약 검증 거부: " + message)


def read_files(path: str | Path) -> dict[str, bytes]:
    directory = Path(path)
    if not directory.is_dir() or directory.is_symlink():
        reject("납품 디렉터리가 일반 디렉터리가 아닙니다.")
    names = set(p.name for p in directory.iterdir())
    if names != FILES:
        reject("누락/추가된 파일이 있거나 예상 집합과 다릅니다.")
    data = {}
    for name in sorted(FILES):
        item = directory / name
        if not item.is_file() or item.is_symlink() or item.stat().st_size > MAX_BYTES[name]:
            reject("이상한 파일 타입/심볼릭링크/크기: " + name)
        data[name] = item.read_bytes()
        if len(data[name]) > MAX_BYTES[name]:
            reject("읽기 중 용량 초과: " + name)
    return data


def _load(data: bytes, name: str) -> dict[str, Any]:
    try:
        result = json.loads(data.decode("utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise InputError("JSON 파싱 거부: " + name) from exc
    if not isinstance(result, dict):
        reject("JSON 최상위는 객체여야 합니다: " + name)
    return result


def _hex(value: Any) -> bool:
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def _counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    expected = ("CONFIRMED", "NEEDS_VALIDATION", "REJECTED", "NOT_COVERED")
    return {
        "total": len(rows),
        "confirmed": sum(r["status"] == expected[0] for r in rows),
        "needs_validation": sum(r["status"] == expected[1] for r in rows),
        "rejected": sum(r["status"] == expected[2] for r in rows),
        "not_covered": sum(r["status"] == expected[3] for r in rows),
    }


def _expected_lines(report: dict[str, Any], rows: list[dict[str, Any]]) -> list[str]:
    coverage = report["coverage"]
    counts = report["counts"]
    lines = [
        "PROOFQA AX P85 SYNTHETIC REPORT",
        "CONTRACT: " + CONTRACT,
        "SUBJECT_SHA256: " + report["subject_sha256"],
        "CASE_SOURCE: SYNTHETIC_ONLY",
        "RUN_STATUS: incomplete",
        "COVERAGE: planned={planned} completed={completed} not_covered={not_covered}".format(**coverage),
        "FINDINGS: total={total} confirmed={confirmed} needs_validation={needs_validation} rejected={rejected} not_covered={not_covered}".format(**counts),
    ]
    for row in rows:
        lines.append("FINDING {id} STATUS {status} EVIDENCE {refs}".format(
            id=row["id"], status=row["status"], refs=",".join(row["evidence_refs"])
        ))
    lines.extend([
        "VERIFIER: code_contract_only; fresh_agent=NOT_RUN",
        "SECURITY_CERTIFICATION: FALSE",
        "CUSTOMER_ACCEPTED: FALSE",
        "RELEASE: HOLD",
    ])
    return lines


def verify_package(path: str | Path, schema_path: str | Path | None = None) -> dict[str, Any]:
    data = read_files(path)
    jsons = {
        name: _load(data[name], name)
        for name in ("audit.json", "coverage-ledger.json", "findings.json", "report.json", "manifest.json")
    }
    audit, ledger, findings, report, manifest = (
        jsons["audit.json"], jsons["coverage-ledger.json"], jsons["findings.json"],
        jsons["report.json"], jsons["manifest.json"],
    )
    if any(doc.get("contract") != CONTRACT for doc in jsons.values()):
        reject("서로 다른 계약 버전.")
    if (manifest.get("release_state") != "HOLD"
            or audit.get("release_state") != "HOLD"
            or report.get("release_state") != "HOLD"
            or report.get("run_status") != "incomplete"
            or audit.get("run_status") != "incomplete"
            or ledger.get("run_status") != "incomplete"
            or findings.get("run_status") != "incomplete"
            or audit.get("schema_version") != 1
            or audit.get("scope") != "SYNTHETIC_ONLY"
            or report.get("scope") != "SYNTHETIC_ONLY"
            or report.get("customer_accepted") is not False
            or report.get("security_certification") is not False):
        reject("실제 인수/판매/정식 인증으로 잘못 표시할 수 있는 값.")
    sha = report.get("subject_sha256")
    if not _hex(sha) or any(doc.get("subject_sha256") != sha for doc in (audit, ledger, findings)) or manifest.get("input_sha256") != sha:
        reject("케이스의 원본 SHA256 일치 실패.")
    hashed = manifest.get("files")
    if not isinstance(hashed, dict) or set(hashed) != (FILES - {"manifest.json"}):
        reject("매니페스트 파일 집합 오류.")
    for name, expected in hashed.items():
        if not _hex(expected) or hashlib.sha256(data[name]).hexdigest() != expected:
            reject("원본 바이트 digest 불일치: " + name)

    phases = audit.get("phases")
    if (not isinstance(phases, list) or len(phases) != len(PHASES)
            or [p.get("id") for p in phases if isinstance(p, dict)] != list(PHASES)
            or any(not isinstance(p.get("state"), str) for p in phases)):
        reject("6단계 순서/상태 누락.")
    if phases[4]["state"] != "CODE_ONLY_FRESH_AGENT_NOT_RUN":
        reject("실제 독립 인간·agent 검증을 실행했다고 오인할 수 없습니다.")
    if audit.get("independent_human_security_verification") != "NOT_RUN":
        reject("실 독립 보안 검증 허위 표기.")
    arch = audit.get("architecture")
    if (not isinstance(arch, dict) or arch.get("customer_code_executed") is not False
            or arch.get("external_llm_called") is not False
            or arch.get("os_enforced_egress_sandbox") is not False
            or not isinstance(arch.get("trust_boundaries"), list)):
        reject("실행 및 네트워크 경계에 허위 주장.")
    evidence = audit.get("evidence")
    if (not isinstance(evidence, list) or len(evidence) != 3
            or {x.get("id") for x in evidence if isinstance(x, dict)} != REFS
            or any(not _hex(x.get("sha256")) or x.get("observed") is not True
                   for x in evidence)):
        reject("기계 증거 참조 무결성 오류.")
    source_record = next(x for x in evidence if x["id"] == "EV-CHECKER")
    if not _hex(source_record.get("source_file_sha256")):
        reject("P50 소스 파일 해시 앵커가 없습니다.")
    units = ledger.get("units")
    if not isinstance(units, list) or len(units) != len(COVERED | UNCOVERED):
        reject("Coverage Ledger 항목 수 오류.")
    ids = [x.get("id") for x in units if isinstance(x, dict)]
    if len(ids) != len(units) or set(ids) != (COVERED | UNCOVERED) or len(ids) != len(set(ids)):
        reject("Coverage Ledger 중복/누락/비등록 단위.")
    for unit in units:
        should = "COMPLETED" if unit["id"] in COVERED else "NOT_COVERED"
        if (unit.get("status") != should or unit.get("scope") != "SYNTHETIC"
                or unit.get("reviewed_customer") is not False):
            reject("Coverage Ledger의 검증 범위 허위 승격.")
    totals = {"planned": len(units),
              "completed": sum(x["status"] == "COMPLETED" for x in units),
              "not_covered": sum(x["status"] == "NOT_COVERED" for x in units)}
    if totals["planned"] != totals["completed"] + totals["not_covered"]:
        reject("Coverage 총합 오류.")
    if ledger.get("totals") != totals or audit.get("coverage") != totals or report.get("coverage") != totals:
        reject("Coverage 세 문서 수량 불일치.")
    rows = findings.get("findings")
    if not isinstance(rows, list) or not 2 <= len(rows) <= 12:
        reject("Finding 개수 오류.")
    identifiers = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not IDS.fullmatch(row["id"]):
            reject("finding id 형식 오류.")
        identifiers.append(row["id"])
        if (row.get("status") != "NEEDS_VALIDATION"
                or row.get("severity") is not None
                or row.get("category") != "static_candidate"
                or row.get("source_path") != "app.py"
                or not isinstance(row.get("source_finding_index"), int)
                or row["source_finding_index"] < 0
                or not isinstance(row.get("line"), int) or row["line"] < 1
                or not _hex(row.get("source_sha256"))
                or row.get("source_sha256") != source_record["source_file_sha256"]
                or not _hex(row.get("fingerprint"))
                or row.get("evidence_refs") != ["EV-CHECKER", "EV-GRAPH"]
                or not isinstance(row.get("unresolved_fact"), str)
                or len(row["unresolved_fact"]) < 20
                or row.get("customer_scope_approved") is not False
                or row.get("verified_by_fresh_independent_agent") is not False):
            reject("확정되지 않은 후보/심각도/근거의 허위 상태.")
    indices = [row["source_finding_index"] for row in rows]
    if len(indices) != len(set(indices)) or indices != sorted(indices):
        reject("CodeChecker 원래 후보 식별자 중복/역순.")
    for row in rows:
        raw = (sha + "|" + row["source_path"] + "|" + str(row["line"]) + "|" + str(row["source_finding_index"])).encode("utf-8")
        if row["fingerprint"] != hashlib.sha256(raw).hexdigest():
            reject("독립 후보 fingerprint와 원래 소스 SHA/라인 연결 실패.")
    if len(identifiers) != len(set(identifiers)):
        reject("중복 후보 식별자.")
    actual_counts = _counts(rows)
    if (findings.get("counts") != actual_counts
            or audit.get("finding_counts") != actual_counts
            or report.get("counts") != actual_counts
            or report.get("finding_ids") != identifiers):
        reject("결과물 간 Findings 수치/순서 불일치.")
    canonical = _expected_lines(report, rows)
    if report.get("canonical_lines") != canonical:
        reject("JSON canonical report의 결과 수치/증거 정합성 오류.")
    try:
        html_text = data["report.html"].decode("utf-8")
    except UnicodeError as exc:
        raise InputError("HTML UTF-8 위반.") from exc
    if re.search(r"<\s*(?:script|iframe|object|embed|form|base|meta\s+http-equiv\s*=\s*['\"]refresh)", html_text, re.I):
        # A strict CSP meta tag is permitted (no refresh).
        reject("HTML 실행 가능 태그/리다이렉션.")
    if not re.search(r"default-src 'none'", html_text):
        reject("HTML CSP 거부.")
    match = re.search(r'<pre id="canonical">(.*?)</pre>', html_text, re.S)
    if match is None or html.unescape(match.group(1)) != "\n".join(canonical):
        reject("HTML과 구조화된 JSON의 정규 텍스트가 다릅니다.")
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data["report.pdf"]), strict=True)
        if len(reader.pages) < 1 or len(reader.pages) > 3:
            reject("PDF 페이지 수 오류.")
        root = reader.trailer["/Root"]
        if "/OpenAction" in root or "/AA" in root:
            reject("PDF 실행 동작 차단.")
        extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
    except ImportError as exc:
        raise InputError("독립 PDF 검증에 pypdf 설치 필요.") from exc
    except Exception as exc:
        raise InputError("PDF 파싱/본문 추출 실패.") from exc
    text_lines = [x.strip() for x in extracted.splitlines() if x.strip()]
    position = 0
    for expected in canonical:
        # pypdf also extracts the visible title and Korean subtitle; canonical
        # machine-readable evidence must appear in the correct order exactly.
        while position < len(text_lines) and text_lines[position] != expected:
            position += 1
        if position == len(text_lines):
            reject("PDF 텍스트와 JSON finding/coverage 불일치: " + expected[:60])
        position += 1
    if schema_path is not None:
        try:
            from jsonschema import Draft202012Validator
            schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            Draft202012Validator(schema).validate(report)
        except ImportError as exc:
            raise InputError("P85 전용 jsonschema 설치 필요.") from exc
        except Exception as exc:
            raise InputError("독립 Report JSON Schema 위반.") from exc
    return {
        "contract": CONTRACT, "verified": True,
        "scope": "SYNTHETIC_ONLY", "pdf_pages": len(reader.pages),
        "coverage": totals, "findings": actual_counts,
        "independent_verifier": "SEPARATE_READ_ONLY_CODE_PATH",
        "fresh_human_or_agent_verifier": "NOT_RUN",
        "release_state": "HOLD",
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="P85 read-only internal verifier (no customer certification)")
    parser.add_argument("report_folder")
    parser.add_argument("--schema", default="schemas/proofqa_p85_report.schema.json")
    args = parser.parse_args()
    try:
        result = verify_package(args.report_folder, args.schema)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    except (InputError, OSError, ValueError) as exc:
        parser.exit(2, "P85 HOLD: " + str(exc) + "\n")
