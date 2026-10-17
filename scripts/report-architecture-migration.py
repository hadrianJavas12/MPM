"""Report every original path without changing the immutable P0 inventory.

Existence/hashes describe ownership progress, never runtime or scientific PASS.
Run from any directory: python scripts/report-architecture-migration.py
"""
import argparse
import collections
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / "docs/architecture"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="docs/architecture/FILE_MIGRATION_RESULT.json")
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    output.relative_to(ROOT)
    baseline_path = ARCH / "FILE_MIGRATION_MATRIX.json"
    assert output != baseline_path
    original_hash = digest(baseline_path)
    baseline = read(baseline_path)
    mappings = {}
    for row in read(ARCH / "MIGRATION_APPROVALS.json")["approvals"]:
        mappings[row["source_path"]] = [target["path"] for target in row["targets"]]
    for row in read(ARCH / "P2_COMPACT_MIGRATION.json")["sources"]:
        if row.get("compact_ordered_targets"):
            mappings[row["source_path"]] = row["compact_ordered_targets"]
    for row in read(ARCH / "P3_DIAGNOSTICS_MIGRATION.json")["ordered_groups"]:
        mappings.setdefault("framework/components/diagnostics.lisp", []).append(row["target_path"])
    for row in read(ARCH / "P4_ORCHESTRATION_MIGRATION.json")["framework_records"]:
        if row["target_paths"]:
            mappings.setdefault(row["source_path"], row["target_paths"])
    for row in read(ARCH / "P5_ENGINE_MIGRATION.json")["files"]:
        mappings[row["source"]] = [row["target"]]
    records = []
    for row in baseline["records"]:
        source = row["source_path"]
        current = digest(ROOT / source)
        targets = list(dict.fromkeys(mappings.get(source, [])))
        owners = [{"path": p, "sha256": digest(ROOT / p)} for p in targets]
        status = ("MAPPED_OWNERS_PRESENT" if all(p["sha256"] for p in owners) else "MAPPED_OWNERS_PENDING") if owners else (
            "RETAINED_UNCHANGED" if current == row["actual_source_sha256"] else
            "RETAINED_MODIFIED" if current else "MISSING_REQUIRES_REVIEW")
        records.append({"source": source, "originalSha256": row["actual_source_sha256"],
                        "currentSha256": current, "status": status, "mappedOwners": owners})
    paths = [row["source"] for row in records]
    assert len(paths) == len(set(paths)) == baseline["tracked_count_at_capture"]
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    result = {"scope": "Complete path/hash ownership ledger; existence is not validation",
              "captureHead": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "originalInventorySha256": original_hash, "originalPaths": len(records),
              "counts": dict(collections.Counter(row["status"] for row in records)),
              "records": records, "newTrackedPaths": sorted(set(filter(None, tracked)) - set(paths)),
              "runtimeValidation": "See stage evidence and STATUS.md; not inferred by this report"}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    assert digest(baseline_path) == original_hash
    print(json.dumps({"originalPaths": len(records), "counts": result["counts"]}))


if __name__ == "__main__":
    main()
