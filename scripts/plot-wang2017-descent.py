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
             "maxAbsoluteMeanPenaltyGapM": max(abs(row["penalty_gap_m"]) for row in rows),
             "maxParticlePenaltyGapM": max(row["max_gap_m"] for row in rows),
             "initialReactionTransientsObserved": any(row["reaction_upward_N_per_m"] < -1e-7 for row in rows),
             "quasiStaticReferenceAgreement": "NOT_VERIFIED",
             "reactionUpwardNPerM": rows[-1]["reaction_upward_N_per_m"],
             "loadingVelocityMPerS": config["velocity"],
             "loadingRateMultiplier": config["velocity"] / 1e-4,
             "maxYieldResidualPa": max(row["max_yield_residual_pa"] for row in rows),
             "finalMeanTrackingErrorFraction": abs(rows[-1]["penalty_gap_m"]) / config["targetDisplacement"],
             "sources": records}
    energy_path = run / "energy-history.csv"
    if energy_path.exists():
        energies = read_rows(energy_path)
        if len(energies) != len(rows):
            raise ValueError("Energy/loading frame counts differ")
        for row, energy in zip(rows, energies):
            if not np.isfinite(list(energy.values())).all():
                raise ValueError("Nonfinite energy observation")
            if not np.isclose(row["time_s"], energy["time_s"], atol=1e-10, rtol=1e-10):
                raise ValueError("Energy/loading times differ")
            if not np.isclose(row["kinetic_energy_J_per_m"], energy["kinetic_J_per_m"], atol=1e-8, rtol=1e-10):
                raise ValueError("Energy/loading kinetic diagnostics differ")
        audit["kineticOverElasticProxyMax"] = max(e["kinetic_over_elastic_proxy"] for e in energies)
        audit["energyCaveat"] = "Current-volume Hencky/native-plastic proxies, not closed energy balance. Gravity prestress can mask loading inertia; rate comparison is still required."
    return manifest, rows, snapshots, audit


def drawing_limits(snapshots):
    """Keep coordinates and physical colour meaning fixed across native frames."""
    quantity = next(name for name in ("wang-paper-kps", "mc-kappa", "stress_yy", "mass")
                    if all(name in fields for _, fields in snapshots))
    xy = np.concatenate([points[:, :2] for points, _ in snapshots])
    low, high = xy.min(axis=0), xy.max(axis=0)
    padding = np.maximum((high - low) * .03, 1e-9)
    vmin = min(float(fields[quantity].min()) for _, fields in snapshots)
    vmax = max(float(fields[quantity].max()) for _, fields in snapshots)
    if not np.isfinite(xy).all() or not np.isfinite([vmin, vmax]).all():
        raise ValueError("Nonfinite plotted native coordinates or scalar range")
    return {"quantity": quantity, "xlim": [float(low[0]-padding[0]), float(high[0]+padding[0])],
            "ylim": [float(low[1]-padding[1]), float(high[1]+padding[1])],
            "vmin": vmin, "vmax": vmax if vmax > vmin else vmin + max(abs(vmin)*.01, 1e-12)}


def draw(manifest, rows, snapshot, index, destination, limits=None):
    points, fields = snapshot
    reference = np.asarray([row["commanded_settlement_m"] for row in rows])
    actual = np.asarray([row["measured_settlement_m"] for row in rows])
    forces = np.asarray([row["reaction_upward_N_per_m"] / 1000 for row in rows])
    config, row = manifest["config"], rows[index]
    fig, (spatial, curve) = plt.subplots(1, 2, figsize=(12, 5.4), constrained_layout=True)
    quantity = next((name for name in ("wang-paper-kps", "mc-kappa", "stress_yy")
                     if name in fields), "mass")
    if quantity not in fields:
        quantity = "mass"
    values = fields[quantity]
    colour_options = {}
    if limits is not None:
        quantity = limits["quantity"]
        values = fields[quantity]
        colour_options = {key: limits[key] for key in ("vmin", "vmax")}
        spatial.set_xlim(limits["xlim"])
        spatial.set_ylim(limits["ylim"])
    dots = spatial.scatter(points[:, 0], points[:, 1], c=values, s=8, cmap="viridis", **colour_options)
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
    if not np.isclose(config["velocity"], 1e-4, rtol=1e-12, atol=0):
        kind = f"ACCELERATED TRIAL ({config['velocity']/1e-4:g}x reference)"
    completion = "native complete" if manifest.get("complete") else "INCOMPLETE"
    model = "Soil2 (declared corotated history)" if config.get("materialModel") == "wang2017-soil2" else "Soil1"
    fig.suptitle(f"Wang2017 {model} | {kind}, {completion} | v={config['velocity']:.1e} m/s\n"
                 f"Relief {config['height']:g} m is assumed; explicit MPM with finite penalty compliance; no displacement amplification",
                 fontsize=11)
    fig.savefig(destination, dpi=140)
    plt.close(fig)


def draw_energy(run):
    path = run / "energy-history.csv"
    if not path.exists():
        return
    rows = read_rows(path)
    times = [r["time_s"] for r in rows]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), constrained_layout=True)
    axes[0].plot(times, [r["kinetic_J_per_m"] for r in rows])
    axes[0].set(ylabel="Kinetic energy (J/m)", title="Native kinetic energy")
    for key, label in (("delta_elastic_proxy_J_per_m", "Elastic proxy change"),
                       ("delta_native_plastic_proxy_J_per_m", "Native plastic proxy change"),
                       ("actuator_signed_command_work_J_per_m", "Signed actuator command work")):
        axes[1].plot(times, [r[key] for r in rows], label=label)
    axes[1].set(ylabel="J/m", title="Signed observations; no closed budget")
    axes[1].legend(fontsize=7)
    axes[2].plot(times, [r["kinetic_over_elastic_proxy"] for r in rows])
    axes[2].set(ylabel="K / |elastic proxy|", title="Prestress can mask loading inertia")
    for ax in axes:
        ax.set_xlabel("Actual loading time (s)")
        ax.grid(alpha=.25)
    fig.savefig(run / "energy-diagnostics.png", dpi=140)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--video", action="store_true")
    args = parser.parse_args()
    run = args.run_dir.resolve()
    manifest, rows, snapshots, audit = inspect(run)
    limits = drawing_limits(snapshots)
    audit["visualization"] = {**limits, "displacementScale": 1,
                              "interpolatedStates": False, "videoFps": 4}
    draw(manifest, rows, snapshots[-1], len(rows)-1, run / "descent-overview.png", limits)
    draw_energy(run)
    if args.video:
        executable = shutil.which("ffmpeg")
        if not executable:
            raise RuntimeError("ffmpeg is required for --video")
        frames = run / "rendered-frames"
        frames.mkdir(exist_ok=True)
        for index, snapshot in enumerate(snapshots):
            draw(manifest, rows, snapshot, index, frames / f"frame_{index:05d}.png", limits)
        subprocess.run([executable, "-v", "error", "-y", "-framerate", "4", "-i",
                        str(frames / "frame_%05d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-frames:v", str(len(snapshots)),
                        "-movflags", "+faststart", str(run / "slope-descent.mp4")], check=True)
    (run / "output-audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in audit.items() if key != "sources"}, indent=2))
    return 0 if manifest.get("complete") else 2


if __name__ == "__main__":
    raise SystemExit(main())
