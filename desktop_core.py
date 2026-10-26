"""Headless desktop workflow used by the Windows GUI.

Only local safe input readers, deterministic scanner and offline reporters are
called. Keeping this layer separate from Tk enables Windows/Linux CI tests
without a display, API key or external network access.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from code_input import InputError, bundle_from_text, load_path
from offline_core import OFFLINE_LIMITS, _split_delimited_txt, scan_path, scan_text
from offline_report import build_report, write_report


@dataclass(frozen=True)
class ScanRequest:
    mode: Literal["path", "paste"]
    source: str = ""
    text: str = ""
    language: str | None = None


@dataclass(frozen=True)
class InputPreview:
    kind: str
    files: int
    excluded: int
    bytes: int
    lines: int
    paths: tuple[str, ...]
    warnings: tuple[str, ...]

    def display(self) -> str:
        summary = (
            f"입력 종류: {self.kind}\n"
            f"분석 후보 파일: {self.files}개 / 제외·미지원: {self.excluded}개\n"
            f"읽은 자료: {self.bytes:,} bytes / {self.lines:,}줄\n"
        )
        if self.paths:
            summary += "파일 예시:\n" + "\n".join("  " + item for item in self.paths[:12]) + "\n"
            if len(self.paths) > 12:
                summary += f"  외 {len(self.paths) - 12}개\n"
        if self.warnings:
            summary += f"경고: {len(self.warnings)}건 (자세한 내용은 검사 결과 보고서 참조)\n"
        return summary + "미리보기는 파일 읽기·필터 검증이며 정적 코드 검사는 실행하지 않습니다."


@dataclass(frozen=True)
class ScanResult:
    status: Literal["complete", "partial"]
    files: int
    analyzed: int
    limited: int
    failed: int
    excluded: int
    unsupported: int
    findings: int
    verified: int
    html_path: Path
    markdown_path: Path

    def display(self) -> str:
        return (
            f"보고서 상태: {self.status}\n"
            f"발견 {self.files}개 / Python 분석 {self.analyzed}개 / 제한 {self.limited}개 / "
            f"실패 {self.failed}개 / 제외 {self.excluded}개 / 미지원 {self.unsupported}개\n"
            f"위험 후보 {self.findings}건 / 근거 일치 {self.verified}건\n"
            f"HTML: {self.html_path.name}\nMarkdown: {self.markdown_path.name}\n"
            "complete도 코드의 안전성을 보증하지 않습니다."
        )


def _validate_request(request: ScanRequest) -> None:
    if request.mode not in {"path", "paste"}:
        raise InputError("입력 모드가 유효하지 않습니다.")
    if request.language not in {None, "python", "javascript", "typescript"}:
        raise InputError("지원하지 않는 언어 선택입니다.")
    if request.mode == "path":
        if not request.source or not request.source.strip():
            raise InputError("검사할 파일·ZIP 또는 폴더를 선택하세요.")
        if request.language and Path(request.source).suffix.lower() != ".txt":
            raise InputError("언어 선택은 단일 TXT 또는 붙여넣기에서만 사용합니다.")
    else:
        if not request.text.strip():
            raise InputError("붙여넣기 영역에 코드를 입력하세요.")


def _base_bundle(request: ScanRequest):
    _validate_request(request)
    if request.mode == "paste":
        return bundle_from_text(request.text, filename="pasted.txt", limits=OFFLINE_LIMITS), "paste"
    candidate = Path(request.source).expanduser()
    kind = "folder" if candidate.is_dir() else (
        "zip" if candidate.suffix.lower() == ".zip" else (
            "txt" if candidate.suffix.lower() == ".txt" else "file"
        )
    )
    return load_path(candidate, OFFLINE_LIMITS), kind


def inspect_input(request: ScanRequest) -> InputPreview:
    """Read and inventory eligible inputs, but DO NOT execute static checks."""
    bundle, kind = _base_bundle(request)
    if kind in {"paste", "txt"} and len(bundle.files) == 1:
        parsed = _split_delimited_txt(bundle.files[0], limits=OFFLINE_LIMITS)
        if parsed is not None:
            if request.language is not None:
                raise InputError("통합 TXT는 파일별 확장자를 사용하므로 언어 자동을 선택하세요.")
            bundle, _origins, additional = parsed
            return InputPreview(
                "multi-txt", len(bundle.files), len(additional) + len(bundle.excluded_paths),
                bundle.source_bytes, sum(item.line_count for item in bundle.files),
                tuple(item.path for item in bundle.files), tuple(bundle.warnings),
            )
    return InputPreview(
        kind, len(bundle.files), len(bundle.excluded_paths), bundle.source_bytes,
        sum(item.line_count for item in bundle.files),
        tuple(item.path for item in bundle.files), tuple(bundle.warnings),
    )


def run_scan(
    request: ScanRequest,
    output_dir: str | Path,
    report_name: str,
) -> ScanResult:
    """Scan without API and write local reports without clobbering prior output."""
    _validate_request(request)
    if request.mode == "paste":
        scan = scan_text(request.text, filename="pasted.txt", language=request.language)
    else:
        scan = scan_path(request.source, language=request.language)
    report = build_report(scan)
    html_path, markdown_path = write_report(report, output_dir, name=report_name)
    counts = scan.counts
    return ScanResult(
        report.status, counts["enumerated"], counts["analyzed"], counts["limited"],
        counts["failed"], counts["excluded"], counts["unsupported"],
        len(report.findings), report.verified_count, html_path, markdown_path,
    )
