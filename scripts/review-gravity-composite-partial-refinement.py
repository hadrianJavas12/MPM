"""Compare the saved 0--5.2s prefix after the failed fine run; never run MPM.

This separate post-failure observer does not relax the complete-pair wrapper.
Its public entry point freezes five Python sources, unchanged contracts and both
existing variant reviews before a copied process reads any numerical CSV data.
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


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_SHA256 = "0836d61273184248868a0ce1c8bd4d7312d9b83be052ec5f9ce01d465a905827"
PYTHON_SOURCES = (Path(__file__).name, "review-gravity-composite-refinement.py",
                  "review-gravity-refinement.py", "review-gravity-slope.py",
                  "plot_m5_cliff_comparison.py")
INPUT_NAMES = ("manifest.json", "history.csv", "particles.csv")
VARIANT = "perfect-mc-composite-apex"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def record(path):
    payload = path.read_bytes()
    return {"path": str(path.resolve()), "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload)}


def write_json(path, value):
    require(not path.exists(), f"Preserve previous analysis: {path}")
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def load_module(support, name, filename):
    path = support / filename
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"Cannot load copied helper: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    require(Path(module.__file__).resolve().parent == support, "Helper was not copied")
    return module


def bind_review(run, report, audit_contract, expected_sha, *, partial):
    """Bind saved bytes to an existing audit; do not repeat source/VTK audits."""
    require(report.get("integrityStatus") == "PASS"
            and report.get("nativeComplete") is (not partial), "Wrong prior audit completion/integrity")
    require(report.get("boundedControlOnly") is False and report.get("analysisSourceAfterMatch") is True,
            "Prior audit is bounded or its analysis bytes changed")
    require(not any(key in report for key in ("error", "sourceAfterError", "mediaError")),
            "Prior audit retains an unresolved analysis-stage error")
    source = report["sourceVerification"]
    require(source.get("status") == "PASS" and source.get("frozenSourcesVerified") == 287
            and source.get("nativeBackend", {}).get("verifiedBy") == "GetModuleHandleW/GetModuleFileNameW",
            "Existing native-source/DLL proof is missing")
    require(Path(report["nativeEvidenceRoot"]).resolve() == run, "Prior audit belongs to another run")
    variant = report["variantReview"]
    require(variant.get("status") == "PASS" and variant.get("materialVariant") == VARIANT
            and variant.get("boundedControlOnly") is False, "Wrong or bounded variant audit")
    base = report["baseReview"]
    require(base.get("integrityStatus") == "PASS" and base.get("nativeComplete") is (not partial)
            and Path(base["runDirectory"]).resolve() == run and base.get("failures") == [],
            "Base audit has the wrong run/completion or saved-integrity failures")
    require(base.get("nativeStatus") == ("failed" if partial else "complete")
            and base.get("savedScope") == ("partial-saved-states-only" if partial else "complete")
            and base.get("savedFrames") == (53 if partial else 61)
            and base.get("lastSavedTimeS") == (5.2 if partial else 6.0), "Unexpected prior saved scope")
    require(base["contract"]["sha256"] == expected_sha
            and record(audit_contract)["sha256"] == expected_sha, "Prior audit contract hash differs")
    inputs = []
    for filename in INPUT_NAMES:
        actual = record(run / filename)
        matches = [row for row in base["inputHashes"] if Path(row["path"]).resolve() == run / filename]
        require(len(matches) == 1 and matches[0] == actual, f"Saved input changed since audit: {filename}")
        inputs.append(actual)
    manifest = read_json(run / "manifest.json")
    require(manifest.get("complete") is (not partial)
            and manifest.get("status") == ("failed" if partial else "complete")
            and manifest.get("savedFrames") == (53 if partial else 61)
            and manifest.get("lastSavedTimeS") == (5.2 if partial else 6.0), "Native manifest scope differs")
    status_path = Path(str(run) + "-status.json")
    status = read_json(status_path)
    require(status.get("status") == ("FAILED_NATIVE" if partial else "NATIVE_COMPLETE_REVIEW_PENDING")
            and status.get("nativeExitCode") == (1 if partial else 0)
            and status.get("nativeComplete") is (not partial), "Native exit/status is not terminal as expected")
    return base, manifest, inputs, record(status_path)


def load_saved_csv(native, run, expected_count, expected_frames):
    """Use the native CSV reader only; no audit, VTK, render or solver calls."""
    particles = native.native_csv(run / "particles.csv")
    history = native.native_csv(run / "history.csv")
    frames = native.integral(history["frame"], "partial observer history frames")
    require(np.array_equal(frames, np.arange(expected_frames)), "History frame prefix differs")
    all_frames = native.integral(particles["frame"], "partial observer particle frames")
    require(set(all_frames) == set(frames), "Particle/history frame sets differ")
    require(np.all(np.diff(history["time_s"]) > 0) and history["time_s"][0] == 0,
            "Actual saved times must start at zero and strictly increase")
    states = []
    for index, frame in enumerate(frames):
        selected = all_frames == frame
        values = {name: column[selected] for name, column in particles.items()}
        ids = native.integral(values["particle_id"], "within-run captured IDs")
        require(np.array_equal(ids, np.arange(expected_count)), "Within-run IDs/count/order differ")
        time = float(history["time_s"][index])
        require(np.allclose(values["time_s"], time, atol=native.TIME_ATOL, rtol=native.TIME_RTOL),
                "Particle/history times differ")
        states.append({"frame": int(frame), "time": time,
            "positions": np.column_stack([values["x_m"], values["y_m"]]),
            "velocity": np.column_stack([values["vx_m_per_s"], values["vy_m_per_s"]]),
            "kappa": values["mc_kappa"], "J": values["J"], "masses": values["mass_kg_per_m"],
            "kinetic": float(history["kinetic_energy_j_per_m"][index])})
    require(all(np.array_equal(state["masses"], states[0]["masses"]) for state in states),
            "Saved particle masses changed")
    return states


def scalar_summary(comparisons, distributions):
    result = {}
    for role, trial in comparisons.items():
        last = distributions[role][-1]
        result[role] = {"nativeComplete": role == "coarse_h1", "matchedSavedFrames": 53,
            "firstMatchedTimeS": 0.0, "lastMatchedTimeS": 5.2,
            "motionWindows": {name: {"status": row["status"],
                "firstDetectionTimeS": row["candidate"]["detectionTimeS"] if row.get("candidate") else None}
                for name, row in trial["motion"]["windows"].items()},
            "maximumMassFractionPastPhysicalToe": max(row["massFractionPastPhysicalToe"] for row in trial["runout"]),
            "coherentMotionCandidate": trial["coherentMotionCandidate"],
            "separateRunoutCandidate": trial["separateRunoutCandidate"],
            "finalCohortCentroidDxM": last["cohortCentroidDisplacementM"][0],
            "finalCohortCentroidDyM": last["cohortCentroidDisplacementM"][1],
            "finalCohortMeanVxMPerS": last["cohortMeanVelocityMPerS"][0],
            "finalCohortMeanVyMPerS": last["cohortMeanVelocityMPerS"][1]}
    return result


def run_frozen(args):
    output, support = args.output_dir.resolve(), Path(__file__).resolve().parent
    require(support == output / "analysis-support", "Execute only the frozen partial observer copy")
    prepared = read_json(output / "support-pre-execution.json")
    require(prepared["pythonSourceCount"] == 5 and prepared["nativeLaunchPreregistration"] is False,
            "Analysis-source timing/count provenance differs")
    for expected in prepared["copies"]:
        actual = record(Path(expected["path"]))
        require(Path(actual["path"]).parent == support and all(actual[key] == expected[key]
                for key in ("path", "sha256", "bytes")), "Frozen support changed before comparison")
    full = load_module(support, "_complete_composite_csv_helpers", "review-gravity-composite-refinement.py")
    helper = load_module(support, "_partial_common_metre_helpers", "review-gravity-refinement.py")
    native = helper.load_review_module(support)
    require(record(args.contract)["sha256"] == CONTRACT_SHA256, "Registered comparison contract changed")
    contract = read_json(args.contract)
    observer = helper.validate_observer(contract)
    runs = {"coarse_h1": args.coarse_run_dir.resolve(), "fine_h05": args.fine_run_dir.resolve()}
    trials, bindings = {}, {}
    for role, audit_key, count in (("coarse_h1", "coarseAudit", 880), ("fine_h05", "fineAudit", 3520)):
        partial = role == "fine_h05"
        prior = support / (role + "-prior-review.json")
        base, manifest, inputs, status = bind_review(runs[role], read_json(prior),
            support / (role + "-audit-contract.json"), contract[audit_key]["sha256"], partial=partial)
        require(manifest["config"]["duration"] == 6 and manifest["config"]["frames"] == 61
                and manifest["particleCount"] == count, "Requested full study/count differs")
        states = load_saved_csv(native, runs[role], count, 53 if partial else 61)
        require(np.isclose(states[-1]["time"], 5.2 if partial else 6.0,
                           atol=native.TIME_ATOL, rtol=0), "Last actual saved time differs")
        trials[role] = {"states": states, "config": manifest["config"]}
        bindings[role] = {"frozenPriorReview": record(prior), "nativeComplete": not partial,
            "nativeStatus": base["nativeStatus"], "savedScope": base["savedScope"],
            "priorSavedFrames": len(states), "priorLastSavedTimeS": states[-1]["time"],
            "nativeFailure": ({"error": manifest["error"], "attemptTimeS": manifest["attemptTimeS"],
                "lastSavedTimeS": manifest["lastSavedTimeS"], "nativeExitCode": 1} if partial else None),
            "priorIntegrityStatus": base["integrityStatus"], "priorVariantStatus": "PASS",
            "frozenAuditContract": record(support / (role + "-audit-contract.json")),
            "priorNativeSourceProofOnly": read_json(prior)["sourceVerification"],
            "terminalStatus": status, "inputs": inputs}
    changes = full.check_pair_configs(trials["coarse_h1"]["config"], trials["fine_h05"]["config"], contract)
    require(contract["expectedParticleCount"] == [880, 3520], "Registered counts changed")
    trials["coarse_h1"]["states"], time_delta = helper.matched_saved_states(native,
        trials["coarse_h1"]["states"], trials["fine_h05"]["states"])
    require(len(trials["coarse_h1"]["states"]) == 53, "Matched partial prefix differs")
    comparisons, distributions = {}, {}
    beta = np.deg2rad(trials["fine_h05"]["config"]["slope"])
    for role, trial in trials.items():
        trial["initial"] = trial["states"][0]["positions"].copy()
        trial["masses"] = trial["states"][0]["masses"].copy()
        motion = helper.common_physical_windows(native, trial["states"], trial["initial"], trial["masses"], beta, observer)
        runout = helper.physical_runout(trial["states"], trial["masses"], observer)
        comparisons[role] = {"motion": motion, "runout": runout,
            "coherentMotionCandidate": any(row["status"] == "PASS" for row in motion["windows"].values()),
            "separateRunoutCandidate": any(row["massFractionPastPhysicalToe"] >= observer["runoutMinimumFractionOfInitialTotalMass"] for row in runout)}
        distributions[role] = helper.physical_distributions(native, trial["states"], trial["initial"], trial["masses"], beta, observer)
    bins = output / "partial-common-initial-1m-spatial-bins.csv"
    helper.write_spatial_bins(bins, trials)
    for role, run in runs.items():
        require(bindings[role]["inputs"] == [record(run / name) for name in INPUT_NAMES]
                and bindings[role]["terminalStatus"] == record(Path(str(run) + "-status.json")),
                "Native saved inputs/status changed during comparison")
    compact = {"status": "PARTIAL_CSV_OBSERVER_COMPLETED", "scope": "ACTUAL_MATCHED_SAVED_PREFIX_0_TO_5.2S_ONLY",
        "fullPairCompleted": False, "convergenceEstablished": False, "landslideVerified": False,
        "scientificallyValidated": False, "trials": scalar_summary(comparisons, distributions)}
    result = {"schema": "cl-mpm.composite-partial-refinement.csv-observer.v1", **compact,
        "contract": record(args.contract), "registeredObserverUnchanged": observer,
        "windowScope": {"registered": observer["windows"], "evaluated": ["0-5.2s", "2-5.2s relative to actual saved2s"],
            "missingFineSavedSpan": "5.3-6s; no extrapolation beyond last saved5.2s", "preregisteredFullWindowsCompleted": False},
        "analysisProvenance": prepared, "inputChanges": changes, "priorAuditBindings": bindings,
        "maximumMatchedSavedTimeDifferenceS": time_delta, "interpolation": False,
        "particleIdsTransferableAcrossMeshes": False, "detailedTrials": comparisons,
        "massWeightedDistributions": distributions,
        "fineMinusCoarseDistributions": full.distribution_differences(distributions["coarse_h1"], distributions["fine_h05"]),
        "outputs": [record(bins)], "nativeCalls": 0, "vtkAudits": 0, "vtkReads": 0, "renders": 0,
        "limits": contract["limits"] + ["Fine native failed; a saved-prefix observation cannot complete the registered6s pair or certify unsaved states."],
        "stopRule": contract["stopRule"]}
    write_json(output / "partial-common-physical-review.json", result)
    write_json(output / "partial-summary.json", compact)
    return 0


def freeze_and_run(args):
    output = args.output_dir.resolve()
    require(not output.exists(), "Use a fresh partial comparison directory")
    require(record(args.contract)["sha256"] == CONTRACT_SHA256, "Registered comparison contract changed")
    support = output / "analysis-support"
    support.mkdir(parents=True)
    args.output_created = True
    sources = [(Path(__file__).with_name(name), name) for name in PYTHON_SOURCES]
    sources += [(args.contract, "comparison-contract.json"), (args.coarse_review, "coarse_h1-prior-review.json"),
                (args.fine_review, "fine_h05-prior-review.json")]
    for role, review in (("coarse_h1", args.coarse_review), ("fine_h05", args.fine_review)):
        sources.append((Path(read_json(review)["baseReview"]["contract"]["path"]), role + "-audit-contract.json"))
    copies = []
    for source, name in sources:
        original = record(source)
        target = support / name
        shutil.copyfile(source, target)
        copied = record(target)
        require((original["sha256"], original["bytes"]) == (copied["sha256"], copied["bytes"]), "Support copy mismatch")
        copies.append({**copied, "originalPath": original["path"]})
    write_json(output / "support-pre-execution.json", {"preparedUtc": datetime.now(timezone.utc).isoformat(),
        "pythonSourceCount": 5, "nativeLaunchPreregistration": False,
        "timing": "Five current Python sources frozen AFTER fine native failure and both prior audits; the unchanged physical observer contract was preregistered. This partial wrapper is a post-failure descriptive analysis.",
        "copies": copies})
    command = [sys.executable, str(support / Path(__file__).name), "--execute-frozen",
        "--coarse-run-dir", str(args.coarse_run_dir.resolve()), "--fine-run-dir", str(args.fine_run_dir.resolve()),
        "--contract", str(support / "comparison-contract.json"), "--output-dir", str(output)]
    write_json(output / "command.json", {"command": command})
    with (output / "comparison.log").open("w", encoding="utf-8") as log:
        completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=False)
    write_json(output / "comparison-exit.json", {"exitCode": completed.returncode,
        "finishedUtc": datetime.now(timezone.utc).isoformat(), "nativeCalls": 0, "vtkAudits": 0, "vtkReads": 0, "renders": 0})
    after = [record(Path(row["path"])) for row in copies]
    unchanged = all(all(before[key] == final[key] for key in ("path", "sha256", "bytes"))
                    for before, final in zip(copies, after))
    write_json(output / "support-after-execution.json", {"copies": after, "unchanged": unchanged})
    require(unchanged, "Frozen support changed; retain failed provenance")
    if completed.returncode == 0:
        print(json.dumps(read_json(output / "partial-summary.json"), allow_nan=False))
    return completed.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coarse-run-dir", required=True, type=Path)
    parser.add_argument("--fine-run-dir", required=True, type=Path)
    parser.add_argument("--coarse-review", type=Path)
    parser.add_argument("--fine-review", type=Path)
    parser.add_argument("--contract", type=Path, default=ROOT / "research/references/unnotched-mc-ssr/composite-apex-refinement-contract.json")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--execute-frozen", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    args.coarse_review = args.coarse_review or args.coarse_run_dir / "variant-review-002/review.json"
    args.fine_review = args.fine_review or args.fine_run_dir / "variant-review-001/review.json"
    args.output_created = False
    try:
        return run_frozen(args) if args.execute_frozen else freeze_and_run(args)
    except Exception as error:
        if (args.execute_frozen or args.output_created) and args.output_dir.is_dir() and not (args.output_dir / "stage-failure.json").exists():
            write_json(args.output_dir / "stage-failure.json", {"error": f"{type(error).__name__}: {error}",
                "traceback": traceback.format_exc(), "scope": "PARTIAL_FAILED_ANALYSIS",
                "fullPairCompleted": False, "landslideVerified": False, "scientificallyValidated": False})
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
