"""Bounded, metadata-only inventory of folder subtrees skipped by safe loaders.

Never follows symlinks or reads file contents. Separate from the legacy v1
loader so current provider behavior remains unchanged.
"""
from __future__ import annotations

import os
from pathlib import Path

from code_input import IGNORED_DIRECTORIES, InputError, InputLimits, _is_linked_or_reparse


def list_pruned_subtrees(
    root: str | Path,
    *,
    limits: InputLimits,
    max_visited_directories: int = 4096,
    max_pruned_subtrees: int = 4096,
) -> tuple[str, ...]:
    """Return relative names of policy-pruned/linked/depth-limited subtrees.

    The number of files inside these subtrees is UNKNOWN; never count these
    folder markers as source files or claim that all filesystem files were seen.
    """
    path = Path(root).expanduser()
    try:
        if _is_linked_or_reparse(path) or not path.is_dir():
            raise InputError("안전한 실폴더가 아닙니다.")
    except OSError as error:
        raise InputError("프로젝트 폴더 경로를 확인하지 못했습니다.") from error
    root_resolved = path.resolve(strict=True)
    pruned: list[str] = []
    visited = 0

    def error_handler(_error: OSError) -> None:
        raise InputError("폴더 구조를 완전히 열거하지 못했습니다.")

    for current, dirnames, _filenames in os.walk(
        root_resolved, topdown=True, followlinks=False, onerror=error_handler
    ):
        visited += 1
        if visited > max_visited_directories:
            raise InputError("폴더 하위 구조의 탐색 한도를 초과했습니다.")
        parent = Path(current)
        relative = parent.relative_to(root_resolved)
        depth = len(relative.parts)
        kept: list[str] = []
        for name in sorted(dirnames):
            child = parent / name
            display = child.relative_to(root_resolved).as_posix() + "/"
            try:
                linked = _is_linked_or_reparse(child)
            except OSError as error:
                raise InputError("하위 폴더 연결 상태를 확인할 수 없습니다.") from error
            if depth >= limits.max_depth or name.lower() in IGNORED_DIRECTORIES or linked:
                pruned.append(display)
                if len(pruned) > max_pruned_subtrees:
                    raise InputError("제외 폴더 수가 안전 한도를 초과했습니다.")
            else:
                kept.append(name)
        dirnames[:] = kept
    return tuple(pruned)
