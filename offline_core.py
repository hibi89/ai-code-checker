"""Offline-only ingestion and deterministic scan with explicit source coverage.

This module never calls Gemini, executes input code, installs packages or performs
network access. The existing cloud CLI is deliberately unchanged.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import unicodedata
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Callable, Literal

from code_input import (
    CodeBundle, InputError, InputLimits, SecretRedaction, SourceFile,
    _is_ignored_path, _is_sensitive_path, _is_supported, _validate_relative_path,
    bundle_from_text, load_path,
)
from review_models import CodeFinding
from static_checks import run_static_checks
from offline_coverage import list_pruned_subtrees


OFFLINE_LIMITS = InputLimits(
    max_files=200,
    max_file_bytes=1024 * 1024,
    max_total_bytes=8 * 1024 * 1024,
)
LANGUAGE_SUFFIX = {
    "python": ".py",
    "javascript": ".js",
    "typescript": ".ts",
}
_HEADER = re.compile(r"===== FILE: (.+) =====\Z")
_RESERVED_PREFIX = "===== FILE:"
_ESCAPED_PREFIX = r"\===== FILE:"
ScanStatus = Literal["complete", "partial", "blocked", "cancelled"]
FileStatus = Literal["analyzed", "limited", "failed", "excluded", "unsupported"]


@dataclass(frozen=True)
class SourceOrigin:
    logical_path: str
    container_path: str
    line_offset: int = 0

    def source_line(self, logical_line: int) -> int:
        """Map one-based logical line back to the original TXT or source file."""
        if logical_line < 1:
            raise ValueError("Line numbers must be positive")
        return logical_line + self.line_offset


@dataclass(frozen=True)
class FileCoverage:
    path: str
    status: FileStatus
    analyzer: str
    reason: str
    origin: SourceOrigin | None = None


@dataclass
class OfflineScan:
    bundle: CodeBundle
    findings: list[CodeFinding]
    coverage: list[FileCoverage]
    input_kind: str
    warnings: list[str] = field(default_factory=list)
    pruned_subtrees: tuple[str, ...] = ()

    @property
    def status(self) -> ScanStatus:
        return "partial" if self.pruned_subtrees or any(item.status != "analyzed" for item in self.coverage) else "complete"

    @property
    def counts(self) -> dict[str, int]:
        counts = {
            "enumerated": len(self.coverage),
            "analyzed": 0,
            "limited": 0,
            "failed": 0,
            "excluded": 0,
            "unsupported": 0,
            "pruned_subtrees": len(self.pruned_subtrees),
        }
        for entry in self.coverage:
            counts[entry.status] += 1
        return counts

    def origin_for(self, path: str, line_number: int) -> tuple[str, int]:
        for entry in self.coverage:
            if entry.path == path and entry.origin is not None:
                return entry.origin.container_path, entry.origin.source_line(line_number)
        raise KeyError(path)

    def summary(self) -> dict[str, object]:
        """Metadata-only: do not print source code or findings evidence."""
        return {
            "status": self.status,
            "input_kind": self.input_kind,
            "counts": self.counts,
            "findings_count": len(self.findings),
            "files": [
                {
                    "path": item.path,
                    "status": item.status,
                    "analyzer": item.analyzer,
                    "reason": item.reason,
                    "origin": item.origin.container_path if item.origin else None,
                }
                for item in self.coverage
            ],
            "warnings": self.warnings,
            "pruned_subtrees": list(self.pruned_subtrees),
            "pruned_subtrees_note": "내부 파일은 읽거나 개별 집계하지 않았습니다.",
        }


def _collision_key(path: str) -> str:
    return unicodedata.normalize("NFC", path).casefold()


def _ensure_distinct(paths: list[str]) -> None:
    seen: set[str] = set()
    for path in paths:
        key = _collision_key(path)
        if key in seen:
            raise InputError("대소문자·Unicode 정규화 기준 중복 파일 경로를 거부했습니다.")
        seen.add(key)


def _language_virtual_path(original: str, language: str | None) -> str:
    if language is None:
        return original
    if language not in LANGUAGE_SUFFIX:
        raise InputError("지원하지 않는 언어 선택입니다.")
    path = Path(original)
    if path.suffix.lower() != ".txt":
        raise InputError("언어 선택은 단일 TXT 또는 붙여넣기 TXT에만 적용됩니다.")
    return path.stem + LANGUAGE_SUFFIX[language]


def _split_delimited_txt(
    source: SourceFile,
    *,
    limits: InputLimits,
) -> tuple[CodeBundle, dict[str, SourceOrigin], list[FileCoverage]] | None:
    """Parse a strict multi-file TXT; None means an ordinary single TXT.

    A header must be the first non-empty line. In code, a literal header line
    must have a leading backslash, which is removed during reconstruction.
    """
    lines = source.text.splitlines(keepends=True)
    first = next((s.rstrip("\r\n") for s in lines if s.strip()), "")
    if not first.startswith(_RESERVED_PREFIX):
        return None
    if _HEADER.fullmatch(first) is None:
        raise InputError("다중 TXT의 첫 파일 구분자가 잘못되었습니다.")

    parts: list[tuple[str, int, str]] = []
    name: str | None = None
    header_line = 0
    current: list[str] = []

    def flush() -> None:
        if name is None:
            return
        body = "".join(current)
        if not body.strip():
            raise InputError("다중 TXT에 내용이 없는 파일 구간이 있습니다.")
        if len(body.encode("utf-8")) > limits.max_file_bytes:
            raise InputError("다중 TXT 구간이 파일당 크기 제한을 초과합니다.")
        parts.append((name, header_line, body))

    for line_number, value in enumerate(lines, 1):
        raw = value.rstrip("\r\n")
        if raw.startswith(_ESCAPED_PREFIX):
            if name is None:
                raise InputError("다중 TXT의 첫 구간이 파일 구분자가 아닙니다.")
            current.append(value[1:])
        elif raw.startswith(_RESERVED_PREFIX):
            match = _HEADER.fullmatch(raw)
            if match is None:
                raise InputError("다중 TXT 파일 구분자 형식이 잘못되었습니다.")
            flush()
            name = _validate_relative_path(match.group(1))
            header_line = line_number
            current = []
        elif name is not None:
            current.append(value)
        elif raw.strip():
            raise InputError("첫 파일 구분자 앞에 예상하지 못한 내용이 있습니다.")
    flush()
    if len(parts) > limits.max_files:
        raise InputError("다중 TXT 파일 개수가 한도를 초과합니다.")
    _ensure_distinct([p for p, _, _ in parts])

    kept: list[SourceFile] = []
    excluded: list[FileCoverage] = []
    origins: dict[str, SourceOrigin] = {}
    warnings: list[str] = []
    for path, offset, body in parts:
        origin = SourceOrigin(path, source.path, offset)
        if _is_sensitive_path(path) or _is_ignored_path(path):
            excluded.append(FileCoverage(path, "excluded", "none", "sensitive or excluded path", origin))
            continue
        if not _is_supported(path):
            excluded.append(FileCoverage(path, "unsupported", "none", "unsupported extension", origin))
            continue
        nlines = len(body.splitlines())
        redactions = tuple(
            SecretRedaction(item.line_number - offset, item.kind)
            for item in source.redactions
            if offset < item.line_number <= offset + nlines
        )
        kept.append(SourceFile(path, body, len(body.encode("utf-8")), redactions))
        origins[path] = origin

    if not kept:
        raise InputError("다중 TXT에 검사 가능한 파일이 없습니다.")
    kept.sort(key=lambda item: item.path.casefold())
    bundle = CodeBundle(
        files=kept,
        warnings=warnings,
        excluded_paths=[entry.path for entry in excluded],
        source_bytes=source.source_bytes,
    )
    return bundle, origins, excluded


def _check_bundle(
    bundle: CodeBundle,
    *,
    input_kind: str,
    origins: dict[str, SourceOrigin],
    excluded: list[FileCoverage] | None = None,
    on_progress: Callable[[int, int], None] | None = None,
    check_cancelled: Callable[[], None] | None = None,
) -> OfflineScan:
    coverage = list(excluded or [])
    for path in bundle.excluded_paths:
        if any(item.path == path for item in coverage):
            continue
        ignored = _is_sensitive_path(path) or _is_ignored_path(path)
        coverage.append(
            FileCoverage(
                path, "excluded" if ignored else "unsupported", "none",
                "excluded by policy" if ignored else "unsupported or undecodable input",
            )
        )
    _ensure_distinct([item.path for item in coverage] + [source.path for source in bundle.files])

    incremental = on_progress is not None or check_cancelled is not None
    findings: list[CodeFinding] = []
    for index, source in enumerate(bundle.files, 1):
        if check_cancelled is not None:
            check_cancelled()
        origin = origins.get(source.path, SourceOrigin(source.path, source.path))
        if source.path.lower().endswith((".py", ".pyi")):
            try:
                ast.parse(source.text, filename=source.path)
                coverage.append(FileCoverage(source.path, "analyzed", "python-ast+generic", "rule-based checks only", origin))
            except (SyntaxError, ValueError):
                coverage.append(FileCoverage(source.path, "failed", "python-ast+generic", "Python parsing failed", origin))
        else:
            coverage.append(FileCoverage(source.path, "limited", "generic-patterns-only", "no language-specific analyzer", origin))
        if incremental:
            # Static checks are file-local; preserve existing file and finding order.
            findings.extend(run_static_checks(CodeBundle([source])))
        if on_progress is not None:
            on_progress(index, len(bundle.files))
    if check_cancelled is not None:
        check_cancelled()
    if not incremental:
        findings = run_static_checks(bundle)
    return OfflineScan(bundle, findings, coverage, input_kind, list(bundle.warnings))


def _txt_bundle(
    base: CodeBundle,
    *,
    source_label: str,
    language: str | None,
    limits: InputLimits,
    input_kind: str,
    on_progress: Callable[[int, int], None] | None = None,
    check_cancelled: Callable[[], None] | None = None,
) -> OfflineScan:
    if len(base.files) != 1:
        raise InputError("단일 TXT 입력에서 하나의 소스만 예상했습니다.")
    source = base.files[0]
    parsed = _split_delimited_txt(source, limits=limits)
    if parsed is not None:
        if language is not None:
            raise InputError("다중 파일 TXT에서는 언어를 각 파일 확장자로 지정하세요.")
        bundle, origins, excluded = parsed
        origins = {
            path: replace(origin, container_path=source_label)
            for path, origin in origins.items()
        }
        excluded = [
            replace(item, origin=replace(item.origin, container_path=source_label) if item.origin else None)
            for item in excluded
        ]
        return _check_bundle(
            bundle, input_kind="multi-txt", origins=origins, excluded=excluded,
            on_progress=on_progress, check_cancelled=check_cancelled,
        )
    virtual = _language_virtual_path(source.path, language)
    modified = replace(source, path=virtual)
    bundle = CodeBundle([modified], list(base.warnings), list(base.excluded_paths), base.source_bytes)
    return _check_bundle(
        bundle, input_kind=input_kind,
        origins={virtual: SourceOrigin(virtual, source_label)},
        on_progress=on_progress, check_cancelled=check_cancelled,
    )


def scan_path(
    path: str | Path,
    *,
    language: str | None = None,
    limits: InputLimits = OFFLINE_LIMITS,
    on_progress: Callable[[int, int], None] | None = None,
    check_cancelled: Callable[[], None] | None = None,
) -> OfflineScan:
    """Never executes scanned code or calls external APIs."""
    source_path = Path(path).expanduser()
    if language is not None and source_path.suffix.lower() != ".txt":
        raise InputError("언어 선택은 TXT에서만 허용됩니다.")
    # The legacy loader enforces size, path, ZIP and symlink protections.
    bundle = load_path(source_path, limits)
    if check_cancelled is not None:
        check_cancelled()
    if source_path.is_file() and source_path.suffix.lower() == ".txt":
        return _txt_bundle(
            bundle, source_label=source_path.name, language=language,
            limits=limits, input_kind="txt",
            on_progress=on_progress, check_cancelled=check_cancelled,
        )
    input_kind = "zip" if source_path.suffix.lower() == ".zip" else (
        "folder" if source_path.is_dir() else "file"
    )
    scan = _check_bundle(
        bundle, input_kind=input_kind, origins={},
        on_progress=on_progress, check_cancelled=check_cancelled,
    )
    if input_kind == "folder":
        scan.pruned_subtrees = list_pruned_subtrees(source_path, limits=limits)
    if check_cancelled is not None:
        check_cancelled()
    return scan


def scan_text(
    text: str,
    *,
    filename: str = "pasted.txt",
    language: str | None = None,
    limits: InputLimits = OFFLINE_LIMITS,
    on_progress: Callable[[int, int], None] | None = None,
    check_cancelled: Callable[[], None] | None = None,
) -> OfflineScan:
    """Inspect pasted synthetic/customer text in memory, without network access."""
    bundle = bundle_from_text(text, filename=filename, limits=limits)
    if check_cancelled is not None:
        check_cancelled()
    if filename.lower().endswith(".txt"):
        return _txt_bundle(
            bundle, source_label=filename, language=language,
            limits=limits, input_kind="paste",
            on_progress=on_progress, check_cancelled=check_cancelled,
        )
    if language is not None:
        raise InputError("확장자가 있는 코드 붙여넣기는 언어 선택을 허용하지 않습니다.")
    return _check_bundle(
        bundle, input_kind="paste", origins={},
        on_progress=on_progress, check_cancelled=check_cancelled,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="오프라인 코드 구조·위험 패턴 스캔 (AI API 호출 없음)")
    parser.add_argument("source", help="ZIP, TXT, 폴더 또는 코드 파일")
    parser.add_argument("--language", choices=tuple(LANGUAGE_SUFFIX))
    args = parser.parse_args()
    try:
        scan = scan_path(args.source, language=args.language)
    except (InputError, OSError, ValueError) as error:
        # InputError originates locally and must not echo the source contents.
        print(json.dumps({"status": "blocked", "error": type(error).__name__}, ensure_ascii=False))
        return 2
    print(json.dumps(scan.summary(), ensure_ascii=False, indent=2))
    return 0 if scan.status == "complete" else 3


if __name__ == "__main__":
    raise SystemExit(main())
