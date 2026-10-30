"""Safe, bounded collection of source text for AI-assisted review.

ZIP files are read as streams and are never extracted. Collected code is
never executed or installed. Sensitive file names are excluded before read.
"""

from __future__ import annotations

import os
import re
import stat
from bisect import bisect_right
import zlib
import zipfile
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path, PurePosixPath
from typing import Iterable


class InputError(ValueError):
    """Raised when input is unsafe, unsupported, or exceeds configured limits."""


@dataclass(frozen=True)
class InputLimits:
    max_archive_bytes: int = 20 * 1024 * 1024
    max_archive_entries: int = 1000
    max_files: int = 50
    max_file_bytes: int = 128 * 1024
    max_total_bytes: int = 512 * 1024
    max_depth: int = 12


@dataclass(frozen=True)
class SecretRedaction:
    line_number: int
    kind: str


@dataclass(frozen=True)
class SourceFile:
    path: str
    text: str
    source_bytes: int
    redactions: tuple[SecretRedaction, ...] = ()

    @cached_property
    def source_lines(self) -> tuple[str, ...]:
        """Bounded per-instance index; never persisted or globally cached."""
        return tuple(self.text.splitlines())

    @property
    def line_count(self) -> int:
        return len(self.source_lines) or 1


@dataclass
class CodeBundle:
    files: list[SourceFile]
    warnings: list[str] = field(default_factory=list)
    excluded_paths: list[str] = field(default_factory=list)
    source_bytes: int = 0

    def render(self) -> str:
        sections = []
        for source in self.files:
            sections.append(f"===== FILE: {source.path} =====\n{source.text}")
        return "\n\n".join(sections)

    @property
    def file_map(self) -> dict[str, SourceFile]:
        return {source.path: source for source in self.files}

    @property
    def redaction_count(self) -> int:
        return sum(len(source.redactions) for source in self.files)


SUPPORTED_EXTENSIONS = {
    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
    ".java", ".go", ".rs", ".rb", ".php", ".cs", ".c", ".h",
    ".cc", ".cpp", ".hpp", ".swift", ".kt", ".kts", ".scala",
    ".sql", ".sh", ".bash", ".ps1", ".bat", ".cmd", ".html",
    ".css", ".scss", ".json", ".yaml", ".yml", ".toml", ".ini",
    ".cfg", ".xml", ".properties", ".md", ".txt",
}

SUPPORTED_NAMES = {
    ".env.example", ".gitignore", "dockerfile", "makefile", "requirements.txt",
    "pipfile", "gemfile", "go.mod", "cargo.toml", "pyproject.toml",
    "package.json", "composer.json",
}

IGNORED_DIRECTORIES = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "node_modules",
    "__pycache__", "dist", "build", "coverage", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", ".tox", ".next", ".nuxt",
    "target", "vendor", ".idea", ".ai-code-checker", "reports",
}

IGNORED_FILENAMES = {
    "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock",
    "pipfile.lock", "cargo.lock", "go.sum", "composer.lock",
}

SENSITIVE_FILENAMES = {
    "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519", "credentials",
    "credentials.json", "service-account.json", "secrets.json",
}
SENSITIVE_SUFFIXES = {".pem", ".p12", ".pfx", ".key", ".jks", ".keystore"}

