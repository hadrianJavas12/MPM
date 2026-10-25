"""Summarize saved kinematic samples; never run a kernel or a time step."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics


def record(path):
    payload = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest()}


def load_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
    if not rows or any(None in row for row in rows):
        raise ValueError("Empty or inconsistent CSV columns")
    return rows


def number(row, key):
    value = float(row[key])
    if not math.isfinite(value):
        raise ValueError("Nonfinite saved diagnostic value")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Preserve previous analysis")
    run = args.run_dir.resolve()
    paths = [run / name for name in ("result.json", "actual-initial-mp-footprints.csv",
                                     "hypothetical-arc-profiles.csv")]
    before = [record(path) for path in paths]
    native = json.loads(paths[0].read_text(encoding="utf-8-sig"))
    if not (native["status"] == "READ_ONLY_KINEMATIC_DIAGNOSTIC_COMPLETE"
            and native["mpmCallsAttempted"] == native["constitutiveCallsAttempted"] == 0):
        raise ValueError("Native diagnostic is not complete/read-only")
    actual, profiles = map(load_rows, paths[1:])
    summaries = []
    for mesh in native["meshSummaries"]:
        h = mesh["meshSizeM"]
        rows = [r for r in actual if number(r, "mesh_m") == h]
        if len(rows) != mesh["actualInitialParticleCount"]:
            raise ValueError("Actual initial MP count differs")
        weight = [r for r in rows if number(r, "base_w") > 0]
        gradient = [r for r in rows if number(r, "base_abs_gradient_norm") > 0]
        cap = [r for r in rows if math.hypot(number(r, "point_ux"), number(r, "point_uy")) > 0]
        min_clearance = min(number(r, "y_m") for r in profiles
                            if r["kind"] == "HYPOTHETICAL_ARC_NORMAL_PROBE"
                            and number(r, "mesh_m") == h and number(r, "normal_offset_m") == 0)
        minimum = [r for r in profiles if r["kind"] == "HYPOTHETICAL_ARC_NORMAL_PROBE"
                   and number(r, "mesh_m") == h and number(r, "normal_offset_m") == 0
                   and number(r, "y_m") == min_clearance]
        summaries.append({
            "meshSizeM": h, "actualMPs": len(rows),
            "actualMPsWithPositiveBaseWeight": len(weight),
            "positiveBaseWeightCountFraction": len(weight) / len(rows),
            "highestActualCenterWithPositiveBaseWeightM": max(number(r, "y_m") for r in weight),
            "actualMPsWithPositiveBaseAbsGradient": len(gradient),
            "maximumActualPartitionError": max(abs(number(r, "sum_w") - 1) for r in rows),
            "maximumActualPartitionGradientNormPerM": max(math.hypot(number(r, "sum_grad_x"), number(r, "sum_grad_y")) for r in rows),
            "maximumRawMinusMaskedFieldNormMPerS": max(number(r, "raw_minus_masked_norm") for r in rows),
            "prescribedCapActualSamples": len(cap),
            "prescribedCapSampleErrorRmsMPerS": math.sqrt(statistics.fmean(number(r, "point_error_norm") ** 2 for r in cap)),
            "minimumArcHypotheticalProbes": [{key: row[key] for key in (
                "x_m", "y_m", "domain_half_m", "domain_edge_margin_m", "sum_w", "base_w",
                "base_signed_grad_y", "base_abs_gradient_norm", "status")} for row in minimum],
        })
    if before != [record(path) for path in paths]:
        raise ValueError("Saved native diagnostic changed during summary")
    report = {"schema": "cl-mpm.basal.saved-summary.v1", "executedSource": record(Path(__file__)),
              "inputsBeforeAfterMatch": True, "inputs": before, "meshes": summaries,
              "actualRows": len(actual), "hypotheticalRows": len(profiles),
              "scope": "Saved CSV aggregation only; prescribed nodal fields are not simulated motion, best approximation or proof of locking. Near-floor hypothetical probes cross the particle-domain boundary. A zero mask difference does not disprove smear; the prescribed cap field already vanishes at the base.",
              "landslideVerified": False, "scientificallyValidated": False}
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
