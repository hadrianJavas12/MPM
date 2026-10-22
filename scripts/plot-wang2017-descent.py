"""Audit and plot native Wang2017 output; never create or alter a run manifest."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return [{key: float(value.lower().replace("d", "e"))
                 for key, value in row.items()} for row in csv.DictReader(stream)]


def inspect(run):
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8-sig"))
    rows = read_rows(run / "force-displacement.csv")
    if not rows or not all(np.isfinite(list(row.values())).all() for row in rows):
        raise ValueError("Missing/nonfinite native loading records")
    config = manifest["config"]
    module_path = Path(__file__).with_name("plot_m5_cliff_comparison.py")
    spec = importlib.util.spec_from_file_location("native_cliff_reader", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    mass0, time0 = rows[0]["mass_kg_per_m"], -1.0
    snapshots, records = [], []
    for row in rows:
        time = row["time_s"]
        if time <= time0:
            raise ValueError("Saved loading times must increase strictly")
        if not np.isclose(row["commanded_settlement_m"], config["velocity"] * time,
                          atol=1e-11, rtol=1e-10):
            raise ValueError("Commanded trajectory differs from configured physical velocity")
        reaction, soil = row["reaction_upward_N_per_m"], row["soil_force_y_N_per_m"]
        if not np.isclose(reaction, -soil, atol=1e-7, rtol=1e-10):
            raise ValueError("Signed action/reaction mismatch")
        if not np.isclose(soil, row["nodal_force_y_N_per_m"], atol=1e-6, rtol=1e-9):
            raise ValueError("Particle penalty force differs from mapped nodal force")
        path = run / "vtk" / f"particles_{int(row['frame']):04d}.vtk"
        points, fields = module.read_cliff_vtk(path)
        if len(points) != int(row["particle_count"]):
            raise ValueError("CSV/VTK particle count mismatch")
        mass = float(fields["mass"].sum())
        if not np.isclose(mass, mass0, atol=1e-8, rtol=1e-11):
            raise ValueError("Native VTK mass conservation failure")
        snapshots.append((points, fields))
        records.append({"path": str(path.relative_to(run)),
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        time0 = time
    if manifest.get("complete"):
        if not manifest.get("gravityConverged") or not manifest.get("reportingResetPreservedState"):
            raise ValueError("Complete flag lacks gravity/reset proof")
        if not np.isclose(rows[-1]["commanded_settlement_m"], config["targetDisplacement"],
                          atol=1e-11, rtol=1e-10):
            raise ValueError("Complete flag precedes the requested displacement target")
        if not np.isclose(rows[-1]["time_s"], config["duration"], atol=1e-9, rtol=1e-10):
            raise ValueError("Complete flag precedes the requested physical duration")
    audit = {"passedConsistencyChecks": True, "nativeComplete": manifest.get("complete", False),
             "scope": "Saved output consistency, not FEM equivalence or experimental validation",
             "scientificValidation": False, "frames": len(rows), "massKgPerM": mass0,
             "physicalTimeS": rows[-1]["time_s"],
             "commandedSettlementM": rows[-1]["commanded_settlement_m"],
             "measuredSettlementM": rows[-1]["measured_settlement_m"],
             "maxAbsolutePenaltyGapM": max(abs(row["penalty_gap_m"]) for row in rows),
             "reactionUpwardNPerM": rows[-1]["reaction_upward_N_per_m"],
             "sources": records}
    return manifest, rows, snapshots, audit


def draw(manifest, rows, snapshot, index, destination):
    points, fields = snapshot
    reference = np.asarray([row["commanded_settlement_m"] for row in rows])
    actual = np.asarray([row["measured_settlement_m"] for row in rows])
    forces = np.asarray([row["reaction_upward_N_per_m"] / 1000 for row in rows])
    config, row = manifest["config"], rows[index]
    fig, (spatial, curve) = plt.subplots(1, 2, figsize=(12, 5.4), constrained_layout=True)
    quantity = "mc-kappa" if "mc-kappa" in fields else "stress_yy"
    if quantity not in fields:
        quantity = "mass"
    values = fields[quantity]
    dots = spatial.scatter(points[:, 0], points[:, 1], c=values, s=8, cmap="viridis")
    fig.colorbar(dots, ax=spatial, label=quantity)
    spatial.set(xlabel="x (m)", ylabel="y (m)", aspect="equal",
                title=f"Actual MPM particles, t={row['time_s']:.4g} s")
    spatial.plot([config["patchStart"], config["patchStart"] + config["patchLength"]],
                 [config["baseHeight"] + config["height"] - row["commanded_settlement_m"]] * 2,
                 color="red", linewidth=3, label="Commanded strip")
    spatial.legend(loc="lower left", fontsize=8)
    curve.plot(reference[:index+1] * 1000, forces[:index+1], label="Commanded descent", color="#377eb8")
    curve.plot(actual[:index+1] * 1000, forces[:index+1], "--", label="Measured soil descent", color="#ff7f00")
    curve.scatter([reference[index] * 1000], [forces[index]], color="#377eb8", s=28)
    curve.set(xlabel="Downward settlement (mm)", ylabel="Upward reaction (kN/m)",
              title="Native reaction versus settlement")
    curve.grid(alpha=.25)
    curve.legend(fontsize=8)
    extent = max(float(np.max(reference)), float(np.max(actual)), 1e-12) * 1000
    curve.set_xlim(min(0.0, float(np.min(actual)) * 1000), extent * 1.05)
    lo, hi = min(0.0, float(np.min(forces))), max(0.0, float(np.max(forces)))
    pad = max(.05 * (hi - lo), 1e-7)
    curve.set_ylim(lo - pad, hi + pad)
    kind = "SHORT PILOT" if config["targetDisplacement"] < .09 else "FULL TARGET"
    completion = "native complete" if manifest.get("complete") else "INCOMPLETE"
    fig.suptitle(f"Wang2017 Soil1 | {kind}, {completion} | v={config['velocity']:.1e} m/s\n"
                 f"Relief {config['height']:g} m is assumed; explicit MPM with finite penalty compliance; no displacement amplification",
                 fontsize=11)
    fig.savefig(destination, dpi=140)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--video", action="store_true")
    args = parser.parse_args()
    run = args.run_dir.resolve()
    manifest, rows, snapshots, audit = inspect(run)
    draw(manifest, rows, snapshots[-1], len(rows)-1, run / "descent-overview.png")
    if args.video:
        executable = shutil.which("ffmpeg")
        if not executable:
            raise RuntimeError("ffmpeg is required for --video")
        frames = run / "rendered-frames"
        frames.mkdir(exist_ok=True)
        for index, snapshot in enumerate(snapshots):
            draw(manifest, rows, snapshot, index, frames / f"frame_{index:05d}.png")
        subprocess.run([executable, "-v", "error", "-y", "-framerate", "4", "-i",
                        str(frames / "frame_%05d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", str(run / "slope-descent.mp4")], check=True)
    (run / "output-audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in audit.items() if key != "sources"}, indent=2))
    return 0 if manifest.get("complete") else 2


if __name__ == "__main__":
    raise SystemExit(main())
