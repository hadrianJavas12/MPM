"""Compare CSVs from two completed variant audits; never audit, render or run MPM."""
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
VARIANT = "perfect-mc-composite-apex"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_helper(support):
    path = support / "review-gravity-refinement.py"
    spec = importlib.util.spec_from_file_location("_composite_refinement_helpers", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    require(Path(module.__file__).resolve().parent == support, "Helper was not copied")
    return module


def bind_review(run, report, expected_contract_sha):
    """Bind current CSV bytes to the existing complete, unbounded variant audit."""
    run = run.resolve()
    require(report.get("integrityStatus") == "PASS" and report.get("nativeComplete") is True,
            "Prior variant review is not complete/PASS")
    require(report.get("boundedControlOnly") is False and report.get("analysisSourceAfterMatch") is True,
            "Prior review is bounded or lacks unchanged analysis proof")
    require(not any(key in report for key in ("error", "sourceAfterError", "mediaError")),
            "Prior review retains an unresolved stage error")
    require(report.get("sourceVerification", {}).get("status") == "PASS", "Native source proof did not pass")
    require(Path(report["nativeEvidenceRoot"]).resolve() == run, "Prior native evidence belongs to another run")
    variant = report["variantReview"]
    require(variant.get("status") == "PASS" and variant.get("materialVariant") == VARIANT
            and variant.get("boundedControlOnly") is False, "Wrong or bounded material variant audit")
    base = report["baseReview"]
    require(base.get("integrityStatus") == "PASS" and base.get("nativeComplete") is True
            and Path(base["runDirectory"]).resolve() == run, "Base audit belongs to another/incomplete run")
    contract = base["contract"]
    require(contract["sha256"] == expected_contract_sha
            and hashlib.sha256(Path(contract["path"]).read_bytes()).hexdigest() == expected_contract_sha,
            "Prior audit contract hash differs")
    for filename in ("manifest.json", "history.csv", "particles.csv"):
        path = run / filename
        records = [row for row in base["inputHashes"] if Path(row["path"]).resolve() == path]
        require(len(records) == 1 and records[0]["bytes"] == path.stat().st_size
                and records[0]["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest(),
                f"Saved input changed since prior audit: {filename}")
    require(read_json(run / "manifest.json").get("complete") is True, "Native manifest is incomplete")
    return base


def check_pair_configs(coarse, fine, contract):
    require(set(coarse) == set(fine), "Configuration key sets differ")
    changes = [{"key": key, "coarse": coarse[key], "fine": fine[key]}
               for key in sorted(coarse) if coarse[key] != fine[key]]
    require(contract["onlyAssignedDifference"] == {"meshSizeM": [1, 0.5]}
            and changes == [{"key": "meshSize", "coarse": 1.0, "fine": 0.5}],
            "Inputs differ beyond registered refinement")
    require(coarse.get("materialVariant") == VARIANT and coarse.get("strengthReductionFactor") == 1.6,
            "Wrong registered material variant/SRF")
    return changes


def apex_summary(report, states, native):
    """Copy already audited last-return observations; never infer q from volume deltas."""
    frames = report["variantReview"]["frames"]
    require(len(frames) == len(states), "Prior apex frame summary differs")
    for row, state in zip(frames, states):
        require(row["frame"] == state["frame"] and np.isclose(row["timeS"], state["time"],
                atol=native.TIME_ATOL, rtol=native.TIME_RTOL), "Apex summary frame/time differs")
    return {"source": "Existing frozen variantReview.frames; no VTK reread or q reconstruction",
            "frames": frames, "lastMultiplierIsNotCumulativeVolumeDifference": True,
            "plasticWorkAggregate": "NOT_EVALUATED_BY_THIS_CSV_COMPARISON"}


def distribution_differences(coarse, fine):
    rows = []
    for left, right in zip(coarse, fine):
        rows.append({"frame": left["frame"], "coarseTimeS": left["timeS"], "fineTimeS": right["timeS"],
            "fineMinusCoarseKineticEnergyJPerM": right["kineticEnergyJPerM"] - left["kineticEnergyJPerM"],
            "fineMinusCoarseCohortCentroidDisplacementM": (np.asarray(right["cohortCentroidDisplacementM"])
                                                         - left["cohortCentroidDisplacementM"]).tolist(),
            "fineMinusCoarseCohortMeanVelocityMPerS": (np.asarray(right["cohortMeanVelocityMPerS"])
                                                      - left["cohortMeanVelocityMPerS"]).tolist(),
            "fineMinusCoarseQuantiles": {name: {q: right["massWeightedQuantiles"][name][q] - value
                  for q, value in quantiles.items()} for name, quantiles in left["massWeightedQuantiles"].items()}})
    return rows


def run_frozen(args):
    output, support = args.output_dir.resolve(), Path(__file__).resolve().parent
    require(support == output / "analysis-support", "Execute the frozen comparison copy")
    before = read_json(output / "support-pre-execution.json")["copies"]
    for record in before:
        path = Path(record["path"])
        require(path.resolve().parent == support and path.stat().st_size == record["bytes"]
                and hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"],
                "Frozen comparison support changed")
    helper = load_helper(support)
    native = helper.load_review_module(support)
    contract = read_json(args.contract)
    observer = helper.validate_observer(contract)
    runs = {"coarse_h1": args.coarse_run_dir.resolve(), "fine_h05": args.fine_run_dir.resolve()}
    trials, reports, bindings = {}, {}, {}
    for role, audit_key in (("coarse_h1", "coarseAudit"), ("fine_h05", "fineAudit")):
        run = runs[role]
        status = Path(str(run) + "-status.json")
        require(not status.is_file() or read_json(status).get("status") not in ("STARTING", "NATIVE_RUNNING"),
                "Comparison must wait for native completion")
        report_path = support / (role + "-prior-review.json")
        report = read_json(report_path)
        base = bind_review(run, report, contract[audit_key]["sha256"])
        base_path = output / (role + "-bound-base-review.json")
        helper.write_json(base_path, base)
        states, config, _ = helper.load_coarse_for_comparison(native, run, base_path, contract[audit_key]["sha256"])
        require(len(states) == 61, "Registered complete pair requires 61 actual saved states")
        trials[role] = {"states": states, "config": config}
        reports[role] = report
        bindings[role] = {"frozenPriorReview": helper.file_record(report_path),
            "priorAuditContract": base["contract"], "boundBaseReview": helper.file_record(base_path),
            "inputs": [helper.file_record(run / name) for name in ("manifest.json", "history.csv", "particles.csv")]}
    changes = check_pair_configs(trials["coarse_h1"]["config"], trials["fine_h05"]["config"], contract)
    require(contract["expectedParticleCount"] == [880, 3520], "Registered counts changed")
    for role, count in zip(trials, contract["expectedParticleCount"]):
        require(len(trials[role]["states"][0]["masses"]) == count, "Wrong actual particle count")
    trials["coarse_h1"]["states"], time_delta = helper.matched_saved_states(native,
        trials["coarse_h1"]["states"], trials["fine_h05"]["states"])
    comparisons, distributions = {}, {}
    beta = np.deg2rad(trials["fine_h05"]["config"]["slope"])
    for role, trial in trials.items():
        trial["initial"] = trial["states"][0]["positions"].copy()
        trial["masses"] = trial["states"][0]["masses"].copy()
        motion = helper.common_physical_windows(native, trial["states"], trial["initial"], trial["masses"], beta, observer)
        runout = helper.physical_runout(trial["states"], trial["masses"], observer)
        comparisons[role] = {"motion": motion, "runout": runout,
            "coherentMotionCandidate": any(row["status"] == "PASS" for row in motion["windows"].values()),
            "separateRunoutCandidate": any(row["massFractionPastPhysicalToe"] >= observer["runoutMinimumFractionOfInitialTotalMass"] for row in runout),
            "priorApexObservations": apex_summary(reports[role], trial["states"], native),
            "nativeHScaledDiagnosticsSeparate": reports[role]["baseReview"]["motionWindows"]}
        distributions[role] = helper.physical_distributions(native, trial["states"], trial["initial"], trial["masses"], beta, observer)
    bins = output / "common-initial-1m-spatial-bins.csv"
    helper.write_spatial_bins(bins, trials)
    for role, run in runs.items():
        require(bindings[role]["inputs"] == [helper.file_record(run / name) for name in ("manifest.json", "history.csv", "particles.csv")],
                "Saved inputs changed during comparison")
    result = {"schema": "cl-mpm.composite-refinement.csv-comparison.v1", "status": "PASS_CSV_COMPARISON",
        "contract": helper.file_record(args.contract), "observer": observer, "inputChanges": changes,
        "priorAuditBindings": bindings, "maximumMatchedSavedTimeDifferenceS": time_delta,
        "interpolation": False, "particleIdsTransferableAcrossMeshes": False,
        "trials": comparisons, "massWeightedDistributions": distributions,
        "fineMinusCoarseDistributions": distribution_differences(distributions["coarse_h1"], distributions["fine_h05"]),
        "outputs": [helper.file_record(bins)], "landslideVerified": False, "scientificallyValidated": False,
        "scope": "CSV comparison after two existing full variant audits; zero VTK rereads, audits, render or native calls",
        "limits": contract["limits"], "stopRule": contract["stopRule"]}
    helper.write_json(output / "common-physical-review.json", result)
    print(json.dumps({"status": result["status"], "motion": {role: {name: row["status"] for name, row in
        value["motion"]["windows"].items()} for role, value in comparisons.items()}, "landslideVerified": False}))
    return 0


def freeze_and_run(args):
    output = args.output_dir.resolve()
    require(not output.exists(), "Use a fresh comparison directory")
    support = output / "analysis-support"
    support.mkdir(parents=True)
    helper = load_helper(Path(__file__).resolve().parent)
    sources = [(Path(__file__).with_name(name), name) for name in (Path(__file__).name,
        "review-gravity-refinement.py", "review-gravity-slope.py", "plot_m5_cliff_comparison.py")]
    sources += [(args.contract, "comparison-contract.json"), (args.coarse_review, "coarse_h1-prior-review.json"),
                (args.fine_review, "fine_h05-prior-review.json")]
    copies = []
    for source, name in sources:
        target = support / name
        shutil.copyfile(source, target)
        require(helper.file_record(source)["sha256"] == helper.file_record(target)["sha256"], "Support copy mismatch")
        copies.append({**helper.file_record(target), "originalPath": str(source.resolve())})
    helper.write_json(output / "support-pre-execution.json", {"preparedUtc": datetime.now(timezone.utc).isoformat(), "copies": copies})
    command = [sys.executable, str(support / Path(__file__).name), "--execute-frozen",
        "--coarse-run-dir", str(args.coarse_run_dir.resolve()), "--fine-run-dir", str(args.fine_run_dir.resolve()),
        "--contract", str(support / "comparison-contract.json"), "--output-dir", str(output)]
    helper.write_json(output / "command.json", {"command": command})
    with (output / "comparison.log").open("w", encoding="utf-8") as log:
        completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=False)
    helper.write_json(output / "comparison-exit.json", {"exitCode": completed.returncode,
        "finishedUtc": datetime.now(timezone.utc).isoformat(), "nativeCalls": 0, "vtkAudits": 0, "renders": 0})
    after = [helper.file_record(Path(row["path"])) for row in copies]
    unchanged = all(before["sha256"] == final["sha256"] for before, final in zip(copies, after))
    helper.write_json(output / "support-after-execution.json", {"copies": after,
        "unchanged": unchanged})
    require(unchanged, "Comparison support changed during execution; retain prior output as failed provenance")
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
    try:
        return run_frozen(args) if args.execute_frozen else freeze_and_run(args)
    except Exception as error:
        if args.output_dir.is_dir() and not (args.output_dir / "stage-failure.json").exists():
            (args.output_dir / "stage-failure.json").write_text(json.dumps({"error": f"{type(error).__name__}: {error}",
                "traceback": traceback.format_exc(), "landslideVerified": False, "scientificallyValidated": False}, indent=2), encoding="utf-8")
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