_SECRET_NAME = (
    r"(?:api[_-]?(?:key|token)|access[_-]?(?:key(?:[_-]?id)?|token)|"
    r"auth[_-]?token|refresh[_-]?token|client[_-]?secret|"
    r"secret[_-]?access[_-]?key|secret(?:[_-]?key)?|credentials?|token|password|passwd|"
    r"private[_-]?key|database[_-]?url|db[_-]?url|connection[_-]?string|"
    r"dsn|redis[_-]?url|mongo[_-]?url)"
)
_SENSITIVE_KEY = re.compile(rf"(?i)(?<![A-Za-z0-9]){_SECRET_NAME}(?=$|[^A-Za-z0-9])")
_SECRET_ASSIGNMENT = re.compile(
    rf"(?i)(?P<prefix>(?<![A-Za-z0-9]){_SECRET_NAME}(?=$|[^A-Za-z0-9])\s*(?:=|:)\s*)"
    r"(?:(?P<quote>['\"])(?P<value>[^'\"\r\n]{8,})(?P=quote)|"
    r"(?P<bare>[A-Za-z0-9_./+@:%=?&~-]{12,})(?=(?:[ \t]*(?:#|,|;|\}|\])|[\r\n]|$)))"
)
_PRIVATE_KEY_BLOCK = re.compile(
    r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----",
    re.DOTALL,
)
_TOKEN_PATTERNS = (
    (re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"), "GitHub token"),
    (re.compile(r"\b(?:xox[baprs]-)[A-Za-z0-9-]{16,}\b"), "Slack token"),
    (re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"), "Google API key"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key id"),
    (re.compile(r"\bsk_(?:live|test)_[A-Za-z0-9]{16,}\b"), "payment secret key"),
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]{16,}={0,2}"), "Bearer token"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"), "JWT token"),
    (re.compile(r"(?i)\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^:\s/@]+:[^@\s/]+@[^\s]+"), "credential URL"),
    (re.compile(r"(?i)\bBasic\s+[A-Za-z0-9+/]{16,}={0,2}"), "Basic authorization value"),
)
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_KOREAN_PHONE = re.compile(r"(?<!\d)(?:\+?82[- ]?)?0?1[016789][ -]?\d{3,4}[ -]?\d{4}(?!\d)")
_KOREAN_RRN = re.compile(r"(?<!\d)\d{6}-[1-4]\d{6}(?!\d)")
_PLACEHOLDER = re.compile(
    r"(?i)^(?:your|replace|example|sample|dummy|placeholder|change[_-]?me|"
    r"changeme|todo|insert[_-]?here|<.*?>|x{3,}|\*{3,}|none|null|undefined)"
)
_CODE_REFERENCE = re.compile(
    r"(?i)^(?:self|cls|settings|config|options|credentials|environment|env|os|request|context|user|client)"
    r"(?:\.[A-Za-z_][A-Za-z0-9_]*)+$"
)


def _is_sensitive_path(path: str) -> bool:
    name = PurePosixPath(path).name.lower()
    if name == ".env.example":
        return False
    if name.startswith(".env"):
        return True
    if name in SENSITIVE_FILENAMES:
        return True
    return PurePosixPath(name).suffix.lower() in SENSITIVE_SUFFIXES


def _is_ignored_path(path: str) -> bool:
    parts = [part.lower() for part in PurePosixPath(path).parts]
    if any(part in IGNORED_DIRECTORIES for part in parts[:-1]):
        return True
    return PurePosixPath(path).name.lower() in IGNORED_FILENAMES


def _is_supported(path: str) -> bool:
    name = PurePosixPath(path).name.lower()
    return name in SUPPORTED_NAMES or PurePosixPath(name).suffix.lower() in SUPPORTED_EXTENSIONS


def _placeholder(value: str) -> bool:
    cleaned = value.strip().strip("'\"").strip()
    return not cleaned or bool(_PLACEHOLDER.match(cleaned))


