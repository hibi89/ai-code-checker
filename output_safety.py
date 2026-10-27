"""Preflight for local-only report output paths; never traverses customer source.

This is a safety guard, not a guarantee against a hostile concurrent process
swapping a filesystem component after preflight. No drive or network inspection
is performed and synchronized directories can still be user-selected.
"""
from __future__ import annotations

import os
import stat
from pathlib import Path

from code_input import InputError

_REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def validate_output_location(
    output_dir: str | Path, *, input_directory: str | Path | None = None,
) -> Path:
    """Reject output through links/junctions, UNC paths and inside scanned folder.

    Does not create any file or directory. Other scans, including a single
    source file, may still select an ordinary separate folder next to input.
    """
    raw = os.fspath(output_dir)
    if not isinstance(raw, str) or not raw.strip() or "\x00" in raw:
        raise InputError("유효한 로컬 보고서 저장 폴더를 지정하세요.")
    if raw.startswith(("\\\\", "//")):
        raise InputError("네트워크 공유 또는 장치 경로로 보고서를 저장하지 않습니다.")
    destination = Path(raw).expanduser().absolute()
    try:
        for node in (destination, *destination.parents):
            try:
                info = node.lstat()
            except FileNotFoundError:
                continue
            if stat.S_ISLNK(info.st_mode) or (
                getattr(info, "st_file_attributes", 0) & _REPARSE
            ):
                raise InputError("심볼릭 링크·Windows 재분석 경로를 통한 보고서 출력을 거부했습니다.")
        if destination.exists() and not destination.is_dir():
            raise InputError("보고서 저장 위치가 폴더가 아닙니다.")
        resolved = destination.resolve(strict=False)
        if input_directory is not None:
            source_root = Path(input_directory).expanduser().resolve(strict=False)
            if resolved == source_root or source_root in resolved.parents:
                raise InputError("검사 중인 프로젝트 폴더 내부로 보고서를 저장하지 않습니다.")
    except (OSError, RuntimeError) as error:
        raise InputError("보고서 경로의 안전성을 확인할 수 없습니다.") from error
    return destination
