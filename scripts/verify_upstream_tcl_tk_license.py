"""Match frozen EXE Tcl/Tk receipt to pinned upstream license.terms bytes.

This is local review evidence, NEVER a legal/NOTICE/customer release approval.
No original texts, source paths, EXE or customer data are uploaded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
from pathlib import Path

FORMAT = "code_checker_upstream_tcl_tk_license_byte_match_v1"
RECEIPT_FORMAT = "code_checker_frozen_tcl_tk_version_receipt_v1"
MAX_EXE = 256 * 1024 * 1024
MAX_LICENSE = 16 * 1024
MAX_RECEIPT = 4096
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
BLOCKED = ("installed_license_text_or_exact_binary_origin_proven",
           "copyright_and_redistribution_rights_verified",
           "customer_notice_ready", "customer_release_ready")
RECEIPT_KEYS = {"format", "exe_sha256", "exe_bytes",
                "frozen_process_runtime_observed", "python_runtime_version",
                "tcl_runtime_patchlevel", "tk_runtime_patchlevel", *BLOCKED}
# Git SHA-1 blob IDs, verified at official tcltk GitHub release tags.
PINNED = {
    "tcl": {
        "8.6.15": ("core-8-6-15", "d8049cd9e7ca055f7e584a76f88861a294b30c9c"),
        "8.6.18": ("core-8-6-18", "d8049cd9e7ca055f7e584a76f88861a294b30c9c"),
    },
    "tk": {
        "8.6.15": ("core-8-6-15", "01264352c87ca7e34771bd1ee18bed5201ef139f"),
        "8.6.18": ("core-8-6-18", "01264352c87ca7e34771bd1ee18bed5201ef139f"),
    },
}


def _identity(value: os.stat_result) -> tuple[int, int, int, int]:
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns


def _safe_read(path: Path, max_bytes: int) -> bytes:
    before = path.lstat()
    if (path.is_symlink() or not stat.S_ISREG(before.st_mode)
            or getattr(before, "st_file_attributes", 0) & _REPARSE
            or not 0 < before.st_size <= max_bytes):
        raise ValueError("Missing, linked or oversized local file")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or _identity(opened) != _identity(before):
            raise ValueError("File changed before read")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            content = stream.read(max_bytes + 1)
        if (len(content) != before.st_size or len(content) > max_bytes
                or _identity(os.fstat(fd)) != _identity(opened)
                or _identity(path.lstat()) != _identity(before)
                or path.is_symlink()):
            raise ValueError("File changed during read")
        return content
    finally:
        os.close(fd)


def _hash_exe(exe: Path) -> tuple[str, int]:
    before = exe.lstat()
    if (exe.is_symlink() or not stat.S_ISREG(before.st_mode)
            or getattr(before, "st_file_attributes", 0) & _REPARSE
            or not 0 < before.st_size <= MAX_EXE):
        raise ValueError("Invalid frozen EXE")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(exe, flags)
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or _identity(opened) != _identity(before):
            raise ValueError("EXE changed before hashing")
        digest = hashlib.sha256()
        size = 0
        with os.fdopen(fd, "rb", closefd=False) as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                size += len(chunk)
                if size > MAX_EXE:
                    raise ValueError("EXE too large")
                digest.update(chunk)
        if (size != before.st_size or _identity(os.fstat(fd)) != _identity(opened)
                or _identity(exe.lstat()) != _identity(before) or exe.is_symlink()):
            raise ValueError("EXE changed while hashing")
        return digest.hexdigest(), size
    finally:
        os.close(fd)


def git_blob_id(raw: bytes) -> str:
    """Git blob ID uses a prefixed header, not plain SHA1(raw)."""
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\x00" + raw).hexdigest()


def compare_originals(receipt: dict, exe: Path, tcl: bytes, tk: bytes, *,
                      pinned: dict | None = None) -> dict:
    """Compare two original texts to tagged upstream blobs; rights not verified."""
    if (not isinstance(receipt, dict) or set(receipt) != RECEIPT_KEYS
            or receipt["format"] != RECEIPT_FORMAT
            or receipt["frozen_process_runtime_observed"] is not True
            or any(receipt[flag] is not False for flag in BLOCKED)
            or not isinstance(receipt["exe_sha256"], str)
            or _SHA256.fullmatch(receipt["exe_sha256"]) is None
            or type(receipt["exe_bytes"]) is not int
            or not isinstance(receipt["python_runtime_version"], str)
            or len(receipt["python_runtime_version"]) > 32):
        raise ValueError("Invalid frozen receipt / premature release approval")
    sha, size = _hash_exe(exe)
    if sha != receipt["exe_sha256"] or size != receipt["exe_bytes"]:
        raise ValueError("Runtime receipt and executable differ")
    lookup = PINNED if pinned is None else pinned
    rows = []
    for role, raw in (("tcl", tcl), ("tk", tk)):
        version = receipt[role + "_runtime_patchlevel"]
        if not isinstance(version, str) or version not in lookup[role]:
            raise ValueError("Exact runtime version lacks verified upstream tag")
        if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_LICENSE:
            raise ValueError("Original text missing or too large")
        tag, expected_blob = lookup[role][version]
        actual_blob = git_blob_id(raw)
        if actual_blob != expected_blob:
            raise ValueError("Local original differs from tagged upstream license")
        rows.append({"component": role, "runtime_patchlevel": version,
                     "official_git_tag": tag,
                     "upstream_license_git_blob_sha1": actual_blob,
                     "upstream_original_bytes_match": True,
                     "exact_bundled_binary_owner_verified": False})
    return {
        "format": FORMAT, "exe_sha256": sha, "exe_bytes": size,
        "source_originals": rows, "original_texts_in_output": False,
        "frozen_receipt_independently_authenticated": False,
        "exact_binary_vendor_and_notice_rights_verified": False,
        "third_party_notice_ready": False,
        "license_compliance_certified": False,
        "customer_release_ready": False,
        "status": "SOURCE_LICENSE_BYTES_ONLY_HUMAN_REVIEW_REQUIRED",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare Tcl/Tk local original license bytes to upstream Git blobs")
    for option in ("exe", "runtime-receipt", "tcl-original", "tk-original", "out"):
        parser.add_argument("--" + option, required=True, type=Path)
    a = parser.parse_args(argv)
    inputs = (a.exe, a.runtime_receipt, a.tcl_original, a.tk_original)
    try:
        if (a.out.exists() or a.out.is_symlink() or not a.out.parent.is_dir()
                or a.out.parent.is_symlink() or a.out in inputs
                or len(set(inputs)) != len(inputs)):
            raise ValueError("Output must be new and files distinct")
        receipt = json.loads(_safe_read(a.runtime_receipt, MAX_RECEIPT))
        tcl = _safe_read(a.tcl_original, MAX_LICENSE)
        tk = _safe_read(a.tk_original, MAX_LICENSE)
        report = compare_originals(receipt, a.exe, tcl, tk)
        with a.out.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
        print("TAGGED_TCL_TK_LICENSE_BYTES_MATCH_PASS")
        print("EXE_HASH_BOUND=True")
        print("BINARY_LICENSE_NOTICE_RELEASE=UNVERIFIED")
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        print("TAGGED_TCL_TK_LICENSE_BYTES_MATCH_INVALID")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
