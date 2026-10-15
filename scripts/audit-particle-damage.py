#!/usr/bin/env python3
"""Audit real particle VTK damage, locations and mass without running a solver."""
import argparse
import csv
import importlib.util
import json
from pathlib import Path

import numpy as np

spec = importlib.util.spec_from_file_location(
    "reference_vtk", Path(__file__).with_name("compare-reference-video.py"))
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    vtk_dir = args.run_dir / "vtk"
    if not vtk_dir.is_dir():
        vtk_dir = args.run_dir
    paths = sorted(vtk_dir.glob("*.vtk"))
    paths = [p for p in paths if not p.stem.startswith("mesh")]
    initial = [p for p in paths if p.stem in ("initial", "sim_00000")]
    paths = initial + [p for p in paths if p not in initial]
    if not paths:
        parser.error("No particle VTK files found")
    times = {}
    csv_path = args.run_dir / "timesteps.csv"
    if csv_path.exists():
        with csv_path.open(newline="", encoding="utf-8-sig") as stream:
            for row in csv.DictReader(stream):
                key = row.get("step", row.get("steps"))
                if key and row.get("time"):
                    times[int(key)] = {"time": float(row["time"]),
                                      "phase": row.get("phase", row.get("step-type"))}
    records = []
    for path in paths:
        points, fields = reader.read_particle_vtk(path)
        damage, mass = fields["damage"], fields["mass"]
        if (damage < 0).any() or (damage > 1).any() or (mass <= 0).any():
            raise ValueError(f"Invalid damage/mass bounds: {path}")
        maximum = int(np.argmax(damage))
        lower, upper = points[:, 1] <= 4, points[:, 1] >= 9
        number = int(path.stem.split("_")[-1]) if path.stem.startswith("sim_") else None
        counts = {}
        for threshold in (1e-6, .05, .5, .9):
            mask = damage > threshold
            counts[str(threshold)] = {
                "particles": int(mask.sum()),
                "bounds": {"min": points[mask].min(axis=0).tolist(),
                           "max": points[mask].max(axis=0).tolist()} if mask.any() else None}
        records.append({"file": str(path.resolve()), "clock": times.get(number),
                        "particles": len(points), "scalar_count": len(fields),
                        "mass": float(mass.sum()), "max_damage": float(damage[maximum]),
                        "max_damage_position": points[maximum].tolist() if damage[maximum] > 0 else None,
                        "mass_weighted_damage": float(np.dot(mass, damage) / mass.sum()),
                        "lower_max_damage": float(damage[lower].max()) if lower.any() else None,
                        "upper_max_damage": float(damage[upper].max()) if upper.any() else None,
                        "damage_thresholds": counts, "all_fields_finite": True})
    baseline = records[0]["mass"]
    for record in records:
        record["mass_change_fraction"] = (record["mass"] - baseline) / baseline
    result = {"basis": "Strict finite big-endian VTK parse; clock only from CSV; lower y<=4m, upper y>=9m",
              "validation": "field integrity and damage location only; no physical accuracy claim",
              "records": records}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    def brief(record):
        if record is None:
            return None
        return {key: record[key] for key in (
            "file", "clock", "particles", "mass", "max_damage", "max_damage_position",
            "lower_max_damage", "upper_max_damage", "mass_change_fraction")}
    print(json.dumps({"frames": len(records), "first_lower_damage_above_0.05": brief(next(
        (r for r in records if r["lower_max_damage"] is not None and r["lower_max_damage"] > .05), None)),
        "last": brief(records[-1])}, indent=2))


if __name__ == "__main__":
    main()
