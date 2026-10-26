"""P0-G: cross-check P0-F unmatched frozen entries against PyInstaller EXE TOC.

Only bounded literal metadata is read. An EXE packaging record is NOT proof of
component ownership, redistribution permission, bundled notice, or license.
No source paths, customer files, or EXE bytes are emitted or executed.
"""
from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from pathlib import Path

from scripts.reconcile_native_build import normalize

MAX_TOC_BYTES = 16 * 1024 * 1024
MAX_VISITS = 600000
MAX_RECORDS = 30000


def parse_exe_toc(path: Path) -> list[tuple[str, str, bool]]:
    """Parse EXE-00.toc as data, retaining only safe destination/type/path-presence."""
    if not path.is_file() or path.stat().st_size > MAX_TOC_BYTES:
        raise ValueError("Missing or oversized EXE-00.toc")
    parsed = ast.literal_eval(path.read_text(encoding="utf-8"))
    found: list[tuple[str, str, bool]] = []
    visits = [0]

    def walk(value, depth: int) -> None:
        visits[0] += 1
        if depth > 80 or visits[0] > MAX_VISITS:
            raise ValueError("EXE TOC nesting or size exceeded")
        if isinstance(value, (tuple, list)):
            if (len(value) == 3 and isinstance(value[0], str)
                    and (isinstance(value[1], str) or value[1] is None)
                    and isinstance(value[2], str)):
                try:
                    dest = normalize(value[0])
                except ValueError:
                    return  # Not a safe relative archive name; no equivalence claim.
                if len(value[2]) > 80:
                    raise ValueError("Unexpected EXE TOC type length")
                found.append((dest, value[2], isinstance(value[1], str)))
                if len(found) > MAX_RECORDS:
                    raise ValueError("Too many EXE source records")
            else:
                for part in value:
                    walk(part, depth + 1)
        elif isinstance(value, dict):
            for part in value.values():
                walk(part, depth + 1)

    walk(parsed, 0)
    return found


def reconcile_exe_toc(previous: dict, audit: dict, records: list[tuple[str, str, bool]]) -> dict:
    """Count every still-uncertain P0-F entry, never promote a name to an owner."""
    if (previous.get("customer_release_ready") is not False
            or previous.get("legal_notice_approved") is not False):
        raise ValueError("P0-F release flags must remain blocked")
    if (audit.get("customer_release_ready") is not False
            or audit.get("license_compliance_certified") is not False
            or audit.get("third_party_notice_ready_to_distribute") is not False):
        raise ValueError("P0-D legal release flags must remain blocked")
    sha = previous.get("exe_sha256")
    if not isinstance(sha, str) or len(sha) != 64 or sha != audit.get("exe_sha256"):
        raise ValueError("EXE identity mismatch")

    rows = previous["records"]
    remaining = [
        row for row in rows
        if row["build_record_evidence"] != "recorded_build_source_path_candidate"
    ]
    if (len(rows) != previous["previous_unresolved_archive_entries"]
            or len(remaining) != previous["not_uniquely_recorded_in_build_toc"]):
        raise ValueError("P0-F accounting mismatch")
    audit_names = {
        normalize(row["name"]): str(row["typecode"])
        for row in audit["archive"]["top_level"]
    }
    lookup: dict[str, set[tuple[str, bool]]] = {}
    for name, kind, has_source in records:
        lookup.setdefault(normalize(name), set()).add((kind, has_source))
    seen = set()
    output = []
    counts = Counter()
    for row in remaining:
        name = row["name"]
        key = normalize(name)
        if key in seen or key not in audit_names:
            raise ValueError("Duplicate or non-observed EXE entry")
        seen.add(key)
        candidates = sorted(lookup.get(key, ()))
        if len(candidates) == 1:
            state = "unique_exe_build_toc_entry_claim_only"
        elif candidates:
            state = "ambiguous_exe_build_toc_entries"
        else:
            state = "no_exe_toc_entry_claim"
        counts[state] += 1
        output.append({
            "name": name,
            "carchive_typecode": audit_names[key],
            "exe_toc_evidence": state,
            "exe_toc_types": sorted({kind for kind, _ in candidates}),
            "exe_toc_source_path_present": any(has_src for _, has_src in candidates),
            "owner_or_license_verified": False,
        })
    return {
        "format": "code_checker_p0g_exe_toc_evidence_v1",
        "exe_sha256": sha,
        "previously_not_unique_analysis_claims": len(remaining),
        "exe_toc_entry_claims": counts["unique_exe_build_toc_entry_claim_only"],
        "ambiguous_exe_toc_claims": counts["ambiguous_exe_build_toc_entries"],
        "without_exe_toc_claims": counts["no_exe_toc_entry_claim"],
        "counts": dict(sorted(counts.items())),
        "records": output,
        "all_pending_entries_accounted_for": len(output) == len(remaining),
        "absolute_build_paths_excluded": True,
        "exe_toc_record_not_vendor_or_license_proof": True,
        "customer_release_ready": False,
        "legal_notice_approved": False,
        "license_compliance_certified": False,
        "status": "EXE_BUILD_METADATA_ONLY_LEGAL_REVIEW_REQUIRED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Local PyInstaller EXE TOC provenance; no extraction")
    parser.add_argument("--prior", required=True)
    parser.add_argument("--audit", required=True)
    parser.add_argument("--exe-toc", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        out = Path(args.out)
        if out.exists() or out.is_symlink() or not out.parent.is_dir():
            raise ValueError("Refuse overwrite or missing output directory")
        previous = json.loads(Path(args.prior).read_text(encoding="utf-8"))
        audit = json.loads(Path(args.audit).read_text(encoding="utf-8"))
        records = parse_exe_toc(Path(args.exe_toc))
        evidence = reconcile_exe_toc(previous, audit, records)
        out.write_text(json.dumps(evidence, ensure_ascii=False, sort_keys=True, indent=2),
                       encoding="utf-8")
        print("EXE_TOC_METADATA_REVIEW_PASS")
        print("STILL_UNIQUE_ANALYSIS_MISSING=" + str(evidence["previously_not_unique_analysis_claims"]))
        print("EXE_TOC_UNIQUE_CLAIMS=" + str(evidence["exe_toc_entry_claims"]))
        print("EXE_TOC_AMBIGUOUS=" + str(evidence["ambiguous_exe_toc_claims"]))
        print("EXE_TOC_NO_CLAIM=" + str(evidence["without_exe_toc_claims"]))
        print("LICENSE_AND_VENDOR_VERIFIED=False")
        print("COMMERCIAL_RELEASE=NOT_APPROVED")
        return 0
    except (OSError, ValueError, TypeError, KeyError, SyntaxError, RecursionError) as exc:
        print("EXE_TOC_METADATA_REVIEW_FAILED=" + type(exc).__name__)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
