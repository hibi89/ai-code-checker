"""Evidence checking and Korean Markdown report rendering."""

from __future__ import annotations

import html
import re
from datetime import datetime, timezone

from code_input import CodeBundle
from review_models import AIReview, AIReviewFinding, CodeFinding, TokenUsage


SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
PERSPECTIVE_LABELS = {
    "security": "보안",
    "reliability": "신뢰성",
    "testing": "테스트",
    "architecture": "구조",
    "maintainability": "유지보수",
    "performance": "성능",
    "resource_use": "자원관리",
    "complexity_cost": "복잡도·비용",
}
STATUS_LABELS = {
    "issue_found": "문제 후보 확인",
    "no_clear_issue": "명확한 문제 후보 없음",
    "not_enough_context": "맥락 부족",
}


def _safe_text(value: str) -> str:
    text = " ".join(str(value).replace("\r", "\n").splitlines()).strip()
    return html.escape(text, quote=False).replace("`", "&#96;").replace("|", "&#124;")


def _safe_code(value: str) -> str:
    return str(value).replace("`", "&#96;").replace("\r", " ").replace("\n", " ")


def _normalize_excerpt(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def verify_ai_citation(item: AIReviewFinding, bundle: CodeBundle) -> bool:
    source = bundle.file_map.get(item.file_path)
    if source is None or item.start_line is None or not item.evidence.strip():
        return False
    end_line = item.end_line if item.end_line is not None else item.start_line
    if item.start_line < 1 or end_line < item.start_line or end_line > source.line_count:
        return False
    lines = source.text.splitlines()
    reported = "\n".join(lines[item.start_line - 1:end_line])
    evidence = _normalize_excerpt(item.evidence)
    return bool(evidence and evidence in _normalize_excerpt(reported))


def convert_ai_findings(review: AIReview, bundle: CodeBundle) -> list[CodeFinding]:
    results: list[CodeFinding] = []
    for item in review.findings:
        citation_verified = verify_ai_citation(item, bundle)
        results.append(CodeFinding(
            severity=item.severity,
            perspective=item.perspective,
            title=item.title,
            file_path=item.file_path,
            start_line=item.start_line,
            end_line=item.end_line,
            evidence=item.evidence,
            impact=item.impact,
            recommendation=item.recommendation,
            confidence=item.confidence,
            source="ai",
            citation_verified=citation_verified,
        ))
    return results


def _sorted(findings: list[CodeFinding]) -> list[CodeFinding]:
    return sorted(
        findings,
        key=lambda item: (
            SEVERITY_ORDER.get(item.severity, 9),
            (item.file_path or "").casefold(),
            item.start_line or 0,
            item.source,
        ),
    )


def render_report(
    *,
    bundle: CodeBundle,
    static_findings: list[CodeFinding],
    ai_review: AIReview,
    ai_findings: list[CodeFinding],
    usage: TokenUsage,
    preflight_cost_usd: float,
    cost_limit_usd: float,
    usage_warnings: list[str] | None = None,
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    findings = _sorted(static_findings + ai_findings)
    check_map = {item.perspective: item for item in ai_review.checks}
    warnings = list(bundle.warnings) + list(usage_warnings or [])

    lines = [
        "# AI 보조 코드 검수 리포트",
        "",
        f"- 생성 시각: {now}",
        f"- 분석 파일: {len(bundle.files)}개 / {bundle.source_bytes:,} bytes",
        f"- 제외 파일: {len(bundle.excluded_paths)}개",
        "- 분석 방식: 로컬 정적 검사 + Gemini 단일 분석 호출",
        "- 코드 실행·의존성 설치: 하지 않음",
        "",
        "> 이 결과는 AI 보조 검수입니다. 취약점 부재나 정상 동작을 보증하지 않습니다. AI 항목은 코드 발췌가 원본에 있는지 별도로 표시하며, 발췌 일치가 결함 자체를 증명하지는 않습니다.",
        "",
        "## 요약",
        "",
        _safe_text(ai_review.summary) or "요약이 제공되지 않았습니다.",
        "",
        "## 점검 범위",
        "",
        "| 관점 | 결과 | 요약 |",
        "|---|---|---|",
    ]

    for perspective, label in PERSPECTIVE_LABELS.items():
        check = check_map.get(perspective)
        if check is None:
            status = "결과 누락"
            summary = "AI 응답에서 이 관점의 확인 결과가 빠졌습니다."
        else:
            status = STATUS_LABELS[check.status]
            summary = _safe_text(check.summary)
        lines.append(f"| {label} | {status} | {summary} |")

    lines.extend(["", "## 발견 항목", ""])
    if not findings:
        lines.append("현재 입력 범위에서 명확한 문제 후보를 찾지 못했습니다. 이는 결함이나 취약점이 없다는 뜻은 아닙니다.")
    else:
        for index, item in enumerate(findings, start=1):
            citation = "로컬 검사 근거" if item.source == "static" else (
                "원본 경로·줄·발췌 일치" if item.citation_verified else "원본 대조 실패 — 사람 확인 필요"
            )
            location = f"`{_safe_code(item.file_path or '경로 미확인')}`"
            if item.start_line is not None:
                location += f" L{item.start_line}"
                if item.end_line is not None and item.end_line != item.start_line:
                    location += f"–L{item.end_line}"
            lines.extend([
                f"### {index}. [{item.severity}] {_safe_text(item.title)}",
                "",
                f"- 관점: {PERSPECTIVE_LABELS.get(item.perspective, item.perspective)}",
                f"- 위치: {location}",
                f"- 근거 상태: {citation}",
                f"- 신뢰도: {item.confidence}% (AI 추정치)",
                f"- 영향: {_safe_text(item.impact)}",
                f"- 권고: {_safe_text(item.recommendation)}",
            ])
            if item.evidence:
                lines.append(f"- 발췌: `{_safe_code(item.evidence[:300])}`")
            if item.source == "ai":
                lines.append("- 검토 상태: AI가 제시한 후보입니다. 실제 결함 여부는 원본 코드와 실행 맥락을 사람이 확인해야 합니다.")
            lines.append("")

    lines.extend(["## 확인 한계", ""])
    limitations = list(ai_review.limitations)
    limitations.extend([
        "이 도구는 코드를 실행하거나 테스트를 돌리지 않았습니다.",
        "이 도구는 침투 테스트, 보안 인증, 무결점 보증을 제공하지 않습니다.",
        "지원하지 않는 형식과 제외 파일은 AI 검수 범위에 들어가지 않았습니다.",
        "AI의 경로·줄·발췌 일치는 인용 위치 확인일 뿐, 결함 판정의 정확성 확인은 아닙니다.",
    ])
    for limitation in dict.fromkeys(limitations):
        lines.append(f"- {_safe_text(limitation)}")

    lines.extend(["", "## 사용량 및 예상 원가", ""])
    input_tokens = "확인 불가" if usage.input_tokens is None else f"{usage.input_tokens:,}"
    output_tokens = "확인 불가" if usage.output_tokens is None else f"{usage.output_tokens:,}"
    total_tokens = "확인 불가" if usage.total_tokens is None else f"{usage.total_tokens:,}"
    cost = "확인 불가" if usage.estimated_cost_usd is None else f"${usage.estimated_cost_usd:.6f} USD"
    lines.extend([
        f"- 모델: `{_safe_code(usage.model)}`",
        f"- Gemini 분석 호출: {usage.request_count}회",
        f"- 입력/출력/전체 토큰: {input_tokens} / {output_tokens} / {total_tokens}",
        f"- AI 호출 처리 시간: {'확인 불가' if usage.duration_ms is None else f'{usage.duration_ms:,} ms'}",
        f"- 목록 단가 기준 예상 API 원가: {cost}",
        f"- 호출 전 상한 추정: ${preflight_cost_usd:.6f} USD / 설정 한도 ${cost_limit_usd:.4f} USD",
        "- 예상 원가는 Google 청구서 금액이 아닙니다. 무료 할당량, 환율, 세금, 가격 변경은 반영하지 않았습니다.",
    ])

    if warnings:
        lines.extend(["", "## 주의 사항", ""])
        for warning in dict.fromkeys(warnings):
            lines.append(f"- {_safe_text(warning)}")

    lines.append("")
    return "\n".join(lines)
