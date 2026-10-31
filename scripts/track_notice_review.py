"""Local, exact-EXE progress tracking for unresolved NOTICE review rows.

This records investigation progress, NOT license compliance, copyright ownership,
redistribution permission or customer release approval. No network or uploads.
Never embed full LICENSE texts, customer code, executable contents or OS paths.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from scripts.build_notice_review_queue import _verify_exe
from scripts.render_notice_review_worksheet import render_review_worksheet
from scripts.verify_upstream_tcl_tk_license import _safe_read

FORMAT = "code_checker_exact_exe_notice_review_progress_v1"
SUMMARY_FORMAT = "code_checker_exact_exe_notice_progress_summary_v1"
STAGES = ("UNREVIEWED", "INVESTIGATING", "REFERENCES_FOUND", "NEEDS_HUMAN_DECISION")
MAX_QUEUE_BYTES = 8 * 1024 * 1024
MAX_PROGRESS_BYTES = 2 * 1024 * 1024
BLOCK_FLAGS = (
    "customer_release_ready",
    "license_compliance_certified",
    "third_party_notice_ready",
    "vendor_or_binary_ownership_certified",
)


def _duplicate_key_guard(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _read_json(path: Path, limit: int) -> dict:
    data = json.loads(_safe_read(path, limit), object_pairs_hook=_duplicate_key_guard)
    if not isinstance(data, dict):
        raise ValueError("Expected JSON object")
    return data


def _queue_id(queue: dict) -> str:
    canonical = json.dumps(
        queue, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _validate_queue(queue: dict, exe: Path) -> list[str]:
    # The existing printable worksheet performs full roster, allowed-evidence,
    # ledger-accounting and permanent BLOCKED-flag validation.
    render_review_worksheet(queue)
    if _verify_exe(exe, queue["exe_sha256"]) != queue["exe_bytes"]:
        raise ValueError("EXE byte count differs from review queue")
    names = [entry["archive_entry"]
             for entry in queue["unresolved_entries_requiring_review"]]
    if not names or len(set(names)) != len(names):
        raise ValueError("Review roster is incomplete or ambiguous")
    return names


def create_progress(queue: dict, exe: Path) -> dict:
    names = _validate_queue(queue, exe)
    return {
        "format": FORMAT,
        "exe_sha256": queue["exe_sha256"],
        "exe_bytes": queue["exe_bytes"],
        "queue_sha256": _queue_id(queue),
        "entry_count": len(names),
        "entries": [
            {"archive_entry": name, "review_stage": "UNREVIEWED"}
            for name in names
        ],
        "customer_release_ready": False,
        "license_compliance_certified": False,
        "third_party_notice_ready": False,
        "vendor_or_binary_ownership_certified": False,
    }


def summarize_progress(queue: dict, exe: Path, progress: dict) -> dict:
    names = _validate_queue(queue, exe)
    expected = {
        "format", "exe_sha256", "exe_bytes", "queue_sha256",
        "entry_count", "entries", *BLOCK_FLAGS,
    }
    if (not isinstance(progress, dict) or set(progress) != expected
            or progress["format"] != FORMAT
            or progress["exe_sha256"] != queue["exe_sha256"]
            or type(progress["exe_bytes"]) is not int
            or progress["exe_bytes"] != queue["exe_bytes"]
            or progress["queue_sha256"] != _queue_id(queue)
            or type(progress["entry_count"]) is not int
            or progress["entry_count"] != len(names)
            or any(progress[key] is not False for key in BLOCK_FLAGS)
            or not isinstance(progress["entries"], list)
            or len(progress["entries"]) != len(names)):
        raise ValueError("Stale, incomplete or prematurely approved review progress")
    counts: Counter[str] = Counter()
    for name, item in zip(names, progress["entries"]):
        if (not isinstance(item, dict)
                or set(item) != {"archive_entry", "review_stage"}
                or item["archive_entry"] != name
                or type(item["review_stage"]) is not str
                or item["review_stage"] not in STAGES):
            raise ValueError("Unexpected archive entry, order or review stage")
        counts[item["review_stage"]] += 1
    return {
        "format": SUMMARY_FORMAT,
        "exe_sha256": queue["exe_sha256"],
        "exe_bytes": queue["exe_bytes"],
        "queue_sha256": _queue_id(queue),
        "unresolved_entry_count": len(names),
        "investigation_stage_counts": {stage: counts[stage] for stage in STAGES},
        "human_review_still_required": True,
        "original_license_and_redistribution_rights_not_certified": True,
        "human_buyer_windows_acceptance_not_certified": True,
        "customer_release_ready": False,
        "status": "REVIEW_PROGRESS_ONLY_RETAIL_RELEASE_BLOCKED",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Track local legal review work, never certify release")
    parser.add_argument("--queue", required=True, type=Path)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--progress", type=Path,
                        help="Existing locally edited progress JSON; without it create a template")
    args = parser.parse_args(argv)
    try:
        inputs = [args.queue, args.exe]
        if args.progress is not None:
            inputs.append(args.progress)
        if (args.out.suffix.lower() != ".json"
                or args.out in inputs or len(set(inputs)) != len(inputs)
                or args.out.exists() or args.out.is_symlink()
                or not args.out.parent.is_dir() or args.out.parent.is_symlink()):
            raise ValueError("Fresh distinct private JSON output required")
        queue = _read_json(args.queue, MAX_QUEUE_BYTES)
        if args.progress is None:
            result = create_progress(queue, args.exe)
        else:
            progress = _read_json(args.progress, MAX_PROGRESS_BYTES)
            result = summarize_progress(queue, args.exe, progress)
        serialized = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)
        with args.out.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(serialized + "\n")
        print("NOTICE_REVIEW_PROGRESS_TRACKER_OK")
        print("EXE_BYTES_HASH_MATCH=True")
        print("REVIEW_ROWS=" + str(result.get("entry_count", result.get("unresolved_entry_count"))))
        print("LICENSE_COMPLIANCE_AND_CUSTOMER_RELEASE=False")
        return 0
    except (OSError, ValueError, TypeError, KeyError, AttributeError, json.JSONDecodeError):
        print("NOTICE_REVIEW_PROGRESS_TRACKER_INVALID")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
