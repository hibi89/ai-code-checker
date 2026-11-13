"""PROOFQA AX P50: local-only, evidence-bound Code Checker adapter.

Developer preview; no customer-code execution, uploads, Graphify or browser.
Importing this module has no scanning or external side effects.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import unicodedata
import zipfile
from pathlib import Path

from code_input import InputError
from offline_core import scan_path
from offline_report import build_report, render_html
from output_safety import validate_output_location

CONTRACT = "proofqa.p50.v1"
MAX_ARCHIVE_BYTES = 20 * 1024 * 1024
MAX_EXPANDED_BYTES = 8 * 1024 * 1024
MAX_ENTRIES = 1000
OUTPUT_FILES = ("case.json", "report.html")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_digest(source: Path) -> str:
    size = source.stat().st_size
    if size > MAX_ARCHIVE_BYTES or size < 1:
        raise InputError("ZIP 크기가 허용 범위를 벗어났습니다.")
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    if source.stat().st_size != size:
        raise InputError("입력 크기가 검사 도중 바뀌었습니다.")
    return digest.hexdigest()


def _safe_zip_preflight(source: Path) -> None:
    """Check central directory without extracting or executing archive members."""
    seen: set[str] = set()
    total = 0
    files = 0
    try:
        with zipfile.ZipFile(source, "r") as archive:
            infos = archive.infolist()
            if not infos or len(infos) > MAX_ENTRIES:
                raise InputError("빈 ZIP 또는 엔트리 수 초과.")
            for info in infos:
                raw = info.filename
                parts = raw.rstrip("/").split("/")
                if (not raw or raw.startswith("/") or chr(92) in raw
                        or chr(0) in raw or any(p in {"", ".", ".."} for p in parts)
                        or ":" in parts[0]):
                    raise InputError("위험한 ZIP 내부 경로를 거부했습니다.")
                key = unicodedata.normalize("NFC", raw.rstrip("/")).casefold()
                if key in seen:
                    raise InputError("ZIP 내부 경로 중복/대소문자 충돌.")
                seen.add(key)
                mode = (info.external_attr >> 16) & stat.S_IFMT(0o177777)
                kind = stat.S_IFMT(mode)
                if kind not in (0, stat.S_IFREG, stat.S_IFDIR):
                    raise InputError("ZIP 링크·장치 등 비정규 엔트리 거부.")
                if info.flag_bits & 1:
                    raise InputError("암호화 ZIP은 지원하지 않습니다.")
                if info.is_dir():
                    continue
                files += 1
                if info.file_size > 1024 * 1024:
                    raise InputError("ZIP 단일 파일 압축 해제 크기 초과.")
                total += info.file_size
                if total > MAX_EXPANDED_BYTES:
                    raise InputError("ZIP 전체 압축 해제 크기 초과.")
                if info.file_size > 1024 * 1024 // 2 and (
                    info.file_size > 100 * max(1, info.compress_size)
                ):
                    raise InputError("ZIP 비정상 압축비 거부.")
            if not files:
                raise InputError("검사할 파일이 없는 ZIP.")
    except (zipfile.BadZipFile, zipfile.LargeZipFile, EOFError) as exc:
        raise InputError("잘못되었거나 지원하지 않는 ZIP.") from exc


def _case_document(report: object, source_sha256: str) -> dict[str, object]:
    scan = report.scan
    rows = []
    for row in report.findings:
        item = row.finding
        rows.append({
            "rule_id": row.rule_id,
            "source_path": item.file_path,
            "line": item.start_line,
            "evidence_line_matched": row.verified,
            "status": "NEEDS_VALIDATION",
            "candidate_severity": item.severity,
            "confirmed_vulnerability": False,
        })
    return {
        "contract": CONTRACT,
        "source": {"type": "local-zip", "sha256": source_sha256},
        "adapter": {"engine": "ai-code-checker/offline_core", "network": False,
                    "source_execution": False, "graph": "NOT_RUN",
                    "browser": "NOT_RUN", "security_audit": "NOT_RUN"},
        "scope": {
            "status": report.status, "counts": scan.counts,
            "coverage": [
                {"path": c.path, "status": c.status, "analyzer": c.analyzer,
                 "reason": c.reason} for c in scan.coverage
            ], "validation_issues": list(report.validation_issues),
            "warnings": list(scan.warnings),
            "pruned_subtrees": list(scan.pruned_subtrees),
        },
        "findings": rows,
        "delivery": {"release_state": "HOLD", "customer_accepted": False,
                     "qualified_as_security_certification": False},
    }


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
            + "\n").encode("utf-8")


def run_p50(source_zip: str | Path, output_root: str | Path) -> tuple[Path, str]:
    """Generate three create-only local files. A partial scan is never 'secure'."""
    source = Path(source_zip)
    if not source.is_file() or source.suffix.lower() != ".zip":
        raise InputError("P50은 로컬 ZIP 프로젝트만 지원합니다.")
    # Existing engine rejects symlink/network-device input paths.
    from input_safety import validate_offline_input_path
    source = validate_offline_input_path(source)
    before = _read_digest(source)
    _safe_zip_preflight(source)
    scan = scan_path(source)
    after = _read_digest(source)
    if before != after:
        raise InputError("검사 중 ZIP 원본 바이트가 변경되었습니다.")
    report = build_report(scan)
    doc = _case_document(report, before)
    html = render_html(report).replace(
        "</h1>", "</h1><p>PROOFQA AX P50 · input SHA256: "
        + before + " · Graph/Browser NOT_RUN · RELEASE HOLD</p>", 1
    ).encode("utf-8")
    outputs = {"case.json": _json_bytes(doc), "report.html": html}
    manifest = {
        "contract": CONTRACT, "input_sha256": before,
        "files": {key: _sha256(value) for key, value in outputs.items()},
        "release_state": "HOLD",
    }
    root = validate_output_location(output_root)
    root.mkdir(parents=True, exist_ok=True)
    folder = root / ("proofqa-" + before[:16])
    folder.mkdir(exist_ok=False)
    for name, data in (*outputs.items(), ("manifest.json", _json_bytes(manifest))):
        with (folder / name).open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    verify_delivery(folder)
    return folder, report.status


def verify_delivery(folder: str | Path) -> bool:
    """Read-only independent manifest/schema/byte-integrity check (not QA approval)."""
    directory = Path(folder)
    expected = set(OUTPUT_FILES) | {"manifest.json"}
    if (not directory.is_dir() or directory.is_symlink()
            or {p.name for p in directory.iterdir()} != expected):
        raise InputError("납품 파일 집합이 불일치합니다.")
    for name in expected:
        p = directory / name
        if not p.is_file() or p.is_symlink():
            raise InputError("납품 파일 형식이 불안전합니다.")
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    case = json.loads((directory / "case.json").read_text(encoding="utf-8"))
    if (manifest.get("contract") != CONTRACT or case.get("contract") != CONTRACT
            or manifest.get("release_state") != "HOLD"
            or case.get("delivery", {}).get("release_state") != "HOLD"
            or manifest.get("input_sha256") != case.get("source", {}).get("sha256")
            or set(manifest.get("files", {})) != set(OUTPUT_FILES)):
        raise InputError("납품 계약/원본 SHA/출시 HOLD 검증 실패.")
    for name in OUTPUT_FILES:
        if _sha256((directory / name).read_bytes()) != manifest["files"][name]:
            raise InputError("납품 파일 SHA256 변조가 감지되었습니다.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="PROOFQA P50 local preview (not security certification)")
    parser.add_argument("project_zip")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    try:
        folder, status = run_p50(args.project_zip, args.output_dir)
    except (InputError, OSError, ValueError, zipfile.BadZipFile) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print(json.dumps({"status": status, "release_state": "HOLD",
                      "output": str(folder)}, ensure_ascii=False))
    return 0 if status == "complete" else 3


if __name__ == "__main__":
    raise SystemExit(main())
