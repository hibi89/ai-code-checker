"""Explicitly opt-in, OFFLINE and NON-RELEASED private Windows ZIP candidate.

It never creates/license-approves documents, executes the EXE or uploads anything.
It reuses the existing independent candidate verifier for exact ZIP/EXE identity.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import stat
import zipfile
from pathlib import Path

from input_safety import validate_offline_input_path
from scripts.verify_customer_zip_candidate import (
    MAX_EXE_BYTES, MAX_TEXT_BYTES, _local_file, inspect_candidate,
)

FORMAT = "code_checker_private_customer_candidate_v1"
_COMPONENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}\.(?:txt|md|terms|license)\Z")
_SAFE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]*\Z")
_DATE = (1980, 1, 1, 0, 0, 0)
_REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def _blocked() -> ValueError:
    return ValueError("PRIVATE_CANDIDATE_BLOCKED")


def _existing_input(path: Path, limit: int) -> tuple[Path, str, int]:
    if not path.is_absolute():
        raise _blocked()
    checked = validate_offline_input_path(path)
    try:
        st = checked.lstat()
        if (not stat.S_ISREG(st.st_mode) or st.st_nlink != 1
                or checked.is_symlink() or getattr(st, "st_file_attributes", 0) & _REPARSE):
            raise _blocked()
        digest, size = _local_file(checked, limit)
    except OSError as exc:
        raise _blocked() from exc
    return checked, digest, size


def _destination(path: Path, sources: set[Path]) -> Path:
    if (not path.is_absolute() or path.suffix.lower() != ".zip"
            or path in sources or path.exists() or path.is_symlink()):
        raise _blocked()
    parent = validate_offline_input_path(path.parent)
    if not parent.is_dir() or parent.is_symlink() or parent != path.parent:
        raise _blocked()
    return path


def _write_member(z: zipfile.ZipFile, name: str, path: Path, expected: str, size: int) -> str:
    zi = zipfile.ZipInfo(name, _DATE)
    zi.create_system = 3
    zi.external_attr = 0o100600 << 16
    zi.compress_type = zipfile.ZIP_STORED if name.endswith(".exe") else zipfile.ZIP_DEFLATED
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    h = hashlib.sha256()
    fd = os.open(path, flags)
    try:
        opened = os.fstat(fd)
        if (not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1
                or opened.st_size != size):
            raise _blocked()
        if name != "CodeCheckerOffline.exe":
            # Text is small; check that the exact supplied original text is safe to render.
            with os.fdopen(os.dup(fd), "rb") as source:
                raw = source.read(MAX_TEXT_BYTES + 1)
            if not raw or len(raw) != size or b"\x00" in raw:
                raise _blocked()
            try:
                raw.decode("utf-8-sig", errors="strict")
            except UnicodeError as exc:
                raise _blocked() from exc
        os.lseek(fd, 0, os.SEEK_SET)  # Dup FDs share file position: reset after text checks.
        with os.fdopen(os.dup(fd), "rb") as source, z.open(zi, "w") as output:
            while True:
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                h.update(chunk)
                output.write(chunk)
        after = os.fstat(fd)
        if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != (
                opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns):
            raise _blocked()
    finally:
        os.close(fd)
    if h.hexdigest() != expected or _local_file(path, MAX_EXE_BYTES if name.endswith(".exe") else MAX_TEXT_BYTES) != (expected, size):
        raise _blocked()
    return h.hexdigest()


def create_private_candidate(*, exe: Path, readme: Path, license_file: Path,
                             notice: Path, component_licenses: dict[str, Path], output: Path) -> dict:
    """Create only a PRIVATE, unapproved candidate ZIP at an owner-chosen fresh path."""
    if (not isinstance(component_licenses, dict) or not component_licenses
            or len(component_licenses) > 120):
        raise _blocked()
    files: dict[str, Path] = {
        "CodeCheckerOffline.exe": exe, "README.txt": readme,
        "LICENSE": license_file, "NOTICE.txt": notice,
    }
    for name, candidate in component_licenses.items():
        if not isinstance(name, str) or not _COMPONENT.fullmatch(name) or name in {".", ".."}:
            raise _blocked()
        files["LICENSES/" + name] = candidate
    if len({n.casefold() for n in files}) != len(files) or any(not _SAFE.fullmatch(n) for n in files):
        raise _blocked()
    inputs: dict[str, tuple[Path, str, int]] = {}
    identities = set()
    for name, source in files.items():
        if not isinstance(source, Path):
            raise _blocked()
        validated = _existing_input(source, MAX_EXE_BYTES if name.endswith(".exe") else MAX_TEXT_BYTES)
        st = validated[0].lstat()
        identity = (st.st_dev, st.st_ino)
        if identity in identities:
            raise _blocked()
        identities.add(identity)
        inputs[name] = validated
    output = _destination(output, {p for p, _, _ in inputs.values()})
    fd = None
    created = False
    try:
        fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600)
        created = True
        with os.fdopen(fd, "wb") as stream:
            fd = None
            with zipfile.ZipFile(stream, "w", allowZip64=True) as z:
                entries = {}
                for name in sorted(inputs):
                    p, digest, size = inputs[name]
                    entries[name] = _write_member(z, name, p, digest, size)
                sums = "".join(f"{entries[name]}  {name}\n" for name in sorted(entries))
                zi = zipfile.ZipInfo("SHA256SUMS.txt", _DATE)
                zi.create_system = 3
                zi.external_attr = 0o100600 << 16
                zi.compress_type = zipfile.ZIP_STORED
                z.writestr(zi, sums.encode("ascii"))
        receipt = inspect_candidate(output, inputs["CodeCheckerOffline.exe"][0])
        if (receipt.get("customer_release_ready") is not False
                or receipt.get("exact_exe_sha256") != inputs["CodeCheckerOffline.exe"][1]
                or receipt.get("entries_checked") != len(files) + 1):
            raise _blocked()
        return {
            "format": FORMAT,
            "status": "PRIVATE_CANDIDATE_CREATED_RELEASE_BLOCKED",
            "candidate_zip_sha256": receipt["candidate_zip_sha256"],
            "exact_exe_sha256": receipt["exact_exe_sha256"],
            "entries_checked": receipt["entries_checked"],
            "customer_release_ready": False,
            "original_license_texts_verified": False,
            "vendor_redistribution_rights_verified": False,
            "human_windows_acceptance_verified": False,
            "owner_release_approval": False,
        }
    except Exception:
        # Preserve the failed, unapproved artifact. A different process may
        # have replaced this pathname; unlinking could erase its file.
        # O_EXCL prevents reuse. An owner must inspect/remove the HOLD artifact.
        raise
    finally:
        if fd is not None:
            os.close(fd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create OFFLINE PRIVATE ZIP CANDIDATE; sale is blocked")
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--readme", type=Path, required=True)
    parser.add_argument("--license", type=Path, required=True)
    parser.add_argument("--notice", type=Path, required=True)
    parser.add_argument("--component-license", action="append", default=[], metavar="NAME=PATH")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        components = {}
        for item in args.component_license:
            if "=" not in item:
                raise _blocked()
            name, source = item.split("=", 1)
            if name in components:
                raise _blocked()
            components[name] = Path(source)
        outcome = create_private_candidate(exe=args.exe, readme=args.readme,
            license_file=args.license, notice=args.notice, component_licenses=components,
            output=args.out)
        print(outcome["status"])
        print("EXE_SHA256=" + outcome["exact_exe_sha256"])
        print("ZIP_SHA256=" + outcome["candidate_zip_sha256"])
        print("CUSTOMER_RELEASE_READY=False")
        return 0
    except (ValueError, OSError, KeyError, TypeError, zipfile.BadZipFile):
        print("PRIVATE_CANDIDATE_BLOCKED")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