def _redact_text(path: str, text: str) -> tuple[str, tuple[SecretRedaction, ...]]:
    redactions: list[SecretRedaction] = []
    # Each re.sub pass matches offsets in the version of text at that point.
    # Build the line index only if at least one match needs a citation. Reset
    # it after every substitution because replacements change character offsets.
    line_starts: list[int] | None = None

    def line_number_at(offset: int) -> int:
        nonlocal line_starts
        if line_starts is None:
            line_starts = [0]
            line_starts.extend(match.end() for match in re.finditer("\n", text))
        return bisect_right(line_starts, offset)

    def replace_match(match: re.Match[str], kind: str, replacement: str) -> str:
        line_number = line_number_at(match.start())
        redactions.append(SecretRedaction(line_number, kind))
        return replacement + "\n" * match.group(0).count("\n")

    text, _ = _PRIVATE_KEY_BLOCK.subn(
        lambda match: replace_match(match, "private key", "<REDACTED PRIVATE KEY>"),
        text,
    )
    line_starts = None

    def replace_assignment(match: re.Match[str]) -> str:
        value = match.group("value") or match.group("bare")
        if len(value.strip()) < 12 or _placeholder(value):
            return match.group(0)
        if not match.group("quote") and _CODE_REFERENCE.fullmatch(value.strip()):
            return match.group(0)
        line_number = line_number_at(match.start())
        redactions.append(SecretRedaction(line_number, "credential assignment"))
        quote = match.group("quote")
        replacement = f"{quote}<REDACTED>{quote}" if quote else "<REDACTED>"
        return f"{match.group('prefix')}{replacement}"

    text, _ = _SECRET_ASSIGNMENT.subn(replace_assignment, text)
    line_starts = None

    for pattern, kind in _TOKEN_PATTERNS:
        def replace_token(match: re.Match[str], current_kind: str = kind) -> str:
            line_number = line_number_at(match.start())
            redactions.append(SecretRedaction(line_number, current_kind))
            if match.group(0).lower().startswith("bearer "):
                return "Bearer <REDACTED>"
            return "<REDACTED>"

        text, _ = pattern.subn(replace_token, text)
        line_starts = None

    def replace_personal(match: re.Match[str], kind: str) -> str:
        value = match.group(0)
        if kind == "email address":
            domain = value.rsplit("@", 1)[1].lower()
            if domain in {"example.com", "example.org", "example.net", "test.com"}:
                return value
        line_number = line_number_at(match.start())
        redactions.append(SecretRedaction(line_number, kind))
        return "<REDACTED>"

    text, _ = _EMAIL.subn(lambda match: replace_personal(match, "email address"), text)
    line_starts = None
    text, _ = _KOREAN_PHONE.subn(lambda match: replace_personal(match, "Korean phone number"), text)
    line_starts = None
    text, _ = _KOREAN_RRN.subn(lambda match: replace_personal(match, "Korean resident number"), text)

    if PurePosixPath(path).name.lower() == ".env.example":
        output: list[str] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            match = re.match(r"^(\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*)(.*)$", line)
            if match and _SENSITIVE_KEY.search(match.group(2)):
                raw_value = match.group(3).split("#", 1)[0].strip().strip("'\"")
                if raw_value and not _placeholder(raw_value) and raw_value != "<REDACTED>":
                    output.append(f"{match.group(1)}<REDACTED>")
                    redactions.append(SecretRedaction(line_number, "sensitive environment value"))
                    continue
            output.append(line)
        text = "\n".join(output)

    return text, tuple(redactions)


def _decode_source(path: str, raw: bytes) -> tuple[SourceFile | None, str | None]:
    if b"\x00" in raw:
        return None, "binary file"
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None, "not UTF-8 text"
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    sanitized, redactions = _redact_text(path, text)
    return SourceFile(path, sanitized, len(raw), redactions), None


def _validate_relative_path(raw_path: str) -> str:
    normalized = raw_path.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if (
        not normalized
        or len(normalized) > 512
        or re.search(r"[\x00-\x1f\x7f<>:\"|?*]", normalized)
        or normalized.startswith("/")
        or re.match(r"^[A-Za-z]:", normalized)
        or any(part in {"..", ""} for part in normalized.split("/"))
        or pure.is_absolute()
    ):
        raise InputError("ZIP에 안전하지 않은 파일 경로가 있습니다. 압축 파일을 해제하지 않았습니다.")
    return pure.as_posix()


