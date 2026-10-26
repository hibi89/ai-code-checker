"""Self-contained offline Korean reports for deterministic Code Checker scans.

No API, scripts, external assets, customer-code execution or telemetry.
The legacy Gemini reporting.py remains unchanged.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

from code_input import InputError
from offline_core import LANGUAGE_SUFFIX, OfflineScan, scan_path
from review_models import CodeFinding


SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
COVERAGE_LABELS = {
    "analyzed": "Python AST 및 규칙 검사", "limited": "제한적 패턴 검사",
    "failed": "구문 분석 실패", "excluded": "정책상 제외",
    "unsupported": "언어·형식 미지원",
}
RULE_TITLES = (
    ("Python 구문 오류", "PY-SYNTAX"),
    ("동적 코드 실행 호출:", "PY-DYNAMIC-EXEC"),
    ("셸 명령을 문자열로 실행함", "PY-SHELL"),
    ("신뢰할 수 없는 데이터의 pickle 역직렬화 가능성", "PY-PICKLE"),
    ("SQL 질의 문자열을 동적으로 조합함", "PY-SQL-CONCAT"),
    ("TLS 인증서 검증을 비활성화함", "GEN-TLS-VERIFY"),
    ("비밀정보 형태의 값이 전송 전에 마스킹됨", "GEN-REDACT-SECRET"),
    ("개인정보 형태의 값이 전송 전에 마스킹됨", "GEN-REDACT-PII"),
)


@dataclass(frozen=True)
class ReportFinding:
    finding: CodeFinding
    rule_id: str
    verified: bool
    excerpt: str
    origin_path: str | None
    origin_line: int | None


@dataclass(frozen=True)
class OfflineReport:
    scan: OfflineScan
    findings: tuple[ReportFinding, ...]
    validation_issues: tuple[str, ...]

    @property
    def status(self) -> str:
        return "complete" if self.scan.status == "complete" and not self.validation_issues else "partial"

    @property
    def verified_count(self) -> int:
        return sum(item.verified for item in self.findings)


def _normalized(text: str) -> str:
    return " ".join(str(text).split())


def _rule_id(finding: CodeFinding) -> str:
    if finding.source != "static":
        return "UNSUPPORTED-SOURCE"
    for title, identifier in RULE_TITLES:
        if finding.title.startswith(title):
            return identifier
    return "LOCAL-UNREGISTERED"


def _validate_evidence(scan: OfflineScan, finding: CodeFinding) -> tuple[bool, str, str | None, int | None]:
    """Verify file, range, evidence against masked input, ignoring cached flag."""
    source = scan.bundle.file_map.get(finding.file_path)
    cover = next((item for item in scan.coverage if item.path == finding.file_path), None)
    if finding.source != "static" or source is None or cover is None:
        return False, "", None, None
    if cover.status not in {"analyzed", "limited", "failed"}:
        return False, "", None, None
    start, end = finding.start_line, finding.end_line
    if not isinstance(start, int) or isinstance(start, bool) or start < 1:
        return False, "", None, None
    if end is None:
        end = start
    if not isinstance(end, int) or isinstance(end, bool) or end < start:
        return False, "", None, None
    lines = source.text.splitlines()
    if end > len(lines):
        return False, "", None, None
    observed = _normalized("\n".join(lines[start - 1:end]))
    expected = _normalized(finding.evidence)
    if not observed or not expected or expected not in observed:
        return False, "", None, None
    origin = cover.origin
    return True, expected[:300], origin.container_path if origin else finding.file_path, (
        origin.source_line(start) if origin else start
    )


def build_report(scan: OfflineScan) -> OfflineReport:
    """Deduplicate candidate observations; mark unmatched citations as partial."""
    seen: set[tuple[object, ...]] = set()
    findings: list[ReportFinding] = []
    errors: list[str] = []
    for index, item in enumerate(scan.findings, 1):
        signature = (
            item.source, item.severity, item.title, item.file_path,
            item.start_line, item.end_line, _normalized(item.evidence),
        )
        if signature in seen:
            continue
        seen.add(signature)
        verified, excerpt, origin_path, origin_line = _validate_evidence(scan, item)
        if not verified:
            errors.append(f"발견 후보 {index}: 파일·줄·발췌 근거 대조 실패 (원문 인용 생략)")
        findings.append(ReportFinding(item, _rule_id(item), verified, excerpt, origin_path, origin_line))
    findings.sort(key=lambda row: (
        SEVERITY_ORDER.get(row.finding.severity, 9),
        row.finding.file_path.casefold(), row.finding.start_line or 0, row.rule_id,
    ))
    return OfflineReport(scan, tuple(findings), tuple(errors))


def _plain(value: object) -> str:
    return " ".join(str(value).replace("\r", " ").splitlines()).strip()


def _h(value: object) -> str:
    return html.escape(_plain(value), quote=True)


def _m(value: object) -> str:
    """Escape Markdown punctuation and HTML, including code-span delimiters."""
    safe = html.escape(_plain(value), quote=True)
    return re.sub(r"([\\\x60*_{}\[\]()#+.!|>~-])", r"\\\1", safe)


def _location(row: ReportFinding) -> str:
    f = row.finding
    path = f"{f.file_path}:{f.start_line if f.start_line is not None else '?'}"
    if row.verified and row.origin_path is not None:
        origin = f"{row.origin_path}:{row.origin_line}"
        if origin != path:
            path += f" (원본 {origin})"
    return path


def render_markdown(report: OfflineReport) -> str:
    counts = report.scan.counts
    lines = [
        "# 코드체커 오프라인 진단 보고서", "",
        f"- 보고서 상태: {_m(report.status)}",
        f"- 검사 상태: {_m(report.scan.status)}",
        f"- 입력 유형: {_m(report.scan.input_kind)}",
        f"- 발견 후보: {len(report.findings)}개 (근거 일치 {report.verified_count}개)",
        f"- 파일: 발견 {counts['enumerated']} / Python 분석 {counts['analyzed']} / 제한 {counts['limited']} / 실패 {counts['failed']} / 제외 {counts['excluded']} / 미지원 {counts['unsupported']}",
        "- 방식: 로컬 정적 규칙과 Python AST. AI 호출·코드 실행 없음.", "",
        "> complete는 입력 처리 상태이지 소프트웨어 안전성이나 결함 부재 보장이 아닙니다.", "",
        "## 파일별 검사 범위", "",
        "| 파일 | 상태 | 분석기 | 사유 |", "|---|---|---|---|",
    ]
    for item in sorted(report.scan.coverage, key=lambda x: x.path.casefold()):
        lines.append(
            f"| {_m(item.path)} | {_m(COVERAGE_LABELS.get(item.status, item.status))} "
            f"| {_m(item.analyzer)} | {_m(item.reason)} |"
        )
    lines.extend(["", "## 위험 후보", ""])
    if not report.findings:
        lines.append("적용 규칙에 일치한 후보가 없습니다. 안전하다는 의미는 아닙니다.")
    for index, row in enumerate(report.findings, 1):
        finding = row.finding
        lines.extend([
            f"### {index}. [{_m(finding.severity)}] {_m(finding.title)}", "",
            f"- 규칙 ID: {_m(row.rule_id)}",
            f"- 위치: {_m(_location(row))}",
            f"- 근거: {'일치(발견 위치만 검증)' if row.verified else '대조 실패 — 사람 확인 필요'}",
            f"- 영향 가능성: {_m(finding.impact)}",
            f"- 수정/확인 권고: {_m(finding.recommendation)}",
        ])
        if row.verified:
            lines.append(f"- 마스킹 발췌: {_m(row.excerpt)}")
        lines.extend(["- 주의: 규칙 일치는 실제 취약점 증명이 아닙니다.", ""])
    if report.validation_issues:
        lines.extend(["## 근거 대조 실패", ""])
        lines.extend("- " + _m(issue) for issue in report.validation_issues)
        lines.extend(["- 추가 확인 없이 납품 완료로 처리하지 마세요.", ""])
    if report.scan.warnings:
        lines.extend(["## 입력 경고", ""])
        lines.extend("- " + _m(warning) for warning in report.scan.warnings)
        lines.append("")
    lines.extend([
        "## 한계 및 보관", "",
        "- 미지원·제외·실패·제한적 검사 파일은 완전하게 분석하지 않았습니다.",
        "- JS/TS는 전용 의미 분석이 아닌 일반 패턴만 적용됩니다.",
        "- 코드 실행, 테스트, 침투 테스트, 런타임 안정성은 평가하지 않았습니다.",
        "- 보고서에 마스킹된 소스 발췌가 포함되므로 로컬 보관/삭제를 직접 관리하세요.",
        "- HTML을 브라우저에서 열어 인쇄 → PDF 저장을 사용하세요.", "",
    ])
    return "\n".join(lines)


def render_html(report: OfflineReport) -> str:
    counts = report.scan.counts
    rows = "".join(
        "<tr><td>" + _h(item.path) + "</td><td>"
        + _h(COVERAGE_LABELS.get(item.status, item.status)) + "</td><td>"
        + _h(item.analyzer) + "</td><td>" + _h(item.reason) + "</td></tr>"
        for item in sorted(report.scan.coverage, key=lambda x: x.path.casefold())
    )
    findings: list[str] = []
    for index, row in enumerate(report.findings, 1):
        item = row.finding
        excerpt = "<p><strong>마스킹 발췌:</strong> <code>" + _h(row.excerpt) + "</code></p>" if row.verified else ""
        findings.append(
            "<article><h3>" + str(index) + ". [" + _h(item.severity) + "] " + _h(item.title) + "</h3>"
            + "<p><strong>규칙:</strong> " + _h(row.rule_id) + " / <strong>위치:</strong> "
            + _h(_location(row)) + "</p><p><strong>근거:</strong> "
            + ("일치(발견 위치만 검증)" if row.verified else "대조 실패 — 사람 확인 필요")
            + "</p><p><strong>영향 가능성:</strong> " + _h(item.impact)
            + "</p><p><strong>수정/확인 권고:</strong> " + _h(item.recommendation)
            + "</p>" + excerpt + "<p class='small'>규칙 일치는 실제 취약점 증명이 아닙니다.</p></article>"
        )
    def items(values: tuple[str, ...] | list[str]) -> str:
        return "<ul>" + "".join("<li>" + _h(value) + "</li>" for value in values) + "</ul>"

    problems = (
        "<section><h2>근거 대조 실패</h2>" + items(report.validation_issues)
        + "<p>사람이 추가 확인하기 전에는 납품 완료로 처리하지 마세요.</p></section>"
        if report.validation_issues else ""
    )
    warnings = (
        "<section><h2>입력 경고</h2>" + items(report.scan.warnings) + "</section>"
        if report.scan.warnings else ""
    )
    cards = "".join(findings) if findings else "<p>적용 규칙에 일치한 후보가 없습니다. 안전 판정은 아닙니다.</p>"
    return (
        "<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none';"
        "style-src 'unsafe-inline'; img-src 'none'; script-src 'none'; "
        "object-src 'none'; form-action 'none'; base-uri 'none'\">"
        "<title>코드체커 오프라인 보고서</title>"
        "<style>body{font-family:system-ui,sans-serif;max-width:960px;margin:auto;"
        "padding:2rem;line-height:1.6;color:#152238}article{border:1px solid #b8c5d3;"
        "border-radius:8px;padding:1rem;margin:1rem 0}table{width:100%;border-collapse:collapse}"
        "th,td{border:1px solid #b8c5d3;padding:.45rem;text-align:left;overflow-wrap:anywhere}"
        "code{white-space:pre-wrap;overflow-wrap:anywhere}.small{color:#465567;font-size:.9rem}"
        "@media print{body{padding:0}article{break-inside:avoid}}</style></head><body>"
        "<h1>코드체커 오프라인 진단 보고서</h1><p>보고서 상태: <strong>"
        + _h(report.status) + "</strong> / 검사 상태: " + _h(report.scan.status)
        + " / 유형: " + _h(report.scan.input_kind) + "</p>"
        + "<p>발견 후보 " + str(len(report.findings)) + "건 (근거 일치 "
        + str(report.verified_count) + "건) / 파일 " + str(counts["enumerated"])
        + " / Python 분석 " + str(counts["analyzed"]) + " / 제한 " + str(counts["limited"])
        + " / 실패 " + str(counts["failed"]) + " / 제외 " + str(counts["excluded"])
        + " / 미지원 " + str(counts["unsupported"]) + "</p>"
        "<p class='small'>오프라인 정적 분석만 수행. complete도 안전성·무결점 보증이 아닙니다.</p>"
        "<section><h2>파일별 검사 범위</h2><table><thead><tr><th>파일</th>"
        "<th>상태</th><th>분석기</th><th>사유</th></tr></thead><tbody>"
        + rows + "</tbody></table></section><section><h2>위험 후보</h2>"
        + cards + "</section>" + problems + warnings
        + "<section><h2>한계 및 보관</h2><ul>"
        "<li>미지원·제외·실패·제한 검사 파일은 분석 범위가 제한됩니다.</li>"
        "<li>코드를 실행하거나 런타임·침투 테스트를 진행하지 않았습니다.</li>"
        "<li>JS/TS 전용 분석기는 아직 없습니다.</li>"
        "<li>보고서는 민감한 발췌가 있을 수 있으므로 로컬 보관·삭제를 관리하세요.</li>"
        "<li>PDF 저장은 브라우저 인쇄 기능을 사용하세요.</li>"
        "</ul></section></body></html>\n"
    )


def write_report(report: OfflineReport, output_dir: str | Path, *, name: str = "code-checker-report") -> tuple[Path, Path]:
    """Atomic no-overwrite publish via hard link; fail closed if unavailable."""
    if not 1 <= len(name) <= 80 or name.startswith(".") or name in {".", ".."} or any(
        not (char.isalnum() or char in "._-") for char in name
    ):
        raise InputError("보고서 이름이 허용 형식이 아닙니다.")
    folder = Path(output_dir).expanduser()
    if folder.is_symlink():
        raise InputError("심볼릭 링크 폴더로 보고서를 출력하지 않습니다.")
    folder.mkdir(parents=True, exist_ok=True)
    if not folder.is_dir():
        raise InputError("보고서 저장 위치가 폴더가 아닙니다.")
    paths = (folder / (name + ".html"), folder / (name + ".md"))
    if any(path.exists() or path.is_symlink() for path in paths):
        raise FileExistsError("기존 보고서 덮어쓰기를 거부했습니다.")
    temps: list[Path] = []
    linked: list[Path] = []
    try:
        for path, data in zip(paths, (render_html(report), render_markdown(report))):
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="\n", dir=folder,
                prefix="." + path.name + "-", suffix=".tmp", delete=False,
            ) as file:
                temps.append(Path(file.name))
                file.write(data)
                file.flush()
                os.fsync(file.fileno())
        for temp, path in zip(temps, paths):
            os.link(temp, path)
            linked.append(path)
    except BaseException:
        for path in linked:
            path.unlink(missing_ok=True)
        raise
    finally:
        for temp in temps:
            temp.unlink(missing_ok=True)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="API 없는 코드체커 HTML·Markdown 보고서")
    parser.add_argument("source", help="파일, TXT, ZIP 또는 폴더")
    parser.add_argument("--language", choices=tuple(LANGUAGE_SUFFIX))
    parser.add_argument("--output-dir", default="reports")
    parser.add_argument("--name", default="code-checker-report")
    args = parser.parse_args()
    try:
        report = build_report(scan_path(args.source, language=args.language))
        html_path, markdown_path = write_report(report, args.output_dir, name=args.name)
    except (InputError, OSError, ValueError) as error:
        print(json.dumps({"status": "blocked", "error": type(error).__name__}, ensure_ascii=False))
        return 2
    print(json.dumps({
        "status": report.status, "scan_status": report.scan.status,
        "findings": len(report.findings), "verified": report.verified_count,
        "html": str(html_path), "markdown": str(markdown_path),
    }, ensure_ascii=False, indent=2))
    return 0 if report.status == "complete" else 3


if __name__ == "__main__":
    raise SystemExit(main())
