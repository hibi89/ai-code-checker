"""Fail-closed cleanup for the exact local HTML/Markdown pair created in this run.

There is no directory-wide deletion, discovery of older reports, network access,
or automatic removal. The caller must first obtain explicit user confirmation.
"""
from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path

# Avoid hashing unbounded modified files. Larger reports remain readable but
# deliberately lack an in-app deletion receipt.
MAX_RECEIPT_BYTES = 32 * 1024 * 1024


class ReportCleanupError(ValueError):
    """Refuse removal of an untrusted, modified or partial report pair."""


@dataclass(frozen=True)
class FileIdentity:
    path: Path
    size: int
    mtime_ns: int
    dev: int
    inode: int
    sha256: str


@dataclass(frozen=True)
class ReportReceipt:
    """Session-local proof of exact generated output; never persisted to disk."""

    directory: Path
    html: FileIdentity
    markdown: FileIdentity


def _identity(path: Path, directory: Path) -> FileIdentity:
    if path.parent.resolve(strict=True) != directory:
        raise ReportCleanupError("보고서 저장 폴더가 변경되었습니다.")
    if path.is_symlink():
        raise ReportCleanupError("심볼릭 링크 보고서는 삭제하지 않습니다.")
    st = path.lstat()
    if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
        raise ReportCleanupError("일반 단독 파일만 삭제할 수 있습니다.")
    if st.st_size > MAX_RECEIPT_BYTES:
        raise ReportCleanupError("보고서 크기가 안전 삭제 검사 한도를 초과합니다.")
    hasher = hashlib.sha256()
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
            raise ReportCleanupError("일반 단독 파일만 삭제할 수 있습니다.")
        if (opened.st_dev, opened.st_ino, opened.st_mtime_ns, opened.st_size) != (
            st.st_dev, st.st_ino, st.st_mtime_ns, st.st_size
        ):
            raise ReportCleanupError("파일이 확인 과정에서 변경되었습니다.")
        with os.fdopen(fd, "rb", closefd=False) as handle:
            while True:
                block = handle.read(64 * 1024)
                if not block:
                    break
                hasher.update(block)
        after = os.fstat(fd)
        if (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_size) != (
            st.st_dev, st.st_ino, st.st_mtime_ns, st.st_size
        ):
            raise ReportCleanupError("파일 읽기 중 변경을 감지했습니다.")
    finally:
        os.close(fd)
    return FileIdentity(path, st.st_size, st.st_mtime_ns, st.st_dev, st.st_ino, hasher.hexdigest())


def _validated_pair(html_path: Path, markdown_path: Path) -> Path:
    if html_path.name in {".", ".."} or html_path.suffix.lower() != ".html":
        raise ReportCleanupError("HTML 보고서 경로가 유효하지 않습니다.")
    if markdown_path.suffix.lower() != ".md" or markdown_path.stem != html_path.stem:
        raise ReportCleanupError("HTML/Markdown 파일 쌍이 일치하지 않습니다.")
    if html_path.parent != markdown_path.parent:
        raise ReportCleanupError("보고서 두 파일이 서로 다른 폴더에 있습니다.")
    if html_path.parent.is_symlink():
        raise ReportCleanupError("심볼릭 링크 저장 폴더는 삭제할 수 없습니다.")
    return html_path.parent.resolve(strict=True)


def capture_report_receipt(html_path: Path, markdown_path: Path) -> ReportReceipt | None:
    """Capture only immediately after this application's successful report write.

    Failure disables GUI deletion; it must not invalidate a complete scan.
    """
    try:
        html_path, markdown_path = Path(html_path), Path(markdown_path)
        directory = _validated_pair(html_path, markdown_path)
        return ReportReceipt(
            directory,
            _identity(html_path, directory),
            _identity(markdown_path, directory),
        )
    except (OSError, ValueError):
        return None


def delete_report_pair(receipt: ReportReceipt) -> None:
    """Explicitly delete the two unchanged regular files; never delete a folder.

    Both files are preflight-verified BEFORE either is removed. File unlinking
    cannot be a truly atomic two-file transaction; on an I/O failure, report
    the incomplete removal rather than promising both files were deleted.
    """
    if not isinstance(receipt, ReportReceipt):
        raise ReportCleanupError("검증된 현재 실행 보고서가 없습니다.")
    directory = _validated_pair(receipt.html.path, receipt.markdown.path)
    if directory != receipt.directory:
        raise ReportCleanupError("저장 폴더의 실제 경로가 변경되었습니다.")
    try:
        for expected in (receipt.html, receipt.markdown):
            if _identity(expected.path, directory) != expected:
                raise ReportCleanupError("파일이 생성된 이후 변경되어 삭제를 거부했습니다.")
    except OSError as error:
        raise ReportCleanupError("보고서 두 파일이 모두 존재하고 변경되지 않아야 삭제할 수 있습니다.") from error
    removed = 0
    try:
        for expected in (receipt.html, receipt.markdown):
            # Recheck the folder and exact file identity just before unlink.
            if expected.path.parent.resolve(strict=True) != directory:
                raise ReportCleanupError("삭제 도중 저장 폴더가 변경되었습니다.")
            if _identity(expected.path, directory) != expected:
                raise ReportCleanupError("삭제 도중 보고서 파일이 변경되었습니다.")
            expected.path.unlink()
            removed += 1
    except (OSError, ValueError) as error:
        raise ReportCleanupError(
            f"파일 {removed}/2개 삭제 후 중단됐습니다. 남은 보고서를 직접 확인하세요."
        ) from error
