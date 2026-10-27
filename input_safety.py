"""Offline v2 input preflight: deny remote and indirect filesystem sources.

Only applies to v2 offline desktop/CLI, not the original Gemini v1 CLI.
This is not a guarantee against filesystem races, local cloud sync or a file
picker itself enumerating a share before the user submits an input.
"""
from __future__ import annotations

import os
import stat
from pathlib import Path

from code_input import InputError
from output_safety import _LOCAL_WINDOWS_DRIVE_TYPES, _REPARSE, _windows_drive_type


def validate_offline_input_path(path: str | Path) -> Path:
    """Validate path components without reading contents or following links.

    Windows drive-type lookup takes place before filesystem traversal, to
    reject UNC and drive-letter mapped shares before opening project data.
    """
    raw = os.fspath(path)
    if not isinstance(raw, str) or not raw.strip() or "\x00" in raw:
        raise InputError("로컬 검사 입력 파일 또는 폴더를 선택하세요.")
    if raw.startswith(("\\\\", "//")):
        raise InputError("네트워크 공유·장치 경로에서 직접 읽는 입력은 지원하지 않습니다.")
    try:
        candidate = Path(raw).expanduser().absolute()
        kind = _windows_drive_type(candidate)
        if kind is not None and kind not in _LOCAL_WINDOWS_DRIVE_TYPES:
            raise InputError("네트워크 연결·알 수 없는 Windows 드라이브에서 입력을 읽지 않습니다.")
        for component in (candidate, *candidate.parents):
            try:
                info = component.lstat()
            except FileNotFoundError:
                continue
            if stat.S_ISLNK(info.st_mode) or (
                getattr(info, "st_file_attributes", 0) & _REPARSE
            ):
                raise InputError("입력 경로의 심볼릭 링크·Windows 연결 경로를 거부했습니다.")
    except InputError:
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        raise InputError("입력 경로를 안전하게 확인하지 못했습니다.") from exc
    return candidate