def _read_checked_source(path: Path, observed: os.stat_result, max_bytes: int) -> bytes:
    """Read only the same bounded, non-linked regular file that was inspected.

    The descriptor and pathname are checked after opening and reading to
    reject ordinary file-replacement races. No customer code is executed.
    """
    def identity(value: os.stat_result) -> tuple[int, int, int, int]:
        return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)

    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    if (not stat.S_ISREG(observed.st_mode)
            or getattr(observed, "st_file_attributes", 0) & reparse
            or path.is_symlink() or observed.st_size > max_bytes):
        raise InputError("일반 로컬 소스 파일이 아니거나 파일 크기 제한을 초과했습니다.")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        opened = os.fstat(fd)
        if (not stat.S_ISREG(opened.st_mode)
                or getattr(opened, "st_file_attributes", 0) & reparse
                or path.is_symlink() or identity(opened) != identity(observed)):
            raise InputError("검사할 파일이 열리는 동안 변경되었습니다. 다시 미리보기를 실행하세요.")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            raw = stream.read(max_bytes + 1)
        after = os.fstat(fd)
        on_disk = path.lstat()
        if (len(raw) > max_bytes or path.is_symlink()
                or identity(after) != identity(observed)
                or identity(on_disk) != identity(observed)):
            raise InputError("검사할 파일이 읽히는 동안 변경되었습니다. 다시 미리보기를 실행하세요.")
        return raw
    finally:
        os.close(fd)


def _bundle_from_records(
    records: Iterable[tuple[str, bytes]],
    limits: InputLimits,
    warnings: list[str],
    excluded: list[str],
) -> CodeBundle:
    files: list[SourceFile] = []
    total_bytes = 0

    for path, raw in records:
        path = _validate_relative_path(path)
        if _is_ignored_path(path):
            excluded.append(path)
            continue
        if _is_sensitive_path(path):
            excluded.append(path)
            warnings.append(f"민감 파일을 읽지 않고 제외함: {path}")
            continue
        if not _is_supported(path):
            excluded.append(path)
            continue
        if len(raw) > limits.max_file_bytes:
            raise InputError(f"파일 크기 제한 초과: {path}")
        total_bytes += len(raw)
        if total_bytes > limits.max_total_bytes:
            raise InputError("프로젝트 전체 입력 크기 제한을 초과했습니다. 분석을 중단했습니다.")

        source, reason = _decode_source(path, raw)
        if source is None:
            excluded.append(path)
            warnings.append(f"텍스트로 읽을 수 없어 제외함 ({reason}): {path}")
            continue
        files.append(source)
        if source.redactions:
            warnings.append(
                f"비밀정보 형태의 값 {len(source.redactions)}개를 전송 전에 마스킹함: {path}"
            )

    if len(files) > limits.max_files:
        raise InputError(f"분석 가능한 파일이 {limits.max_files}개 제한을 초과했습니다.")
    if not files:
        raise InputError("지원되는 UTF-8 코드·설정 파일을 찾지 못했습니다.")
    files.sort(key=lambda item: item.path.casefold())
    if excluded:
        warnings.append(f"지원하지 않거나 제외된 파일: {len(excluded)}개")
    return CodeBundle(files, warnings, excluded, total_bytes)


