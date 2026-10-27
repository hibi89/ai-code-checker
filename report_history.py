"""Read-only, explicit selection of historical local Code Checker reports.

Does not discover, delete or register historical files as current-session reports.
Header checks recognize report *format*, not cryptographic provenance.
"""
from __future__ import annotations

import os
import stat
from pathlib import Path

from code_input import InputError
from output_safety import validate_output_location

_MAX_REPORT_BYTES = 32 * 1024 * 1024
_REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_HTML_MARKERS = (
    b"<!doctype html><html lang='ko'>",
    b"<title>\xec\xbd\x94\xeb\x93\x9c\xec\xb2\xb4\xec\xbb\xa4 \xec\x98\xa4\xed\x94\x84\xeb\x9d\xbc\xec\x9d\xb8 \xeb\xb3\xb4\xea\xb3\xa0\xec\x84\x9c</title>",
    b"Content-Security-Policy",
    b"default-src 'none'",
)
_MD_MARKER = "# 코드체커 오프라인 진단 보고서".encode("utf-8")


def _read_report_header(path: Path, *, suffix: str) -> bytes:
    """Check a regular single-link local file without following final symlinks."""
    try:
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise InputError("기존 보고서는 일반 단독 파일만 선택할 수 있습니다.")
        if getattr(metadata, "st_file_attributes", 0) & _REPARSE:
            raise InputError("재분석 경로에 있는 보고서는 열지 않습니다.")
        if metadata.st_size == 0 or metadata.st_size > _MAX_REPORT_BYTES:
            raise InputError("기존 보고서 크기가 허용 범위를 벗어났습니다.")
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(path, flags)
        with os.fdopen(fd, "rb") as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
                raise InputError("기존 보고서의 파일 유형이 안전하지 않습니다.")
            if (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != (
                metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns
            ):
                raise InputError("기존 보고서가 검증 중 변경되었습니다.")
            start = stream.read(8192 if suffix == ".html" else 512)
            after = os.fstat(stream.fileno())
            if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != (
                opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns
            ):
                raise InputError("기존 보고서 읽기 중 파일이 변경되었습니다.")
        return start
    except (OSError, RuntimeError) as exc:
        raise InputError("기존 보고서를 안전하게 읽을 수 없습니다.") from exc


def validate_historical_report(output_dir: str | Path, selected: str | Path) -> Path:
    """Permit explicit read-only open of paired reports in the chosen local folder.

    This cannot prove the file was produced by Code Checker: a malicious local
    actor could forge the header. Revalidate before launch; no TOCTOU guarantee.
    """
    folder = validate_output_location(output_dir)
    if not folder.is_dir():
        raise InputError("보고서 저장 폴더가 존재하지 않습니다.")

    raw = os.fspath(selected)
    if not isinstance(raw, str) or not raw.strip() or "\x00" in raw:
        raise InputError("기존 보고서 HTML 파일을 선택하세요.")
    if raw.startswith(("//", "\\\\")):
        raise InputError("네트워크 보고서는 열지 않습니다.")
    html = Path(raw).expanduser().absolute()
    if html.parent != folder or html.suffix.lower() != ".html" or html.name.startswith("."):
        raise InputError("선택한 로컬 저장 폴더의 HTML 보고서만 열 수 있습니다.")
    if not 1 <= len(html.stem) <= 80 or not all(
        char.isalnum() or char in "._-" for char in html.stem
    ):
        raise InputError("보고서 파일 이름이 유효하지 않습니다.")
    markdown = html.with_suffix(".md")
    header = _read_report_header(html, suffix=".html")
    md_header = _read_report_header(markdown, suffix=".md")
    if not all(marker in header for marker in _HTML_MARKERS) or not md_header.startswith(_MD_MARKER):
        raise InputError("코드체커에서 생성한 HTML·Markdown 보고서 형식을 확인할 수 없습니다.")
    return html
