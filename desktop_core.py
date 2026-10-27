"""Headless desktop workflow used by the Windows GUI.

Only local safe input readers, deterministic scanner and offline reporters are
called. Keeping this layer separate from Tk enables Windows/Linux CI tests
without a display, API key or external network access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from threading import Event
from typing import Callable, Literal

from code_input import InputError, bundle_from_text, load_path
from offline_core import OFFLINE_LIMITS, _split_delimited_txt, scan_path, scan_text
from offline_report import build_report, write_report
from offline_coverage import list_pruned_subtrees
from report_cleanup import ReportReceipt, capture_report_receipt


class ScanCancelled(Exception):
    """User requested cancellation before the report publication boundary."""


@dataclass(frozen=True)
class ProgressUpdate:
    phase: Literal["reading", "scan", "report", "publishing", "done", "preview"]
    completed: int = 0
    total: int = 0


@dataclass
class ScanControl:
    """Thread-safe cooperative cancellation; callback runs on the worker thread."""

    on_update: Callable[[ProgressUpdate], None] | None = None
    cancel_requested: Event = field(default_factory=Event)

    def cancel(self) -> None:
        self.cancel_requested.set()

    def check(self) -> None:
        if self.cancel_requested.is_set():
            raise ScanCancelled("사용자 취소 요청")

    def emit(self, phase: Literal["reading", "scan", "report", "publishing", "done", "preview"], completed: int = 0, total: int = 0) -> None:
        if self.on_update is not None:
            self.on_update(ProgressUpdate(phase, completed, total))


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
    python_files: int
    generic_files: int
    paths: tuple[str, ...]
    warnings: tuple[str, ...]
    pruned_subtrees: tuple[str, ...] = ()

    def display(self) -> str:
        summary = (
            f"입력 종류: {self.kind}\n"
            f"분석 후보 파일: {self.files}개 / 제외·미지원: {self.excluded}개\n"
            f"읽은 자료: {self.bytes:,} bytes / {self.lines:,}줄\n"
            f"검사 예정 범위: Python AST {self.python_files}개 / 일반 패턴만 {self.generic_files}개\n"
            f"탐색 제외된 폴더: {len(self.pruned_subtrees)}개 (내부 파일 수 미확인)\n"
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
    pruned_subtrees: int = 0
    report_receipt: ReportReceipt | None = None

    def display(self) -> str:
        return (
            f"보고서 상태: {self.status}\n"
            f"발견 {self.files}개 / Python 분석 {self.analyzed}개 / 제한 {self.limited}개 / "
            f"실패 {self.failed}개 / 제외 {self.excluded}개 / 미지원 {self.unsupported}개\n"
            f"탐색 제외 폴더 {self.pruned_subtrees}개 (내부 파일 수는 미확인)\n"
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


def inspect_input(request: ScanRequest, *, control: ScanControl | None = None) -> InputPreview:
    """Read and inventory eligible inputs, but DO NOT execute static checks."""
    if control is not None:
        control.check()
        control.emit("reading")
    bundle, kind = _base_bundle(request)
    if control is not None:
        control.check()
    if kind in {"paste", "txt"} and len(bundle.files) == 1:
        parsed = _split_delimited_txt(bundle.files[0], limits=OFFLINE_LIMITS)
        if parsed is not None:
            if request.language is not None:
                raise InputError("통합 TXT는 파일별 확장자를 사용하므로 언어 자동을 선택하세요.")
            bundle, _origins, additional = parsed
            if control is not None:
                control.check()
                control.emit("preview", 1, 1)
            return InputPreview(
                "multi-txt", len(bundle.files), len(additional),
                bundle.source_bytes, sum(item.line_count for item in bundle.files),
                sum(item.path.lower().endswith((".py", ".pyi")) for item in bundle.files),
                sum(not item.path.lower().endswith((".py", ".pyi")) for item in bundle.files),
                tuple(item.path for item in bundle.files), tuple(bundle.warnings),
            )
    pruned = list_pruned_subtrees(request.source, limits=OFFLINE_LIMITS) if kind == "folder" else ()
    if control is not None:
        control.check()
        control.emit("preview", 1, 1)
    return InputPreview(
        kind, len(bundle.files), len(bundle.excluded_paths), bundle.source_bytes,
        sum(item.line_count for item in bundle.files),
        sum(item.path.lower().endswith((".py", ".pyi")) or (kind in {"paste", "txt"} and request.language == "python") for item in bundle.files),
        sum(not (item.path.lower().endswith((".py", ".pyi")) or (kind in {"paste", "txt"} and request.language == "python")) for item in bundle.files),
        tuple(item.path for item in bundle.files), tuple(bundle.warnings),
        pruned,
    )


def run_scan(
    request: ScanRequest,
    output_dir: str | Path,
    report_name: str,
    *,
    control: ScanControl | None = None,
) -> ScanResult:
    """Run an offline scan; cancellation before publishing writes no report pair."""
    _validate_request(request)
    if control is not None:
        control.check()
        control.emit("reading")
    on_progress = (
        (lambda completed, total: control.emit("scan", completed, total))
        if control is not None else None
    )
    check_cancelled = control.check if control is not None else None
    if request.mode == "paste":
        scan = scan_text(
            request.text, filename="pasted.txt", language=request.language,
            on_progress=on_progress, check_cancelled=check_cancelled,
        )
    else:
        scan = scan_path(
            request.source, language=request.language,
            on_progress=on_progress, check_cancelled=check_cancelled,
        )
    if control is not None:
        control.check()
        control.emit("report")
    report = build_report(scan)
    if control is not None:
        control.check()
        control.emit("publishing")
        # Cancellation is cooperative until this final publication boundary.
        # Once publishing starts, atomic write_report completes or rolls back.
        control.check()
    html_path, markdown_path = write_report(report, output_dir, name=report_name)
    receipt = capture_report_receipt(html_path, markdown_path)
    if control is not None:
        control.emit("done", 1, 1)
    counts = scan.counts
    return ScanResult(
        report.status, counts["enumerated"], counts["analyzed"], counts["limited"],
        counts["failed"], counts["excluded"], counts["unsupported"],
        len(report.findings), report.verified_count, html_path, markdown_path,
        counts["pruned_subtrees"], receipt,
    )
