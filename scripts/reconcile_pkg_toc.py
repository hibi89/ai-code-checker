"""P0-H: safely investigate P0-G archive items absent from the EXE TOC.

PyInstaller PKG TOC entries are only local build-stage metadata. This module
cannot establish legal owner, source rights, origin of a runtime-generated
entry, or customer-release approval. No bundled/customer code is executed.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from scripts.reconcile_exe_toc import parse_exe_toc
from scripts.reconcile_native_build import normalize


def reconcile_pkg_toc(previous: dict, audit: dict,
                      pkg_entries: list[tuple[str, str, bool]]) -> dict:
    """Require exact EXE identity and preservation of the P0-G evidence ledger."""
    if any(previous.get(flag) is not False for flag in (
            "customer_release_ready", "legal_notice_approved",
            "license_compliance_certified")):
        raise ValueError("P0-G release gates must be blocked")
    if any(audit.get(flag) is not False for flag in (
            "customer_release_ready", "third_party_notice_ready_to_distribute",
            "license_compliance_certified")):
        raise ValueError("P0-D release gates must be blocked")
    sha = previous.get("exe_sha256")
    if (not isinstance(sha, str) or len(sha) != 64
            or audit.get("exe_sha256") != sha):
        raise ValueError("P0-D / P0-G EXE SHA mismatch")
    records = previous["records"]
    if (len(records) != previous["previously_not_unique_analysis_claims"]
            or previous["exe_toc_entry_claims"]
            + previous["ambiguous_exe_toc_claims"]
            + previous["without_exe_toc_claims"] != len(records)):
        raise ValueError("Prior EXE TOC accounting mismatch")
    missing = [row for row in records if row["exe_toc_evidence"] == "no_exe_toc_entry_claim"]
    if len(missing) != previous["without_exe_toc_claims"]:
        raise ValueError("Prior unmatched count mismatch")
    top = {
        normalize(row["name"]): str(row["typecode"])
        for row in audit["archive"]["top_level"]
    }
    if len(top) != len(audit["archive"]["top_level"]):
        raise ValueError("Duplicate actual EXE archive names")
    pkg: dict[str, set[tuple[str, bool]]] = {}
    for name, entry_type, source_path_present in pkg_entries:
        pkg.setdefault(normalize(name), set()).add((entry_type, source_path_present))

    outcomes = []
    counts: Counter[str] = Counter()
    seen = set()
    for row in missing:
        name = row["name"]
        key = normalize(name)
        if key in seen or key not in top or top[key] != row["carchive_typecode"]:
            raise ValueError("Unknown, duplicated or mismatched actual CArchive entry")
        seen.add(key)
        matches = sorted(pkg.get(key, ()))
        if not matches:
            state = "no_pkg_toc_record"
        elif len(matches) > 1:
            state = "ambiguous_pkg_toc_records"
        else:
            state = "unique_pkg_toc_record_claim_only"
        counts[state] += 1
        outcomes.append({
            "name": name,
            "carchive_typecode": top[key],
            "pkg_toc_evidence": state,
            "pkg_toc_record_types": sorted({kind for kind, _ in matches}),
            "pkg_toc_source_path_present": any(src for _, src in matches),
            "copyright_owner_verified": False,
            "license_approved": False,
        })
    return {
        "format": "code_checker_p0h_pkg_toc_metadata_v1",
        "exe_sha256": sha,
        "previously_unmatched_exe_toc": len(missing),
        "pkg_unique_record_claims": counts["unique_pkg_toc_record_claim_only"],
        "pkg_ambiguous_record_claims": counts["ambiguous_pkg_toc_records"],
        "pkg_no_record_claims": counts["no_pkg_toc_record"],
        "records": outcomes,
        "all_prior_unmatched_accounted_for": len(outcomes) == len(missing),
        "build_source_paths_excluded": True,
        "metadata_not_owner_or_license_proof": True,
        "customer_release_ready": False,
        "legal_notice_approved": False,
        "license_compliance_certified": False,
        "status": "PKG_BUILD_METADATA_ONLY_LICENSE_REVIEW_REQUIRED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Locally check frozen EXE PKG TOC only")
    parser.add_argument("--prior", required=True)
    parser.add_argument("--audit", required=True)
    parser.add_argument("--pkg-toc", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        output = Path(args.out)
        if output.exists() or output.is_symlink() or not output.parent.is_dir():
            raise ValueError("Refuse overwrite or missing output directory")
        prior = json.loads(Path(args.prior).read_text(encoding="utf-8"))
        audit = json.loads(Path(args.audit).read_text(encoding="utf-8"))
        records = parse_exe_toc(Path(args.pkg_toc))
        evidence = reconcile_pkg_toc(prior, audit, records)
        output.write_text(json.dumps(evidence, ensure_ascii=False,
                                     sort_keys=True, indent=2), encoding="utf-8")
        print("PKG_TOC_METADATA_CHECK_PASS")
        print("PREVIOUS_NO_EXE_TOC_CLAIMS=" + str(evidence["previously_unmatched_exe_toc"]))
        print("PKG_UNIQUE_NAME_CLAIMS=" + str(evidence["pkg_unique_record_claims"]))
        print("PKG_AMBIGUOUS=" + str(evidence["pkg_ambiguous_record_claims"]))
        print("PKG_NO_CLAIM=" + str(evidence["pkg_no_record_claims"]))
        print("VENDOR_LICENSE_APPROVED=False")
        print("COMMERCIAL_RELEASE=NOT_APPROVED")
        return 0
    except (ValueError, OSError, SyntaxError, TypeError, KeyError, RecursionError) as exc:
        print("PKG_TOC_CHECK_FAILED=" + type(exc).__name__)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