def load_directory(root_path: str | Path, limits: InputLimits = InputLimits()) -> CodeBundle:
    original = Path(root_path).expanduser()
    if original.is_symlink():
        raise InputError("심볼릭 링크가 입력 경로입니다. 실제 폴더를 선택하세요.")
    try:
        root = original.resolve(strict=True)
    except OSError as error:
        raise InputError(f"입력 폴더를 찾을 수 없습니다: {root_path}") from error
    if not root.is_dir():
        raise InputError("입력 경로가 폴더가 아닙니다.")

    warnings: list[str] = []
    excluded: list[str] = []
    records: list[tuple[str, bytes]] = []
    candidate_count = 0

    for current, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        relative_directory = current_path.relative_to(root)
        depth = len(relative_directory.parts)
        if depth >= limits.max_depth:
            if dirnames:
                warnings.append(f"폴더 깊이 제한으로 하위 폴더를 생략함: {relative_directory.as_posix()}")
            dirnames[:] = []
        else:
            dirnames[:] = sorted(
                name for name in dirnames
                if name.lower() not in IGNORED_DIRECTORIES
                and not (current_path / name).is_symlink()
            )

        for filename in sorted(filenames):
            file_path = current_path / filename
            relative_path = file_path.relative_to(root).as_posix()
            if file_path.is_symlink():
                excluded.append(relative_path)
                warnings.append(f"심볼릭 파일을 읽지 않고 제외함: {relative_path}")
                continue
            if _is_sensitive_path(relative_path) or _is_ignored_path(relative_path):
                excluded.append(relative_path)
                if _is_sensitive_path(relative_path):
                    warnings.append(f"민감 파일을 읽지 않고 제외함: {relative_path}")
                continue
            if not _is_supported(relative_path):
                excluded.append(relative_path)
                continue
            candidate_count += 1
            if candidate_count > limits.max_files:
                raise InputError(f"분석 가능한 파일이 {limits.max_files}개 제한을 초과했습니다.")
            try:
                file_stat = file_path.lstat()
                if not stat.S_ISREG(file_stat.st_mode):
                    excluded.append(relative_path)
                    warnings.append(f"일반 파일이 아니어서 읽지 않고 제외함: {relative_path}")
                    continue
                size = file_stat.st_size
                if size > limits.max_file_bytes:
                    raise InputError(f"파일 크기 제한 초과: {relative_path}")
                if sum(len(raw) for _, raw in records) + size > limits.max_total_bytes:
                    raise InputError("프로젝트 전체 입력 크기 제한을 초과했습니다. 분석을 중단했습니다.")
                raw = _read_checked_source(file_path, file_stat, limits.max_file_bytes)
            except OSError as error:
                raise InputError(f"파일을 안전하게 읽지 못했습니다: {relative_path}") from error
            if len(raw) > limits.max_file_bytes:
                raise InputError(f"파일 크기 제한 초과: {relative_path}")
            records.append((relative_path, raw))

    return _bundle_from_records(records, limits, warnings, excluded)


def load_zip(zip_path: str | Path, limits: InputLimits = InputLimits()) -> CodeBundle:
    archive_path = Path(zip_path).expanduser()
    if archive_path.is_symlink():
        raise InputError("심볼릭 링크 ZIP은 지원하지 않습니다.")
    try:
        archive_size = archive_path.stat().st_size
    except OSError as error:
        raise InputError(f"ZIP 파일을 찾을 수 없습니다: {zip_path}") from error
    if archive_size > limits.max_archive_bytes:
        raise InputError("압축 파일 크기 제한을 초과했습니다.")

    warnings: list[str] = []
    excluded: list[str] = []
    records: list[tuple[str, bytes]] = []
    seen_paths: set[str] = set()
    declared_total = 0

    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            infos = archive.infolist()
            if len(infos) > limits.max_archive_entries:
                raise InputError("ZIP 내부 항목 수 제한을 초과했습니다.")
            for info in infos:
                relative_path = _validate_relative_path(
                    info.filename.rstrip("/") if info.is_dir() else info.filename
                )
                if relative_path in seen_paths:
                    raise InputError("ZIP에 중복 파일 경로가 있습니다. 모호한 입력을 거부했습니다.")
                seen_paths.add(relative_path)
                if info.is_dir():
                    continue
                unix_mode = info.external_attr >> 16
                if stat.S_IFMT(unix_mode) == stat.S_IFLNK:
                    excluded.append(relative_path)
                    warnings.append(f"ZIP 내부 심볼릭 링크를 제외함: {relative_path}")
                    continue
                if info.flag_bits & 0x1:
                    excluded.append(relative_path)
                    warnings.append(f"암호화된 파일을 제외함: {relative_path}")
                    continue
                if _is_sensitive_path(relative_path) or _is_ignored_path(relative_path):
                    excluded.append(relative_path)
                    if _is_sensitive_path(relative_path):
                        warnings.append(f"민감 파일을 읽지 않고 제외함: {relative_path}")
                    continue
                if not _is_supported(relative_path):
                    excluded.append(relative_path)
                    continue
                if info.file_size > limits.max_file_bytes:
                    raise InputError(f"ZIP 내부 파일 크기 제한 초과: {relative_path}")
                declared_total += info.file_size
                if declared_total > limits.max_total_bytes:
                    raise InputError("압축 해제 후 전체 크기 제한을 초과합니다. 분석을 중단했습니다.")
                if len(records) >= limits.max_files:
                    raise InputError(f"분석 가능한 파일이 {limits.max_files}개 제한을 초과했습니다.")
                with archive.open(info, "r") as stream:
                    raw = stream.read(limits.max_file_bytes + 1)
                if len(raw) > limits.max_file_bytes or len(raw) != info.file_size:
                    raise InputError(f"ZIP 내부 파일 크기가 안전 한도를 벗어남: {relative_path}")
                records.append((relative_path, raw))
    except zipfile.BadZipFile as error:
        raise InputError("정상적인 ZIP 파일이 아닙니다.") from error
    except (zlib.error, EOFError, RuntimeError) as error:
        raise InputError("ZIP 내부 파일을 안전하게 해제하지 못했습니다.") from error
    except OSError as error:
        raise InputError("ZIP 파일을 읽지 못했습니다.") from error

    return _bundle_from_records(records, limits, warnings, excluded)


