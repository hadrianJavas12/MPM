#!/usr/bin/env python3
"""Compare native pre/post refactor VTK states and recorded curves.

No solver is run and no frame/time is interpolated. Identity uses unique native
IDs only when unique in both files, otherwise the reference coordinates x-u.
The latter are quantised at an explicit spatial tolerance and checked unique;
particles are never paired by current position or by nearest damaged shape.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

_spec = importlib.util.spec_from_file_location(
    "native_particle_vtk", Path(__file__).with_name("compare-reference-video.py"))
_reader = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_reader)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reference_points(points, fields):
    result = points.copy()
    for axis, key in enumerate(("disp_x", "disp_y", "disp_z")):
        if key in fields:
            result[:, axis] -= fields[key]
    return result


def identity(points_a, fields_a, points_b, fields_b, quantum):
    native_a, native_b = fields_a.get("unique-id"), fields_b.get("unique-id")
    if (native_a is not None and native_b is not None
            and len(np.unique(native_a)) == len(native_a)
            and len(np.unique(native_b)) == len(native_b)
            and np.array_equal(np.sort(native_a), np.sort(native_b))):
        ia, ib = np.argsort(native_a), np.argsort(native_b)
        ra = np.rint(reference_points(points_a, fields_a)[ia] / quantum)
        rb = np.rint(reference_points(points_b, fields_b)[ib] / quantum)
        if np.array_equal(ra, rb):
            return ia, ib, "native-unique-id-verified-against-reference-coordinates"
    keys = []
    for points, fields in ((points_a, fields_a), (points_b, fields_b)):
        coords = reference_points(points, fields)
        quantised = np.rint(coords / quantum).astype(np.int64)
        if len(np.unique(quantised, axis=0)) != len(coords):
            raise ValueError("Reference-coordinate identities are not unique; cannot compare safely")
        order = np.lexsort(tuple(quantised[:, i] for i in (2, 1, 0)))
        keys.append((quantised[order], order))
    if not np.array_equal(keys[0][0], keys[1][0]):
        raise ValueError("Reference-coordinate identities differ; cannot pair particles safely")
    return keys[0][1], keys[1][1], "reference-coordinates-x-minus-displacement"


def metric(a, b, atol, rtol):
    difference = np.abs(a - b)
    tolerance = atol + rtol * np.abs(a)
    baseline_scale = float(np.max(np.abs(a), initial=0))
    max_difference = float(difference.max(initial=0))
    global_tolerance = atol + rtol * baseline_scale
    return {"max_abs_difference": float(difference.max(initial=0)),
            "rms_difference": float(np.sqrt(np.mean(difference ** 2))),
            "max_scaled_difference": float(np.max(difference / np.maximum(tolerance, np.finfo(float).tiny), initial=0)),
            "mismatched_values": int(np.count_nonzero(difference > tolerance)),
            "pass": bool(np.all(difference <= tolerance)),
            "global_linf_diagnostic": {
                "basis": "max absolute difference / max absolute baseline value for this entire saved field; does not replace pointwise pass",
                "baseline_linf": baseline_scale,
                "relative_linf_difference": (max_difference / baseline_scale
                                             if baseline_scale else (0.0 if not max_difference else None)),
                "tolerance": global_tolerance,
                "pass": max_difference <= global_tolerance}}


def recorded_states(run):
    """Saved physical clocks are authoritative; preparatory settle rows excluded."""
    table = "timesteps.csv" if (run / "timesteps.csv").exists() else "stress-strain.csv"
    with (run / table).open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        columns, rows = reader.fieldnames, list(reader)
    states = []
    for row in rows:
        if row.get("phase") == "settle":
            continue
        if table == "timesteps.csv":
            path = run / "vtk" / f"sim_{int(row['step']):05d}.vtk"
            time = float(row["time"])
        else:
            path = run / f"particles_{int(row['frame']):04d}.vtk"
            time = float(row["time_s"])
        if not path.is_file():
            raise ValueError(f"Recorded state has no VTK: {path}")
        states.append({"time": time, "path": path, "row": row})
    if not states:
        raise ValueError(f"No physical states in {run}")
    return table, columns, states


def state_summary(points, fields):
    mass = fields["mass"]
    ref = reference_points(points, fields)
    result = {"particles": len(points), "fields": sorted(fields),
              "mass": float(mass.sum()), "bounds_min": points.min(axis=0).tolist(),
              "bounds_max": points.max(axis=0).tolist(),
              "max_displacement": float(np.linalg.norm(points - ref, axis=1).max()),
              "mass_centroid": np.average(points, axis=0, weights=mass).tolist()}
    if "damage" in fields:
        damage = fields["damage"]
        if np.any((damage < 0) | (damage > 1)):
            raise ValueError("Damage outside [0,1]")
        index = int(np.argmax(damage))
        result.update(max_damage=float(damage[index]),
                      max_damage_position=points[index].tolist(),
                      max_damage_reference_position=ref[index].tolist(),
                      mass_weighted_damage=float(np.dot(damage, mass) / mass.sum()))
        for label, mask in (("lower_reference_y_le_4m", ref[:, 1] <= 4),
                            ("upper_reference_y_ge_9m", ref[:, 1] >= 9)):
            result[label] = float(damage[mask].max()) if np.any(mask) else None
        for threshold in (0.05, 0.5, 0.9):
            mask = damage > threshold
            result[f"damage_gt_{threshold}"] = {
                "count": int(mask.sum()),
                "reference_y_min": float(ref[mask, 1].min()) if mask.any() else None,
                "reference_y_max": float(ref[mask, 1].max()) if mask.any() else None}
        # Actual domain edge above elastic foundation; no reference-video clock.
        above_base = points[:, 1] > 1.05
        result["right_domain_edge_above_y1_05m"] = float(
            (points[above_base, 0] + fields["size_x"][above_base] / 2).max()) if above_base.any() else None
        initial_top = ref[:, 1] >= 14
        result["initial_top_particle_mean_y"] = float(points[initial_top, 1].mean()) if initial_top.any() else None
    return result


def curve_compare(columns_a, states_a, columns_b, states_b, atol, rtol):
    result = {"same_columns": columns_a == columns_b, "columns": {}}
    for key in sorted(set(columns_a) & set(columns_b)):
        aa, bb = [s["row"][key] for s in states_a], [s["row"][key] for s in states_b]
        try:
            a, b = np.asarray(aa, dtype=float), np.asarray(bb, dtype=float)
        except ValueError:
            result["columns"][key] = {"pass": aa == bb, "kind": "categorical"}
            continue
        if not (np.isfinite(a).all() and np.isfinite(b).all()):
            raise ValueError(f"Non-finite CSV column {key}")
        result["columns"][key] = metric(a, b, atol, rtol)
    result["pass"] = result["same_columns"] and all(v["pass"] for v in result["columns"].values())
    result["global_linf_diagnostic_pass"] = result["same_columns"] and all(
        v.get("global_linf_diagnostic", v)["pass"] for v in result["columns"].values())
    return result


def compare(args):
    table_a, columns_a, aa = recorded_states(args.baseline)
    table_b, columns_b, bb = recorded_states(args.candidate)
    metadata = {}
    for label, run, states in (("baseline", args.baseline, aa), ("candidate", args.candidate, bb)):
        path = run / ("reference-metadata.json" if table_a == "timesteps.csv" else "manifest.json")
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        if value.get("complete") is not True:
            raise ValueError(f"{label} is not a completed native run")
        if table_a == "timesteps.csv":
            if value.get("termination") != "simulation-time":
                raise ValueError(f"{label} did not reach the simulation-time termination")
            if abs(value["requestedSimulationTime"] - states[-1]["time"]) > args.time_tolerance:
                raise ValueError(f"{label} final CSV clock does not reach the requested duration")
        metadata[label] = value
    result = {"baseline": str(args.baseline.resolve()), "candidate": str(args.candidate.resolve()),
              "comparison": "native saved states and recorded CSV only; no interpolation or renderer comparison",
              "scientific_validation": False,
              "run_metadata": metadata,
              "tolerances": {"absolute": args.atol, "relative_to_baseline": args.rtol,
                             "reference_coordinate_quantum_m": args.identity_quantum,
                             "time_tolerance_s": args.time_tolerance},
              "baseline_states": len(aa), "candidate_states": len(bb), "frames": []}
    if len(aa) != len(bb):
        result.update(passed=False, failure="Different saved physical frame counts")
        return result
    if table_a != table_b:
        result.update(passed=False, failure="Different recorded CSV types")
        return result
    if any(abs(a["time"] - b["time"]) > args.time_tolerance for a, b in zip(aa, bb)):
        result.update(passed=False, failure="Different saved physical clocks; no interpolation permitted")
        return result
    for a, b in zip(aa, bb):
        pa, fa = _reader.read_particle_vtk(a["path"])
        pb, fb = _reader.read_particle_vtk(b["path"])
        if len(pa) != len(pb):
            raise ValueError(f"Particle count changed at t={a['time']}")
        ia, ib, basis = identity(pa, fa, pb, fb, args.identity_quantum)
        fields = {key: metric(fa[key][ia], fb[key][ib], args.atol, args.rtol)
                  for key in sorted(set(fa) & set(fb))}
        position = metric(pa[ia], pb[ib], args.atol, args.rtol)
        same_fields = set(fa) == set(fb)
        result["frames"].append({"time": a["time"], "baseline_file": a["path"].name,
                                 "candidate_file": b["path"].name,
                                 "baseline_sha256": sha256(a["path"]),
                                 "candidate_sha256": sha256(b["path"]),
                                 "identity_basis": basis, "same_fields": same_fields,
                                 "position": position, "fields": fields,
                                 "baseline_summary": state_summary(pa, fa),
                                 "candidate_summary": state_summary(pb, fb),
                                 "passed": same_fields and position["pass"] and all(v["pass"] for v in fields.values())})
    result["curve"] = curve_compare(columns_a, aa, columns_b, bb, args.atol, args.rtol)
    result["passed"] = all(f["passed"] for f in result["frames"]) and result["curve"]["pass"]
    result["global_linf_diagnostic_passed"] = result["curve"]["global_linf_diagnostic_pass"] and all(
        f["same_fields"] and f["position"]["global_linf_diagnostic"]["pass"]
        and all(v["global_linf_diagnostic"]["pass"] for v in f["fields"].values())
        for f in result["frames"])
    result["global_linf_is_diagnostic_only"] = True
    result["max_position_difference_m"] = max(f["position"]["max_abs_difference"] for f in result["frames"])
    result["field_maxima"] = {key: max(f["fields"][key]["max_abs_difference"] for f in result["frames"])
                              for key in result["frames"][0]["fields"]}
    for name in ("baseline", "candidate"):
        masses = np.array([f[name + "_summary"]["mass"] for f in result["frames"]])
        mass_drift = float(np.max(np.abs(masses / masses[0] - 1)))
        result[name + "_max_relative_mass_drift"] = mass_drift
        if mass_drift > 1e-12:
            result["passed"] = False
    for name in ("baseline", "candidate"):
        series = [(f["time"], f[name + "_summary"]) for f in result["frames"]]
        if "max_damage" not in series[0][1]:
            continue
        def first(key):
            return next(({"time": t, **s} for t, s in series if s.get(key) is not None and s[key] > 0.05), None)
        result[name + "_damage_progression"] = {
            "definition": "threshold damage>0.05; lower/upper refer to original material y, not falling current y",
            "first_lower": first("lower_reference_y_le_4m"),
            "first_upper": first("upper_reference_y_ge_9m"),
            "final": {"time": series[-1][0], **series[-1][1]}}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--atol", type=float, default=1e-8)
    parser.add_argument("--rtol", type=float, default=1e-7)
    parser.add_argument("--identity-quantum", type=float, default=1e-7)
    parser.add_argument("--time-tolerance", type=float, default=1e-10)
    args = parser.parse_args()
    if min(args.atol, args.rtol, args.time_tolerance) < 0 or args.identity_quantum <= 0:
        parser.error("Tolerances must be nonnegative and identity quantum positive")
    try:
        result = compare(args)
    except (ValueError, OSError, KeyError) as error:
        result = {"passed": False, "error": str(error)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("passed", "failure", "error", "baseline_states", "candidate_states", "max_position_difference_m") if key in result}, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
