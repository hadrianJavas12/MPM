#!/usr/bin/env python3
"""Audit one fine native run, then compare meshes using fixed metre observers.

The public entry point freezes this script, its imported analysis sources and
contracts before launching a copied Python analysis process. It never launches
MPM. Coarse data is compared only; its audit and geometry/video are not rerun.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

import numpy as np


REPOSITORY = Path(__file__).resolve().parents[1]
REFERENCES = REPOSITORY / "research/references/unnotched-mc-ssr"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def file_record(path: Path):
    payload = path.read_bytes()
    return {"path": str(path.resolve()), "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}


def write_json(path: Path, value):
    if path.exists():
        raise ValueError(f"Preserve previous analysis: {path}")
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def load_review_module(support_dir: Path):
    """Load the copied reader explicitly, then the copied native audit module."""
    modules = (("plot_m5_cliff_comparison", "plot_m5_cliff_comparison.py"),
               ("_gravity_native_audit_frozen", "review-gravity-slope.py"))
    loaded = None
    for name, filename in modules:
        path = support_dir / filename
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Cannot load copied analysis: {path}")
        loaded = importlib.util.module_from_spec(spec)
        sys.modules[name] = loaded
        spec.loader.exec_module(loaded)
    return loaded


def validate_observer(refinement_contract: dict) -> dict:
    """Reject drift: existing native helpers implement this exact metre observer."""
    observer = refinement_contract["comparisonObserver"]
    expected = {
        "initialCohort": {"xGreaterThanM": 2, "yGreaterThanM": 2},
        "initialAdjacencyRadiusM": 1.01,
        "movingMinimumDxM": 0.25,
        "movingMinimumDownslopeDisplacementM": 0.5,
        "minimumConnectedMovingFractionOfCohortMass": 0.1,
        "minimumPositiveDxFractionOfComponentMass": 0.75,
        "componentVelocity": {"minimumMeanVxMPerS": 0.001, "allSavedStatesDurationS": 1,
                              "fixedComponentIDsWithinEachInterval": True},
        "runoutMinimumFractionOfInitialTotalMass": 0.01,
        "runoutXGreaterThanM": 32.5,
        "windows": ["0-6s", "2-6s relative to saved2s"],
    }
    for key, value in expected.items():
        if observer.get(key) != value:
            raise ValueError(f"Preregistered physical observer changed: {key}")
    return observer


def common_physical_windows(native, states: list, initial_positions: np.ndarray,
                            masses: np.ndarray, beta: float, observer: dict) -> dict:
    cutoff = observer["initialCohort"]
    cohort = ((initial_positions[:, 0] > cutoff["xGreaterThanM"])
              & (initial_positions[:, 1] > cutoff["yGreaterThanM"]))
    if not cohort.any() or not np.all(masses > 0):
        raise ValueError("Physical cohort must have positive mass")
    # This is the fixed observer's one-metre scale, not the fine mesh size.
    # The actual fine config and its separate h-scaled audit are not modified.
    observer_scale_m = 1.0
    graph = native.initial_graph(initial_positions, cohort, observer_scale_m)
    windows = {"entire": native.motion_window(states, 0, graph, cohort, masses,
                    observer_scale_m, beta, "common metre observer: entire available matched saved span")}
    hold = [index for index, state in enumerate(states) if np.isclose(state["time"], 2,
                                                                   atol=native.TIME_ATOL, rtol=0)]
    windows["post2s"] = (native.motion_window(states, hold[0], graph, cohort, masses,
                            observer_scale_m, beta, "common metre observer: displacement relative to actual saved2s")
                          if hold else {"status": "NOT_EVALUATED", "reason": "No actual saved2s state; no interpolation"})
    return {"cohortCount": int(cohort.sum()), "cohortMassKgPerM": float(masses[cohort].sum()),
            "observerScaleM": observer_scale_m, "meshSizeWasNotChanged": True,
            "windows": windows}


def physical_runout(states: list, masses: np.ndarray, observer: dict) -> list[dict]:
    rows = []
    for state in states:
        x = state["positions"][:, 0]
        order = np.argsort(x, kind="stable")
        middle = min(int(np.searchsorted(np.cumsum(masses[order]), masses.sum() / 2)), len(masses) - 1)
        rows.append({"frame": state["frame"], "timeS": state["time"],
                     "massFractionPastPhysicalToe": float(masses[x > observer["runoutXGreaterThanM"]].sum() / masses.sum()),
                     "frontXM": float(x.max()), "medianXM": float(x[order[middle]]),
                     "centroidXM": float(np.average(x, weights=masses))})
    return rows


def validate_contracts(fine: dict, original: dict, refinement: dict,
                       fine_path: Path, original_path: Path, refinement_path: Path):
    if fine["refinementRole"] != "NATIVE_INTEGRITY_AND_H_SCALED_DIAGNOSTICS_ONLY":
        raise ValueError("Fine audit contract role is not separate from the physical observer")
    if fine["detectionConventions"] != original["detectionConventions"]:
        raise ValueError("Fine native h-scaled criteria differ from the original contract")
    if fine["numerics"]["meshSizeM"] != 0.5 or fine["independentTrials"] != [1.4]:
        raise ValueError("Wrong fine native mesh/SRF contract")
    for key, path in (("originalStudy", original_path), ("refinementStudy", refinement_path)):
        if fine["sourceContracts"][key]["sha256"] != file_record(path)["sha256"]:
            raise ValueError(f"Fine audit contract parent hash mismatch: {key}")
    return {"fineAudit": file_record(fine_path), "originalStudy": file_record(original_path),
            "refinementStudy": file_record(refinement_path)}


def verify_fine_sources(run: Path) -> dict:
    manifest_path = run / "source/source-manifest.json"
    manifest = read_json(manifest_path)
    verified = []
    for expected in manifest["files"]:
        path = (run / expected["path"]).resolve()
        if not path.is_relative_to((run / "source").resolve()):
            raise ValueError("Frozen source entry escapes source directory")
        actual = file_record(path)
        if (actual["sha256"], actual["bytes"]) != (expected["sha256"], expected["bytes"]):
            raise ValueError(f"Fine executed source mismatch: {expected['path']}")
        verified.append({"path": expected["path"], "sha256": actual["sha256"], "bytes": actual["bytes"]})
    provenance_path = run / "source-provenance.json"
    provenance = read_json(provenance_path)
    backend = provenance["nativeBackend"]
    dll = next(row for row in verified if row["path"] == "source/libs/kirchoff.dll")
    if not (provenance["sourceSnapshotExactLoadedBytes"] and provenance["copiedByteEqualityBeforeLoad"]
            and backend["sha256"] == dll["sha256"]
            and backend["verifiedBy"] == "GetModuleHandleW/GetModuleFileNameW"):
        raise ValueError("Recorded fine loaded-source/mapped-DLL proof disagrees")
    return {"files": verified, "allManifestHashesAndLengthsMatched": True,
            "sourceManifest": file_record(manifest_path), "runtimeProvenance": file_record(provenance_path),
            "actualMappedDll": backend, "scope": "File hash verification plus existing runtime proof; no process/native query"}


def load_coarse_for_comparison(native, run: Path, review_path: Path, original_hash: str):
    """Read CSVs anchored to the prior audit; do not call its audit/VTK functions."""
    reviewed = read_json(review_path)
    if reviewed["integrityStatus"] != "PASS" or not reviewed["nativeComplete"]:
        raise ValueError("Coarse reference requires an existing complete independent audit")
    if reviewed["contract"]["sha256"] != original_hash:
        raise ValueError("Coarse reference was not reviewed against the original contract")
    for filename in ("manifest.json", "history.csv", "particles.csv"):
        path = run / filename
        matches = [row for row in reviewed["inputHashes"] if Path(row["path"]).resolve() == path.resolve()]
        if len(matches) != 1 or matches[0]["sha256"] != file_record(path)["sha256"]:
            raise ValueError(f"Coarse input changed since its prior audit: {filename}")
    manifest = read_json(run / "manifest.json")
    particles, history = native.native_csv(run / "particles.csv"), native.native_csv(run / "history.csv")
    all_frames = native.integral(particles["frame"], "coarse comparison frames")
    states = []
    for frame in native.integral(history["frame"], "coarse history frames"):
        selected = all_frames == frame
        values = {name: column[selected] for name, column in particles.items()}
        ids = native.integral(values["particle_id"], "coarse comparison captured IDs")
        if not np.array_equal(ids, np.arange(len(ids))):
            raise ValueError("Coarse comparison IDs reordered; no cross-mesh ID matching allowed")
        states.append({"frame": int(frame), "time": float(history["time_s"][frame]),
                       "positions": np.column_stack([values["x_m"], values["y_m"]]),
                       "velocity": np.column_stack([values["vx_m_per_s"], values["vy_m_per_s"]]),
                       "kappa": values["mc_kappa"], "J": values["J"], "masses": values["mass_kg_per_m"],
                       "kinetic": float(history["kinetic_energy_j_per_m"][frame])})
    return states, manifest["config"], reviewed


def matched_saved_states(native, coarse: list, fine: list):
    by_frame = {state["frame"]: state for state in coarse}
    selected, maximum_time_delta = [], 0.0
    for state in fine:
        reference = by_frame.get(state["frame"])
        if reference is None or not np.isclose(reference["time"], state["time"],
                atol=native.TIME_ATOL, rtol=native.TIME_RTOL):
            raise ValueError("No same-frame/time coarse state; interpolation is not permitted")
        maximum_time_delta = max(maximum_time_delta, abs(reference["time"] - state["time"]))
        selected.append(reference)
    return selected, maximum_time_delta


def physical_distributions(native, states: list, initial: np.ndarray, masses: np.ndarray,
                           beta: float, observer: dict) -> list:
    region = observer["initialCohort"]
    selected = (initial[:, 0] > region["xGreaterThanM"]) & (initial[:, 1] > region["yGreaterThanM"])
    direction = np.array([np.cos(beta), -np.sin(beta)])
    rows = []
    for state in states:
        delta, speed = state["positions"] - initial, np.linalg.norm(state["velocity"], axis=1)
        rows.append({"frame": state["frame"], "timeS": state["time"], "kineticEnergyJPerM": state["kinetic"],
                     "cohortMeanVelocityMPerS": np.average(state["velocity"][selected], axis=0, weights=masses[selected]).tolist(),
                     "cohortCentroidDisplacementM": np.average(delta[selected], axis=0, weights=masses[selected]).tolist(),
                     "massWeightedQuantiles": {name: {str(q): native.weighted_quantile(values[selected], masses[selected], q)
                                                          for q in (0.5, 0.9, 0.95)}
                         for name, values in (("dxM", delta[:, 0]), ("downslopeDisplacementM", delta @ direction),
                                              ("speedMPerS", speed), ("nativeKappa", state["kappa"]))}})
    return rows


def write_spatial_bins(output: Path, trials: dict):
    import csv
    keys = set()
    for trial in trials.values():
        trial["bins"] = np.floor(trial["initial"]).astype(int)
        keys.update(map(tuple, trial["bins"]))
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["frame", "time_s", "initial_bin_x_m", "initial_bin_y_m", "mesh_role",
                         "mass_kg_per_m", "mean_dx_m", "mean_dy_m", "mean_vx_m_per_s", "mean_vy_m_per_s", "mean_native_kappa"])
        for role, trial in trials.items():
            for x, y in sorted(keys):
                selected = np.all(trial["bins"] == (x, y), axis=1)
                if not selected.any():
                    continue
                weights = trial["masses"][selected]
                for state in trial["states"]:
                    displacement = state["positions"][selected] - trial["initial"][selected]
                    writer.writerow([state["frame"], state["time"], int(x), int(y), role, float(weights.sum()),
                                     *np.average(displacement, axis=0, weights=weights),
                                     *np.average(state["velocity"][selected], axis=0, weights=weights),
                                     float(np.average(state["kappa"][selected], weights=weights))])


def render_comparison_histories(native, distributions: dict, output: Path):
    fig, axes = native.plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    for name, rows in distributions.items():
        times = [row["timeS"] for row in rows]
        axes[0, 0].plot(times, [row["cohortCentroidDisplacementM"][0] for row in rows], label=name)
        axes[0, 1].plot(times, [row["cohortCentroidDisplacementM"][1] for row in rows], label=name)
        axes[1, 0].plot(times, [row["kineticEnergyJPerM"] for row in rows], label=name)
        axes[1, 1].plot(times, [row["massWeightedQuantiles"]["nativeKappa"]["0.95"] for row in rows], label=name)
    for ax, ylabel in zip(axes.flat, ("common-cohort Δx (m)", "common-cohort Δy (m)", "kinetic energy (J/m)", "common-cohort95% native κ")):
        ax.set(xlabel="actual saved time (s)", ylabel=ylabel)
        if rows[-1]["timeS"] >= 2:
            ax.axvline(2, color="0.5", lw=0.8, ls="--")
        ax.grid(alpha=0.2)
        ax.legend()
    fig.suptitle("Coupled space/time refinement · fixed physical metre observer\nNo cross-mesh ID matching; no automatic landslide/scientific validation")
    fig.savefig(output, dpi=150)
    native.plt.close(fig)


def run_frozen(args):
    output, support = args.output_dir.resolve(), Path(__file__).resolve().parent
    expected_support = output / "analysis-support"
    if support != expected_support.resolve():
        raise ValueError("Internal analysis must execute its frozen copy under output/analysis-support")
    preparation = read_json(output / "support-pre-execution.json")
    for row in preparation["copies"]:
        actual = file_record(Path(row["path"]))
        if (actual["sha256"], actual["bytes"]) != (row["sha256"], row["bytes"]):
            raise ValueError("Frozen analysis support changed before execution")
    native = load_review_module(support)
    fine_contract, original, refinement = map(read_json,
        (args.fine_contract, args.original_contract, args.refinement_contract))
    contracts = validate_contracts(fine_contract, original, refinement,
        args.fine_contract, args.original_contract, args.refinement_contract)
    observer = validate_observer(refinement)
    status_path = args.run_dir.parent / (args.run_dir.name + "-status.json")
    if status_path.is_file() and read_json(status_path).get("status") in ("STARTING", "NATIVE_RUNNING"):
        raise ValueError("Fine native process is active; saved-data audit must wait for terminal status")
    fine_report, fine_states, fine_config = native.inspect(args.run_dir, args.fine_contract, args.source_root)
    fine_report["auditRole"] = "FINE_NATIVE_INTEGRITY_AND_SEPARATE_H_SCALED_DIAGNOSTICS"
    fine_report["crossMeshComparisonIsSeparate"] = True
    write_json(output / "fine-native-review.json", fine_report)
    # Subsequent stages retain their own errors; a comparison/media failure does
    # not erase an already completed native saved-state audit.
    provenance = verify_fine_sources(args.run_dir)
    write_json(output / "fine-terminal-source-verification.json", provenance)
    if fine_report["integrityStatus"] != "PASS":
        raise ValueError("Fine native integrity failed; retained audit/source proof, comparison and media not run")
    media = {"files": [], "nativeIntegrity": fine_report["integrityStatus"]}
    try:
        media["files"].append(file_record(native.render_static(fine_states, fine_config, output)))
        if args.video and fine_report["integrityStatus"] == "PASS":
            media["files"].append(native.render_video(fine_states, fine_config, output))
        elif args.video:
            media["videoSkipped"] = "Native integrity failed; no fabricated successful video"
    except Exception as error:
        media["error"] = f"{type(error).__name__}: {error}"
    write_json(output / "fine-media.json", media)
    coarse_states, coarse_config, coarse_review = load_coarse_for_comparison(native,
        args.coarse_run_dir, args.coarse_review, contracts["originalStudy"]["sha256"])
    if set(coarse_config) != set(fine_config):
        raise ValueError("Coarse and fine configuration key sets differ")
    changes = [{"key": key, "coarse": coarse_config[key], "fine": fine_config[key]}
               for key in sorted(coarse_config) if coarse_config[key] != fine_config[key]]
    if changes != [{"key": "meshSize", "coarse": 1.0, "fine": 0.5}]:
        raise ValueError(f"Refinement inputs differ beyond the registered mesh change: {changes}")
    if len(fine_states[0]["masses"]) != 3520 or len(coarse_states[0]["masses"]) != 880:
        raise ValueError("Wrong fine/coarse particle counts for the registered study")
    coarse_states, maximum_time_delta = matched_saved_states(native, coarse_states, fine_states)
    trials = {"coarse_h1": {"states": coarse_states}, "fine_h05": {"states": fine_states}}
    comparisons, distributions = {}, {}
    beta = np.deg2rad(fine_config["slope"])
    for role, trial in trials.items():
        trial["initial"] = trial["states"][0]["positions"].copy()
        trial["masses"] = trial["states"][0]["masses"].copy()
        windows = common_physical_windows(native, trial["states"], trial["initial"], trial["masses"], beta, observer)
        runout = physical_runout(trial["states"], trial["masses"], observer)
        comparisons[role] = {"motion": windows, "runout": runout,
            "coherentMotionCandidate": any(window["status"] == "PASS" for window in windows["windows"].values()),
            "separateRunoutCandidate": any(row["massFractionPastPhysicalToe"] >= observer["runoutMinimumFractionOfInitialTotalMass"] for row in runout)}
        distributions[role] = physical_distributions(native, trial["states"], trial["initial"], trial["masses"], beta, observer)
    bins = output / "common-initial-1m-spatial-bins.csv"
    write_spatial_bins(bins, trials)
    comparison_image = output / "common-physical-histories.png"
    render_comparison_histories(native, distributions, comparison_image)
    common = {"schema": "cl-mpm.gravity-refinement.common-physical-review.v1",
        "nativeFineIntegrity": fine_report["integrityStatus"], "nativeFineComplete": fine_report["nativeComplete"],
        "scope": "Same physical regions/bins/distributions; coarse CSVs compared, not independently re-audited or geometry/video rerendered",
        "observer": observer, "maximumMatchedSavedTimeDifferenceS": maximum_time_delta,
        "interpolation": False, "particleIdsTransferableAcrossMeshes": False,
        "inputChanges": changes, "trials": comparisons, "massWeightedDistributions": distributions,
        "nativeHScaledDiagnosticsSeparate": {"fine": fine_report["motionWindows"], "coarsePriorReview": coarse_review["motionWindows"]},
        "landslideVerified": False, "scientificallyValidated": False,
        "manualSpatialMechanismReviewRequired": comparisons["fine_h05"]["coherentMotionCandidate"],
        "contracts": contracts, "coarsePriorAudit": file_record(args.coarse_review),
        "comparisonSources": [file_record(args.coarse_run_dir / name) for name in ("manifest.json", "history.csv", "particles.csv")],
        "analysisScript": file_record(Path(__file__)), "outputs": [file_record(bins), file_record(comparison_image)],
        "limits": refinement["limits"] + ["Motion thresholds are diagnostic conventions, not universal failure criteria.",
             "Fine native h-scaled cohort/detector is not substituted for the fixed metre observer.",
             "Initial1m bin history distributions are not measured shear-band width or damage.",
             "Current-state and saved-interval checks do not certify unsaved states or calibrated runout."]}
    write_json(output / "common-physical-review.json", common)
    print(json.dumps({"fineNativeIntegrity": fine_report["integrityStatus"], "fineNativeComplete": fine_report["nativeComplete"],
        "fineHScaledMotion": {key: row["status"] for key, row in fine_report["motionWindows"].items()},
        "commonPhysicalMotion": {role: {key: row["status"] for key, row in result["motion"]["windows"].items()}
                                  for role, result in comparisons.items()}, "landslideVerified": False}, indent=2))
    return 0 if fine_report["integrityStatus"] == "PASS" and "error" not in media else 1


def freeze_and_run(args):
    output = args.output_dir.resolve()
    if output.exists():
        raise ValueError("Use a fresh output directory; prior stages/errors must be preserved")
    support = output / "analysis-support"
    support.mkdir(parents=True)
    source_dir = Path(__file__).resolve().parent
    copies = []
    for source, filename in ((Path(__file__), "review-gravity-refinement.py"),
            (source_dir / "review-gravity-slope.py", "review-gravity-slope.py"),
            (source_dir / "plot_m5_cliff_comparison.py", "plot_m5_cliff_comparison.py"),
            (args.fine_contract, "fine-audit-contract.json"),
            (args.refinement_contract, "refinement-contract.json"),
            (args.original_contract, "original-study-contract.json")):
        destination = support / filename
        shutil.copyfile(source, destination)
        copied = file_record(destination)
        if copied["sha256"] != file_record(source)["sha256"]:
            raise ValueError("Analysis/support copy mismatch")
        copies.append({**copied, "originalPath": str(source.resolve())})
    write_json(output / "support-pre-execution.json", {"preparedUtc": datetime.now(timezone.utc).isoformat(),
        "copies": copies, "scope": "Copied wrapper/modules/contracts before any saved-data audit, detector or render"})
    command = [sys.executable, str(support / "review-gravity-refinement.py"), "--execute-frozen",
        "--run-dir", str(args.run_dir.resolve()), "--coarse-run-dir", str(args.coarse_run_dir.resolve()),
        "--coarse-review", str(args.coarse_review.resolve()), "--output-dir", str(output),
        "--source-root", str(args.source_root.resolve()),
        "--fine-contract", str(support / "fine-audit-contract.json"),
        "--refinement-contract", str(support / "refinement-contract.json"),
        "--original-contract", str(support / "original-study-contract.json")]
    if args.video:
        command.append("--video")
    with (output / "frozen-execution.log").open("w", encoding="utf-8") as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=False)
    write_json(output / "refinement-review-exit.json", {"exitCode": result.returncode,
        "finishedUtc": datetime.now(timezone.utc).isoformat(), "command": command,
        "scope": "One fine saved-data audit/render and common physical comparison; no native process launched"})
    print(json.dumps({"output": str(output), "exitCode": result.returncode,
                      "log": str(output / "frozen-execution.log")}, indent=2))
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True, help="Terminal fine native output")
    parser.add_argument("--coarse-run-dir", type=Path, required=True, help="Already audited h1 SRF1.4 output")
    parser.add_argument("--coarse-review", type=Path, help="Default COARSE/review-001/review.json")
    parser.add_argument("--output-dir", type=Path, help="Fresh directory; default FINE/refinement-review-001")
    parser.add_argument("--source-root", type=Path, help="Default FINE/source")
    parser.add_argument("--fine-contract", type=Path, default=REFERENCES / "refinement-audit-contract.json")
    parser.add_argument("--refinement-contract", type=Path, default=REFERENCES / "refinement-contract.json")
    parser.add_argument("--original-contract", type=Path, default=REFERENCES / "contract.json")
    parser.add_argument("--video", action="store_true", help="Actual fine saved states only at4fps, without interpolation")
    parser.add_argument("--execute-frozen", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    args.output_dir = args.output_dir or args.run_dir / "refinement-review-001"
    args.source_root = args.source_root or args.run_dir / "source"
    args.coarse_review = args.coarse_review or args.coarse_run_dir / "review-001/review.json"
    try:
        return run_frozen(args) if args.execute_frozen else freeze_and_run(args)
    except Exception as error:
        if args.output_dir.is_dir():
            destination = args.output_dir / "stage-failure.json"
            if not destination.exists():
                write_json(destination, {"error": f"{type(error).__name__}: {error}", "traceback": traceback.format_exc(),
                    "landslideVerified": False, "scientificallyValidated": False,
                    "fineNativeAuditRetained": (args.output_dir / "fine-native-review.json").is_file(),
                    "scope": "Saved-data analysis failure; preserve completed earlier stages, do not rerun native simulation"})
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