def load_single_file(file_path: str | Path, limits: InputLimits = InputLimits()) -> CodeBundle:
    path = Path(file_path).expanduser()
    if path.is_symlink():
        raise InputError("심볼릭 링크 파일은 지원하지 않습니다.")
    try:
        resolved = path.resolve(strict=True)
        size = resolved.stat().st_size
    except OSError as error:
        raise InputError(f"입력 파일을 찾을 수 없습니다: {file_path}") from error
    if not resolved.is_file():
        raise InputError("입력 경로가 일반 파일이 아닙니다.")
    if size > limits.max_file_bytes or size > limits.max_total_bytes:
        raise InputError("단일 파일 크기 제한을 초과했습니다.")
    if _is_sensitive_path(resolved.name):
        raise InputError("민감 파일은 읽지 않습니다. 비밀정보를 제거한 사본을 선택하세요.")
    if not _is_supported(resolved.name):
        raise InputError("지원하지 않는 파일 형식입니다.")
    try:
        observed = resolved.lstat()
        raw = _read_checked_source(resolved, observed, limits.max_file_bytes)
    except OSError as error:
        raise InputError("입력 파일을 안전하게 읽지 못했습니다.") from error
    warnings: list[str] = []
    excluded: list[str] = []
    return _bundle_from_records([(resolved.name, raw)], limits, warnings, excluded)


def load_path(path: str | Path, limits: InputLimits = InputLimits()) -> CodeBundle:
    candidate = Path(path).expanduser()
    if candidate.is_dir():
        return load_directory(candidate, limits)
    if candidate.suffix.lower() == ".zip":
        return load_zip(candidate, limits)
    return load_single_file(candidate, limits)


def bundle_from_text(
    text: str,
    filename: str = "stdin.py",
    limits: InputLimits = InputLimits(),
) -> CodeBundle:
    # Tk clipboard/paste strings can contain an unpaired surrogate. File and
    # ZIP readers reject invalid UTF-8; treat memory input the same way rather
    # than leaking an internal UnicodeEncodeError into the desktop workflow.
    try:
        raw = text.encode("utf-8")
    except UnicodeEncodeError:
        raise InputError("붙여넣은 내용에 UTF-8로 저장할 수 없는 문자가 있습니다. 내용을 수정한 뒤 다시 시도하세요.") from None
    if len(raw) > min(limits.max_file_bytes, limits.max_total_bytes):
        raise InputError("붙여넣은 입력이 파일 크기 제한을 초과했습니다.")
    filename = _validate_relative_path(filename)
    if not _is_supported(filename):
        raise InputError("지원하지 않는 파일 형식입니다. --filename으로 확장자를 지정하세요.")
    return _bundle_from_records([(filename, raw)], limits, [], [])
