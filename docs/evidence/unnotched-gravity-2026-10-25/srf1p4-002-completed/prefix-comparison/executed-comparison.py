"""Strict saved-prefix comparison only; never import a solver or change tolerance."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import io
import json
import math
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
BEFORE = ROOT / "output/unnotched-gravity-2026-10-24/srf1p4-001"
AFTER = ROOT / "output/unnotched-gravity-2026-10-25/srf1p4-002"
OUTPUT = AFTER / "prefix-comparison-001"
LAST_FRAME = 9


def record(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": h.hexdigest()}


def write_json(name, value):
    (OUTPUT / name).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def prefix(path):
    with path.open("rb") as stream:
        header = stream.readline()
        if not header:
            raise ValueError(f"Empty CSV: {path}")
        lines = []
        for line in stream:
            number = int(line.split(b",", 1)[0])
            if number > LAST_FRAME:
                break
            lines.append(line)
    payload = header + b"".join(lines)
    rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8-sig"), newline="")))
    if any(None in row or any(v is None for v in row.values()) for row in rows):
        raise ValueError(f"Incomplete CSV: {path}")
    return header, payload, rows


def numeric(text):
    value = float(text.replace("D", "e").replace("d", "e"))
    if not math.isfinite(value):
        raise ValueError("Nonfinite CSV field")
    return value


def main():
    if OUTPUT.exists():
        raise ValueError("Choose a fresh prefix-comparison output")
    OUTPUT.mkdir()
    # Source was already saved before process invocation; retain its exact bytes
    # before reading or comparing the native data.
    executed = OUTPUT / "executed-comparison.py"
    shutil.copyfile(Path(__file__), executed)
    if executed.read_bytes() != Path(__file__).read_bytes():
        raise ValueError("Executed analysis source copy mismatch")
    inputs = []
    vtk = []
    for frame in range(LAST_FRAME + 1):
        before = BEFORE / "vtk" / f"particles_{frame:04d}.vtk"
        after = AFTER / "vtk" / f"particles_{frame:04d}.vtk"
        a, b = record(before), record(after)
        inputs.extend([a, b])
        vtk.append({"frame": frame, "savedTimeNominalS": frame / 10,
                    "before": a, "after": b, "byteIdentical": before.read_bytes() == after.read_bytes()})

    csv_results = []
    difference_records = []
    for name, expected_per_frame in [("history.csv", 1), ("particles.csv", 880)]:
        left, right = BEFORE / name, AFTER / name
        inputs.extend([record(left), record(right)])
        ah, ab, ar = prefix(left)
        bh, bb, br = prefix(right)
        if len(ar) != (LAST_FRAME + 1) * expected_per_frame or len(br) != len(ar):
            raise ValueError(f"Unexpected saved-prefix row counts for {name}")
        for rows in (ar, br):
            for frame in range(LAST_FRAME + 1):
                selected = [row for row in rows if int(row["frame"]) == frame]
                if len(selected) != expected_per_frame:
                    raise ValueError(f"Missing/extra saved frame rows for {name}/{frame}")
                if "particle_id" in rows[0] and [int(row["particle_id"]) for row in selected] != list(range(880)):
                    raise ValueError("Particle CSV captured ID/order mismatch")
        (OUTPUT / f"before-{name}").write_bytes(ab)
        (OUTPUT / f"after-{name}").write_bytes(bb)
        max_deltas = {key: 0.0 for key in ar[0]}
        changed_fields = {key: 0 for key in ar[0]}
        differing_rows = 0
        header_equal = ah == bh
        if set(ar[0]) != set(br[0]):
            raise ValueError("CSV schema mismatch")
        for index, (a, b) in enumerate(zip(ar, br)):
            differences = []
            for key in a:
                av, bv = numeric(a[key]), numeric(b[key])
                max_deltas[key] = max(max_deltas[key], abs(av - bv))
                if a[key] != b[key]:
                    changed_fields[key] += 1
                    differences.append({"field": key, "beforeRaw": a[key], "afterRaw": b[key],
                                        "absoluteNumericDelta": abs(av - bv)})
            if differences:
                differing_rows += 1
                difference_records.append({"csv": name, "rowZeroBased": index,
                    "frame": a["frame"], "particle_id": a.get("particle_id"), "differences": differences})
        csv_results.append({"name": name, "prefixRows": len(ar), "frames": LAST_FRAME + 1,
                            "headerBytesIdentical": header_equal, "prefixBytesIdentical": ab == bb,
                            "allFieldStringsIdentical": differing_rows == 0,
                            "differingRows": differing_rows, "changedFieldStringCounts": changed_fields,
                            "maxAbsoluteNumericDeltas": max_deltas,
                            "beforePrefix": record(OUTPUT / f"before-{name}"),
                            "afterPrefix": record(OUTPUT / f"after-{name}")})
    passed = all(row["byteIdentical"] for row in vtk) and all(row["prefixBytesIdentical"] for row in csv_results)
    write_json("raw-field-differences.json", {"count": len(difference_records), "rows": difference_records})
    write_json("result.json", {"schema": "cl-mpm.unnotched-gravity.strict-prefix-comparison.v1",
        "createdUtc": datetime.now(timezone.utc).isoformat(), "status": "PASS" if passed else "FAIL",
        "beforeRun": str(BEFORE.relative_to(ROOT)), "afterRun": str(AFTER.relative_to(ROOT)),
        "comparisonScope": "All ten actual saved states from0 through0.9s; exact VTK bytes and complete raw CSV row/string bytes for those frames",
        "tolerance": "EXACT_BYTES_AND_STRINGS; no threshold, interpolation or tolerance relaxation",
        "newProjectorOrSolverCalls": 0, "executedScript": record(executed), "inputFiles": inputs,
        "vtk": vtk, "csv": csv_results, "differingRawRows": len(difference_records),
        "notClaims": ["No comparison beyond the failed run's final saved0.9s", "No whole-state MPM restart or paper/landslide validation", "Finiteness/physical integrity/full-motion review is separate"]})
    write_json("SHA256SUMS.json", {"files": [record(p) for p in sorted(OUTPUT.iterdir()) if p.is_file() and p.name != "SHA256SUMS.json"]})
    print(json.dumps({"output": str(OUTPUT), "status": "PASS" if passed else "FAIL",
                      "vtkStatesByteIdentical": sum(r["byteIdentical"] for r in vtk),
                      "csvRows": [r["prefixRows"] for r in csv_results], "differingRawRows": len(difference_records)}))
    return 0 if passed else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        if OUTPUT.exists():
            write_json("analysis-failure.json", {"status": "FAILED_ANALYSIS", "error": str(error), "newSolverCalls": 0})
        raise
