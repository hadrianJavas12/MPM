"""Compare two already audited native runs at the same times/captured IDs.

No native calls, VTK reading, old-run re-audit or geometry/video rendering.
"""
from datetime import datetime, timezone
import csv
import hashlib
import json
from pathlib import Path
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


OUTPUT = Path(__file__).resolve().parent
BASE = OUTPUT.parent
RUNS = {"srf1": BASE / "srf1-001", "srf1p4": BASE / "srf1p4-002"}


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def record(path):
    payload = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        names = reader.fieldnames
        rows = [[float(row[name].lower().replace("d", "e")) for name in names] for row in reader]
    values = np.asarray(rows, dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Nonfinite paired input CSV")
    return {name: values[:, index] for index, name in enumerate(names)}


def write_json(path, value):
    if path.exists():
        raise RuntimeError(f"Preserve existing paired result: {path}")
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def weighted_mean(values, mass):
    return np.average(values, axis=0, weights=mass)


def main():
    manifests = {name: load(path / "manifest.json") for name, path in RUNS.items()}
    reviews = {name: load(path / "review-001/review.json") for name, path in RUNS.items()}
    if not all(m["complete"] and m["timeS"] == 6 and m["savedFrames"] == 61 for m in manifests.values()):
        raise ValueError("Pair requires two actual completed6s/61state runs")
    if not all(r["integrityStatus"] == "PASS" for r in reviews.values()):
        raise ValueError("Pair requires previously completed independent integrity audits")
    if reviews["srf1"]["contract"]["sha256"] != reviews["srf1p4"]["contract"]["sha256"]:
        raise ValueError("Predeclared detector changed between pair members")
    a, b = manifests["srf1"]["config"], manifests["srf1p4"]["config"]
    config_changes = [{"key": key, "srf1": a[key], "srf1p4": b[key]} for key in sorted(a) if a[key] != b[key]]
    if {r["key"] for r in config_changes} != {"strengthReductionFactor", "cohesionPa", "frictionRad"}:
        raise ValueError("Unexpected physical/numerical changes in paired configuration")
    source = {name: {r["path"]: r for r in load(path / "source/source-manifest.json")["files"]}
              for name, path in RUNS.items()}
    if set(source["srf1"]) != set(source["srf1p4"]):
        raise ValueError("Different frozen source member sets")
    changed_sources = [key for key in sorted(source["srf1"])
                       if source["srf1"][key]["sha256"] != source["srf1p4"][key]["sha256"]]
    if changed_sources != ["source/case.lisp"]:
        raise ValueError(f"Unexpected source difference: {changed_sources}")
    case_bytes = {name: (path / "source/case.lisp").read_bytes() for name, path in RUNS.items()}
    normalized = {name: re.sub(rb"\(srf\s+[^)]+\)", b"(srf <PREDECLARED_FACTOR>)", payload, count=1)
                  for name, payload in case_bytes.items()}
    if normalized["srf1"] != normalized["srf1p4"]:
        raise ValueError("Case differs beyond its predeclared literal SRF")
    history = {name: read_csv(path / "history.csv") for name, path in RUNS.items()}
    data = {name: read_csv(path / "particles.csv") for name, path in RUNS.items()}
    n, frames = manifests["srf1"]["particleCount"], 61
    for name, values in data.items():
        if not (len(values["particle_id"]) == n * frames
                and np.array_equal(values["frame"], np.repeat(np.arange(frames), n))
                and np.array_equal(values["particle_id"], np.tile(np.arange(n), frames))):
            raise ValueError(f"Unexpected captured ID/time order: {name}")
    for column in ("frame", "time_s", "particle_id", "initial_x_m", "initial_y_m", "mass_kg_per_m",
                   "reference_volume_m3_per_m", "free_upper_reference_subset"):
        if not np.array_equal(data["srf1"][column], data["srf1p4"][column]):
            raise ValueError(f"Pair differs in required time/ID/reference field: {column}")
    if not np.array_equal(history["srf1"]["time_s"], history["srf1p4"]["time_s"]):
        raise ValueError("Saved history times differ; do not interpolate")
    times = history["srf1"]["time_s"]
    initial = np.column_stack([data["srf1"]["initial_x_m"][:n], data["srf1"]["initial_y_m"][:n]])
    mass = data["srf1"]["mass_kg_per_m"][:n]
    cohort = data["srf1"]["free_upper_reference_subset"][:n] == 1
    physical = {}
    for name, values in data.items():
        positions = np.stack([values["x_m"], values["y_m"]], axis=1).reshape(frames, n, 2)
        velocity = np.stack([values["vx_m_per_s"], values["vy_m_per_s"]], axis=1).reshape(frames, n, 2)
        displacement = positions - initial[None, :, :]
        physical[name] = {"position": positions, "velocity": velocity, "displacement": displacement,
                          "kappa": values["mc_kappa"].reshape(frames, n), "J": values["J"].reshape(frames, n)}
    delta = {name: physical["srf1p4"][name] - physical["srf1"][name]
             for name in ("position", "velocity", "kappa", "J")}
    stress_columns = [f"sig_{axis}_pa" for axis in ("xx", "yy", "zz", "yz", "xz", "xy")]
    stress_delta = np.stack([data["srf1p4"][key] - data["srf1"][key] for key in stress_columns], axis=1).reshape(frames, n, 6)
    per_frame = []
    for frame, time in enumerate(times):
        row = {"frame": frame, "timeS": float(time),
               "maximumIdAlignedPositionDifferenceM": float(np.abs(delta["position"][frame]).max()),
               "massWeightedRmsPositionDifferenceM": float(np.sqrt(weighted_mean(np.square(delta["position"][frame]).sum(axis=1), mass))),
               "maximumIdAlignedVelocityDifferenceMPerS": float(np.abs(delta["velocity"][frame]).max()),
               "maximumIdAlignedKappaDifference": float(np.abs(delta["kappa"][frame]).max()),
               "maximumIdAlignedCauchyStressDifferencePa": float(np.abs(stress_delta[frame]).max())}
        row["trials"] = {}
        for name, state in physical.items():
            displacement = state["displacement"][frame]
            velocity = state["velocity"][frame]
            row["trials"][name] = {
                "cohortCentroidDisplacementM": weighted_mean(displacement[cohort], mass[cohort]).tolist(),
                "cohortMeanVelocityMPerS": weighted_mean(velocity[cohort], mass[cohort]).tolist(),
                "cohortRmsSpeedMPerS": float(np.sqrt(weighted_mean(np.square(velocity[cohort]).sum(axis=1), mass[cohort]))),
                "kineticEnergyJPerM": float(history[name]["kinetic_energy_j_per_m"][frame]),
                "maximumKappa": float(state["kappa"][frame].max()),
                "totalMassWithAccumulatedPlasticHistoryFraction": float(mass[state["kappa"][frame] > 0].sum() / mass.sum())}
        per_frame.append(row)
    with (OUTPUT / "same-id-saved-differences.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["frame", "time_s", "captured_particle_id", "srf1p4_minus_srf1_x_m", "delta_y_m",
                         "delta_vx_m_per_s", "delta_vy_m_per_s", "delta_kappa", "delta_J", "max_abs_delta_cauchy_stress_pa"])
        for frame, time in enumerate(times):
            for particle in range(n):
                writer.writerow([frame, format(time, ".17g"), particle,
                                 *[format(value, ".17g") for value in [*delta["position"][frame, particle],
                                     *delta["velocity"][frame, particle], delta["kappa"][frame, particle],
                                     delta["J"][frame, particle], np.abs(stress_delta[frame, particle]).max()]]])
    # Initial physical bins describe the spatial distribution of accumulated
    # history, not a verified shear-band width or a current-yielded indicator.
    bins = np.floor(initial).astype(int)
    with (OUTPUT / "final-initial-1m-spatial-bins.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["initial_bin_x_m", "initial_bin_y_m", "mass_kg_per_m", "srf1_mean_kappa", "srf1p4_mean_kappa",
                         "srf1_mean_dx_m", "srf1_mean_dy_m", "srf1p4_mean_dx_m", "srf1p4_mean_dy_m"])
        for x, y in sorted(set(map(tuple, bins))):
            selected = np.all(bins == (x, y), axis=1)
            values = [x, y, float(mass[selected].sum())]
            values.extend(float(weighted_mean(physical[name]["kappa"][-1, selected], mass[selected])) for name in RUNS)
            values.extend(float(value) for name in RUNS
                          for value in weighted_mean(physical[name]["displacement"][-1, selected], mass[selected]))
            writer.writerow(values)
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    for name, label in (("srf1", "SRF1"), ("srf1p4", "SRF1.40")):
        centroid = np.array([row["trials"][name]["cohortCentroidDisplacementM"] for row in per_frame])
        axes[0, 0].plot(times, centroid[:, 0] * 1000, label=label)
        axes[0, 1].plot(times, centroid[:, 1] * 1000, label=label)
        axes[1, 0].plot(times, history[name]["kinetic_energy_j_per_m"], label=label)
        axes[1, 1].plot(times, [row["trials"][name]["maximumKappa"] for row in per_frame], label=label)
    for ax, ylabel in zip(axes.flat, ("fixed-cohort Δx (mm)", "fixed-cohort Δy (mm)", "kinetic energy (J/m)", "maximum native plastic history κ")):
        ax.axvline(2, color="0.5", lw=0.8, ls="--")
        ax.set(xlim=(0, 6), xlabel="actual saved time (s)", ylabel=ylabel)
        ax.grid(alpha=0.2)
        ax.legend()
    fig.suptitle("Predeclared coarse gravity/SSR pair: actual saved histories\nNo coherent landslide detected; κ and solver completion are not damage/failure validation")
    figure = OUTPUT / "paired-observables.png"
    fig.savefig(figure, dpi=150)
    plt.close(fig)
    peak = {name: int(np.argmax(h["kinetic_energy_j_per_m"])) for name, h in history.items()}
    window_summary = {}
    for name, review in reviews.items():
        window_summary[name] = {key: {"status": window["status"], "referenceTimeS": window["referenceTimeS"],
                                      "final": window["states"][-1]} for key, window in review["motionWindows"].items()}
    final_difference = {window: (np.array(window_summary["srf1p4"][window]["final"]["cohortCentroidDisplacementM"])
                                  - np.array(window_summary["srf1"][window]["final"]["cohortCentroidDisplacementM"])).tolist()
                        for window in ("entire", "post2s")}
    inputs = [record(path / relative) for path in RUNS.values()
              for relative in ("manifest.json", "history.csv", "particles.csv", "source/source-manifest.json",
                               "source/case.lisp", "review-001/review.json", "review-001/physical-spatial-review.json")]
    result = {"schema": "cl-mpm.unnotched-gravity.paired-review.v1", "createdUtc": datetime.now(timezone.utc).isoformat(),
              "comparisonStatus": "PASS_TIME_ID_INPUT_ALIGNMENT_AND_METRIC_EXTRACTION",
              "physicalResult": "BOTH_TRIALS_SETTLE_NO_COHERENT_LANDSLIDE_DETECTED",
              "nativeCompleteBoth": True, "savedTimes": frames, "particlesPerTime": n,
              "actualPairedRows": frames * n, "interpolation": False, "sameInitialGeometryIdsMassCohort": True,
              "configChanges": config_changes, "changedSourceMembers": changed_sources,
              "allOtherFrozenSourceHashesIdentical": True, "caseDifferenceOnlyLiteralSrf": True,
              "wholeAndHoldWindows": window_summary,
              "srf1p4MinusSrf1FinalCentroidDisplacementM": final_difference,
              "kineticPeaks": {name: {"timeS": float(times[index]), "energyJPerM": float(history[name]["kinetic_energy_j_per_m"][index])}
                               for name, index in peak.items()},
              "kineticFinalJPerM": {name: float(h["kinetic_energy_j_per_m"][-1]) for name, h in history.items()},
              "maximumToeMassFractions": {name: max(row["totalMassFractionPastToePlusHalfH"] for row in r["toeHistory"])
                                           for name, r in reviews.items()},
              "maximumAllTimePositionComponentDifferenceM": float(np.abs(delta["position"]).max()),
              "maximumAllTimeVelocityComponentDifferenceMPerS": float(np.abs(delta["velocity"]).max()),
              "maximumAllTimeKappaDifference": float(np.abs(delta["kappa"]).max()),
              "maximumAllTimeCauchyStressComponentDifferencePa": float(np.abs(stress_delta).max()),
              "perFrame": per_frame, "landslideVerified": False, "scientificallyValidated": False,
              "limitations": ["Strength reduction increases plastic history/deformation here but neither run establishes coherent failure.",
                              "The same coarse explicit geometry/ramp/fixed-base adaptation remains different from a fully verified paper benchmark.",
                              "Kappa-weighted spatial bins are history distribution diagnostics, not measured shear-band width or damage.",
                              "No factor of safety, mesh convergence, calibrated runout or energy closure is inferred.",
                              "Existing SRF1.40 audit/render were not repeated; only new paired arithmetic and aggregate history plots were executed."],
              "inputHashes": inputs, "comparisonScript": record(Path(__file__)),
              "outputs": [record(OUTPUT / name) for name in ("same-id-saved-differences.csv", "final-initial-1m-spatial-bins.csv", "paired-observables.png")]}
    write_json(OUTPUT / "paired-result.json", result)
    print(json.dumps({key: result[key] for key in ("comparisonStatus", "physicalResult", "actualPairedRows",
        "srf1p4MinusSrf1FinalCentroidDisplacementM", "kineticPeaks", "kineticFinalJPerM", "maximumToeMassFractions")}, indent=2))


if __name__ == "__main__":
    main()
