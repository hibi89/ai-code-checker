"""Read-only structural/integrity preflight for an owner's *unreleased* ZIP.

A match certifies neither malware safety nor the right to redistribute bundled
binaries. This tool NEVER creates a retail package, runs an EXE, extracts ZIP
entries, reads customer source, uploads files, or sets a release-approved flag.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import unicodedata
import zipfile
from pathlib import Path

from input_safety import validate_offline_input_path

FORMAT = "code_checker_customer_zip_candidate_structure_v1"
EXPECTED = frozenset({
    "CodeCheckerOffline.exe", "README.txt", "LICENSE",
    "NOTICE.txt", "SHA256SUMS.txt",
})
LICENSE_PATTERN = re.compile(r"LICENSES/[A-Za-z0-9][A-Za-z0-9._-]{0,79}\.(?:txt|md|terms|license)\Z")
SHA_PATTERN = re.compile(r"([0-9a-f]{64})  ([A-Za-z0-9][A-Za-z0-9._/-]*)\Z")
MAX_ZIP_BYTES = 320 * 1024 * 1024
MAX_EXE_BYTES = 256 * 1024 * 1024
MAX_TEXT_BYTES = 2 * 1024 * 1024
MAX_SUMS_BYTES = 128 * 1024
MAX_ENTRIES = 128
MAX_TOTAL_BYTES = 300 * 1024 * 1024
_WINDOWS_RESERVED = re.compile(r"(?i)^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)")
_REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def _local_file(path: Path, limit: int) -> tuple[str, int]:
    # Existing shared offline guard prevents UNC, mapped Windows network drives,
    # reparse-point ancestors and linked inputs before any file is opened.
    candidate = validate_offline_input_path(path)
    st = candidate.lstat()
    if (not stat.S_ISREG(st.st_mode) or candidate.is_symlink()
            or getattr(st, "st_file_attributes", 0) & _REPARSE
            or not 0 < st.st_size <= limit):
        raise ValueError("Missing, linked or oversized local file")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(candidate, flags)
    try:
        opened = os.fstat(fd)
        identity = lambda x: (x.st_dev, x.st_ino, x.st_size, x.st_mtime_ns)
        if not stat.S_ISREG(opened.st_mode) or identity(opened) != identity(st):
            raise ValueError("Local file changed before opening")
        h = hashlib.sha256()
        with os.fdopen(fd, "rb", closefd=False) as stream:
            for part in iter(lambda: stream.read(1024 * 1024), b""):
                h.update(part)
        if identity(os.fstat(fd)) != identity(opened) or identity(candidate.lstat()) != identity(st):
            raise ValueError("Local file changed while hashing")
        return h.hexdigest(), st.st_size
    finally:
        os.close(fd)


def _validate_entry(info: zipfile.ZipInfo) -> str:
    name = info.filename
    if (not name or name not in EXPECTED and LICENSE_PATTERN.fullmatch(name) is None
            or name != unicodedata.normalize("NFKC", name)
            or any(part in ("", ".", "..") for part in name.split("/"))
            or "\\" in name or "\x00" in name
            or any(_WINDOWS_RESERVED.match(part) for part in name.split("/"))
            or info.is_dir() or info.flag_bits & 0x1
            or info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)):
        raise ValueError("Unsafe or unexpected customer ZIP entry")
    mode = stat.S_IFMT(info.external_attr >> 16)
    if mode not in (0, stat.S_IFREG):
        raise ValueError("Links or special files are prohibited in customer ZIP")
    limit = MAX_EXE_BYTES if name == "CodeCheckerOffline.exe" else (
        MAX_SUMS_BYTES if name == "SHA256SUMS.txt" else MAX_TEXT_BYTES)
    if not 0 < info.file_size <= limit:
        raise ValueError("Missing or oversized ZIP entry data")
    return name


def inspect_candidate(archive: Path, exe: Path) -> dict:
    """Compare one actual local EXE to a bounded, still-unapproved ZIP."""
    exe_sha, exe_size = _local_file(exe, MAX_EXE_BYTES)
    zip_sha, zip_size = _local_file(archive, MAX_ZIP_BYTES)
    if archive.absolute() == exe.absolute():
        raise ValueError("Candidate ZIP and EXE must be separate")
    try:
        with zipfile.ZipFile(archive, "r") as z:
            infos = z.infolist()
            if not 0 < len(infos) <= MAX_ENTRIES:
                raise ValueError("Unexpected ZIP entry count")
            names = [_validate_entry(i) for i in infos]
            if not EXPECTED.issubset(names) or len(set(n.casefold() for n in names)) != len(names):
                raise ValueError("Missing required files or Windows case-colliding entries")
            if sum(i.file_size for i in infos) > MAX_TOTAL_BYTES:
                raise ValueError("ZIP expanded size exceeds customer candidate limit")
            hashes: dict[str, str] = {}
            sums: bytes | None = None
            for info in infos:
                digest = hashlib.sha256()
                count = 0
                with z.open(info, "r") as f:
                    while True:
                        chunk = f.read(1024 * 1024)
                        if not chunk:
                            break
                        count += len(chunk)
                        if count > info.file_size:
                            raise ValueError("Unexpected decompression expansion")
                        digest.update(chunk)
                        if info.filename == "SHA256SUMS.txt":
                            sums = (sums or b"") + chunk
                if count != info.file_size:
                    raise ValueError("ZIP stored size differs from extracted byte count")
                hashes[info.filename] = digest.hexdigest()
                if info.filename != "CodeCheckerOffline.exe" and info.filename != "SHA256SUMS.txt":
                    # All human-facing files must be usable UTF-8 text, but
                    # their legal adequacy is never asserted.
                    with z.open(info) as stream:
                        raw = stream.read(MAX_TEXT_BYTES + 1)
                    if b"\x00" in raw:
                        raise ValueError("Customer notices/docs contain binary data")
                    raw.decode("utf-8-sig", errors="strict")
            if hashes["CodeCheckerOffline.exe"] != exe_sha:
                raise ValueError("ZIP EXE differs from independently supplied candidate")
            if sums is None:
                raise ValueError("Missing checksums")
            lines = sums.decode("ascii", errors="strict").splitlines()
            if not lines or any("\r" in line for line in lines):
                raise ValueError("Invalid checksum text")
            pairs = []
            for line in lines:
                match = SHA_PATTERN.fullmatch(line)
                if match is None:
                    raise ValueError("Invalid SHA256SUMS line format")
                pairs.append((match.group(2), match.group(1)))
            required_sums = {n for n in names if n != "SHA256SUMS.txt"}
            if ([n for n, _ in pairs] != sorted(required_sums)
                    or len(pairs) != len(required_sums)
                    or any(hashes[name] != sha for name, sha in pairs)):
                raise ValueError("ZIP entry checksums missing, duplicated or mismatched")
    except (zipfile.BadZipFile, zipfile.LargeZipFile, EOFError, UnicodeError) as exc:
        raise ValueError("Invalid or corrupted ZIP candidate") from exc
    # Reread both local objects at the end; no evidence is valid if modified.
    if _local_file(exe, MAX_EXE_BYTES) != (exe_sha, exe_size):
        raise ValueError("EXE changed during candidate inspection")
    if _local_file(archive, MAX_ZIP_BYTES) != (zip_sha, zip_size):
        raise ValueError("ZIP changed during candidate inspection")
    return {
        "format": FORMAT,
        "candidate_zip_sha256": zip_sha,
        "candidate_zip_bytes": zip_size,
        "exact_exe_sha256": exe_sha,
        "exact_exe_bytes": exe_size,
        "entries_checked": len(names),
        "original_license_texts_verified": False,
        "vendor_redistribution_rights_verified": False,
        "human_windows_acceptance_verified": False,
        "owner_release_approval": False,
        "customer_release_ready": False,
        "status": "PACKAGE_STRUCTURE_ONLY_RELEASE_BLOCKED",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Inspect private unapproved customer ZIP, never authorize release")
    p.add_argument("--zip", required=True, type=Path)
    p.add_argument("--exe", required=True, type=Path)
    p.add_argument("--out", type=Path, help="Fresh local summary JSON; optional")
    args = p.parse_args(argv)
    try:
        if args.out is not None and (
            args.out.exists() or args.out.is_symlink()
            or not args.out.parent.is_dir() or args.out.parent.is_symlink()
            or args.out in (args.zip, args.exe)
            or args.out.suffix.lower() != ".json"
        ):
            raise ValueError("Output must be new, local and distinct")
        receipt = inspect_candidate(args.zip, args.exe)
        if args.out is not None:
            # Subject to the same path/UNC/reparse rejection as other offline paths.
            out = validate_offline_input_path(args.out)
            with out.open("x", encoding="utf-8", newline="\n") as stream:
                json.dump(receipt, stream, ensure_ascii=False, sort_keys=True, indent=2)
                stream.write("\n")
        print("PRIVATE_CUSTOMER_ZIP_STRUCTURE_PASS")
        print("EXE_SHA256=" + receipt["exact_exe_sha256"])
        print("ZIP_SHA256=" + receipt["candidate_zip_sha256"])
        print("CUSTOMER_RELEASE_READY=False")
        return 0
    except (OSError, ValueError, TypeError, KeyError, AttributeError, zipfile.BadZipFile) as exc:
        print("PRIVATE_CUSTOMER_ZIP_STRUCTURE_INVALID")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
