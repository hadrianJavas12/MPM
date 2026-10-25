"""Planned saved-byte comparison; adapted from compare-unnotched-fixed-controls.py.

No native/test/replay/audit/render execution. Unlike the historical fixed-count
script, this derives the new source count from its actual frozen manifest and
retains a FAIL result before returning nonzero when output bytes differ.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "output/unnotched-gravity-2026-10-25/native-output-fixed-001"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path):
    payload = path.read_bytes()
    return {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--new-run", type=Path, required=True)
    args = parser.parse_args()
    new = args.new_run.resolve()
    target = new / "comparison-to-default-strict-baseline.json"
    if target.exists():
        raise RuntimeError("Preserve existing comparison; refuse overwrite")
    manifest = read(new / "source/source-manifest.json")
    rows = manifest["files"]
    expected = {row["path"]: row for row in rows}
    if len(expected) != len(rows):
        raise RuntimeError("Duplicate frozen source members")
    failures = []
    for relative, row in expected.items():
        path = (new / relative).resolve()
        if not path.is_relative_to((new / "source").resolve()):
            raise RuntimeError("Source escaped its snapshot")
        if digest(path) != {key: row[key] for key in ("bytes", "sha256")}:
            failures.append("Frozen source bytes changed: " + relative)
    for phase in ("before", "after"):
        actual = {row["path"]: row["sha256"] for row in read(new / f"source-proof-{phase}.json")["files"]}
        if actual != {relative: row["sha256"] for relative, row in expected.items()}:
            failures.append("Frozen source proof differs: " + phase)
    result = read(new / "result.json")
    if not (result["passed"] and result["mode"] == "output" and result["passedCount"] == 4
            and result["physicalUpdatesExecuted"] == 2 and result["pointCalls"] == 0
            and result["materialCallsAttempted"] == result["materialCallsAccepted"] == 1760):
        failures.append("Existing bounded native output gate did not pass its declared scope")
    files = sorted((OLD / "observations/vtk").glob("particles_*.vtk"))
    if len(files) != 3:
        raise RuntimeError("Original retained baseline must have exactly3 actual states")
    files += [OLD / "observations/particles.csv", OLD / "observations/history.csv"]
    comparison = []
    for old_path in files:
        relative = old_path.relative_to(OLD)
        new_path = new / relative
        equal = old_path.read_bytes() == new_path.read_bytes()
        comparison.append({"path": relative.as_posix(), "baseline": digest(old_path),
                           "current": digest(new_path), "byteIdentical": equal})
        if not equal:
            failures.append("Actual bytes differ: " + relative.as_posix())
    report = {"status": "FAIL" if failures else "PASS", "failures": failures,
        "reference": str(OLD), "newRun": str(new), "sourceCountVerified": len(rows),
        "sourceBeforeAfterCurrentMatched": not any("source" in message.lower() for message in failures),
        "physicalUpdates": result["physicalUpdatesExecuted"], "standalonePointCalls": result["pointCalls"],
        "materialCallsAttempted": result["materialCallsAttempted"], "materialCallsAccepted": result["materialCallsAccepted"],
        "savedStates": 3, "comparedFiles": comparison,
        "executedComparisonScript": {"path": str(Path(__file__).resolve()), **digest(Path(__file__))},
        "scope": "Five existing native output files compared byte for byte, frozen source records checked. No numerical/test/replay/audit/render execution, no interpolation or changed tolerance.",
        "landslideVerified": False, "scientificallyValidated": False}
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": report["status"], "comparedFiles": len(comparison), "sources": len(rows), "result": str(target)}))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
