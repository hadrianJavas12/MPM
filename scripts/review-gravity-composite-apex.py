"""Review saved optional composite-apex gravity states; never run a solver."""
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

VARIANT = "perfect-mc-composite-apex"
PARTICLE_CLASS = "CL-MPM/MODELS/MC-COMPOSITE-APEX:PARTICLE-MC-COMPOSITE-APEX"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "research/references/unnotched-mc-ssr/composite-apex-srf1p6-contract.json"
REQUIRED = ["materials/models/plastic/mc-composite-apex/" + name + ".lisp"
            for name in ("package", "projection", "native")]
REQUIRED += ["materials/adapters/mc-composite-apex.lisp",
             "scenarios/gravity-slope/mc-composite-apex-adapter.lisp"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def require(condition, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_native_sources(run: Path) -> dict:
    """Check retained bytes and actual runtime provenance, not current workspace."""
    manifest = load_json(run / "source/source-manifest.json")
    records = {}
    for row in manifest["files"]:
        relative = Path(row["path"].replace("\\", "/"))
        path = (run / relative).resolve()
        require(path.is_relative_to((run / "source").resolve()), "Source outside frozen tree")
        key = str(relative).replace("\\", "/")
        require(key not in records, "Duplicate frozen source entry")
        require(path.stat().st_size == row["bytes"] and digest(path) == row["sha256"],
                f"Frozen source mismatch: {relative}")
        records[key] = row
    provenance = load_json(run / "source-provenance.json")
    require(provenance.get("sourceSnapshotExactLoadedBytes") is True,
            "Native runtime does not attest exact frozen loading")
    require(provenance.get("copiedByteEqualityBeforeLoad") is True,
            "Native runtime lacks pre-load byte equality")
    loaded = {Path(action["source"]).resolve() for action in provenance["verifiedAsdfActions"]
              if action.get("firstParty") and action.get("operation") == "load-op"
              and action.get("event") == "performing"}
    for relative in REQUIRED:
        require("source/" + relative in records, f"Optional source missing: {relative}")
        require((run / "source" / relative).resolve() in loaded,
                f"Optional source not recorded loaded: {relative}")
    dll = provenance["nativeBackend"]
    expected = run / "source/libs/kirchoff.dll"
    require(Path(dll["modulePath"]).resolve() == expected.resolve(), "Different mapped DLL path")
    require(dll["sha256"] == digest(expected), "Mapped DLL hash mismatch")
    require(dll.get("verifiedBy") == "GetModuleHandleW/GetModuleFileNameW",
            "Actual module mapping was not checked")
    return {"status": "PASS", "frozenSourcesVerified": len(records),
            "optionalLoadedSources": REQUIRED, "nativeBackend": dll,
            "scope": "Retained source hashes and native runtime proof; no post-exit process remapping"}


def verify_variant(base, run: Path, contract: dict, states: list, bounded: bool = False) -> dict:
    import numpy as np
    manifest = load_json(run / "manifest.json")
    config = manifest["config"]
    require(contract.get("materialVariant") == VARIANT, "Wrong variant contract")
    for record in (manifest, config):
        require(record.get("materialVariant") == VARIANT, "Missing or contradictory material variant")
        require(record.get("materialClass") == PARTICLE_CLASS, "Unexpected material class")
        for key in ("apexConvention", "apexCapBandPolicy"):
            require(record.get(key) == contract["variantMetadata"][key],
                    f"Incorrect declared {key}")
    require(all(manifest[key] == config[key] for key in
                ("apexConvention", "apexCapBandPolicy")), "Variant conventions disagree")
    require(config["strengthReductionFactor"] == contract["independentTrials"][0], "Wrong SRF")
    material, geometry, numeric, gravity = (contract[key] for key in
                                         ("referenceMaterial", "geometry", "numerics", "gravity"))
    expected = {
        "E": material["youngsModulusPa"], "nu": material["poissonRatio"],
        "referenceCohesionPa": material["cohesionCauchyPa"],
        "referenceFrictionDeg": material["frictionDeg"],
        "density": material["unitWeightNPerM3"] / abs(gravity["fullAccelerationMPerS2"]),
        "domainWidth": geometry["domainWidthM"], "domainHeight": geometry["domainHeightM"],
        "height": geometry["heightM"], "crestLength": geometry["rearCrestM"],
        "width": geometry["rearCrestM"] + geometry["faceHorizontalM"],
        "baseHeight": geometry["foundationDepthM"], "meshSize": numeric["meshSizeM"],
        "mpsPerCell": numeric["particlesPerAxisPerCell"], "workers": numeric["workers"],
        "timeStepScale": numeric["timeStepScale"], "duration": numeric["durationS"],
        "frames": numeric["frames"], "maxUpdates": numeric["maxUpdates"],
        "damping": numeric["damping"], "gravity": gravity["fullAccelerationMPerS2"],
        "gravityRampDuration": gravity["rampDurationS"],
    }
    import math
    expected["slope"] = math.degrees(math.atan2(geometry["heightM"], geometry["faceHorizontalM"]))
    if bounded:
        expected.update(duration=2e-5, gravityRampDuration=1e-5, frames=3, maxUpdates=2)
    for key, value in expected.items():
        require(base.close(config[key], value), f"Configured {key} differs from declared experiment")
    for key in ("frames", "workers", "mpsPerCell", "maxUpdates"):
        require(type(config[key]) is int and config[key] == expected[key], f"Noninteger or incorrect {key}")
    if bounded:
        require(manifest.get("updates") == 2 and manifest.get("savedFrames") == 3,
                "Bounded fixture is not exactly two updates / three saved states")
    require(manifest["notchCount"] == manifest["driverCount"] == 0
            and manifest["massScale"] == 1 and manifest["damping"] == 0,
            "Unexpected notch, driver, mass scale or damping")
    particles = base.native_csv(run / "particles.csv")
    frames = base.integral(particles["frame"], "particle frames")
    constants, _ = base.stress_constants(run, run / "source")
    frame_results = []
    previous_volume = None
    for state in states:
        frame = state["frame"]
        rows = frames == frame
        values = {name: column[rows] for name, column in particles.items()}
        _, fields = base.read_cliff_vtk(run / "vtk" / f"particles_{frame:04d}.vtk")
        for name in ("mc-apex-active-last", "mc-apex-lambda-last",
                     "mc-plastic-volume", "mc-plastic-work-j-m3"):
            require(name in fields, f"Missing variant VTK field {name}")
            require(np.asarray(fields[name]).shape == values["J"].shape
                    and np.isfinite(fields[name]).all(), f"Invalid variant field {name}")
        active, q = fields["mc-apex-active-last"], fields["mc-apex-lambda-last"]
        require(np.isin(active, [0, 1]).all(), "Nonboolean last-apex flag")
        require((q >= 0).all() and (q[active == 0] == 0).all()
                and (q[active == 1] > 0).all(), "Inconsistent last-apex multiplier")
        require(base.close(fields["mc-plastic-volume"], values["plastic_volume"]),
                "CSV/VTK cumulative plastic volume differs")
        require(base.close(fields["mc-plastic-work-j-m3"], values["plastic_work_pa"]),
                "CSV/VTK cumulative plastic work differs")
        volume = values["plastic_volume"]
        require((volume >= -base.STATE_ATOL).all(), "Negative cumulative plastic volume")
        require(previous_volume is None or (volume >= previous_volume - base.STATE_ATOL).all(),
                "Cumulative plastic volume decreased")
        previous_volume = volume.copy()
        j = values["J"]
        stress = np.zeros((len(j), 3, 3))
        for (i, k), name in zip(((0, 0), (1, 1), (2, 2), (1, 2), (0, 2), (0, 1)), base.STRESS_COLUMNS):
            stress[:, i, k] = values[name] * j
            stress[:, k, i] = values[name] * j
        principal = np.linalg.eigvalsh(stress)
        tol = constants["stress-atol"] + constants["stress-rtol"] * np.maximum(1, np.abs(principal).max(axis=1))
        apex = j * values["cohesion_pa"] / np.tan(values["friction_rad"])
        active_ids = active == 1
        errors = np.abs(principal - apex[:, None]).max(axis=1)
        require((errors[active_ids] <= tol[active_ids]).all(), "Active last-apex stress is not at hydrostatic cap")
        frame_results.append({"frame": frame, "timeS": state["time"],
                              "activeLastReturnCount": int(active_ids.sum()),
                              "maximumLastMultiplier": float(q.max()),
                              "maximumCumulativePlasticVolume": float(volume.max()),
                              "maximumActiveHydrostaticErrorPa": float(errors[active_ids].max()) if active_ids.any() else None})
    return {"status": "PASS", "materialVariant": VARIANT, "boundedControlOnly": bounded,
            "inputSettingsVerified": expected, "frames": frame_results,
            "limitations": "Last q is not a sparse-frame history difference; unsaved trial compliance/full energy balance are not reconstructed"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--video", action="store_true")
    parser.add_argument("--bounded-control", action="store_true",
                        help="Explicit two-update/three-state output fixture; cannot establish full slope completion")
    parser.add_argument("--frozen-analysis-dir", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    run, output = args.run_dir.resolve(), args.output_dir.resolve()
    status = Path(str(run) + "-status.json")
    require(not status.exists() or load_json(status).get("status") not in ("STARTING", "NATIVE_RUNNING"),
            "Refusing analysis during active native execution")
    if args.frozen_analysis_dir is None:
        require(not output.exists(), "Choose a fresh analysis directory")
        source = output / "analysis-source"
        records = []
        try:
            source.mkdir(parents=True)
            for original in (Path(__file__), Path(__file__).with_name("review-gravity-slope.py"),
                             Path(__file__).with_name("plot_m5_cliff_comparison.py"), args.contract.resolve()):
                target = source / original.name
                shutil.copyfile(original, target)
                require(digest(original) == digest(target), "Analysis source copy mismatch")
                records.append({"originalPath": str(original), "path": str(target), "sha256": digest(target)})
            (output / "analysis-source-before.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
            command = [sys.executable, str(source / Path(__file__).name), "--run-dir", str(run),
                       "--contract", str(source / args.contract.name), "--output-dir", str(output),
                       "--frozen-analysis-dir", str(source)]
            if args.video:
                command.append("--video")
            if args.bounded_control:
                command.append("--bounded-control")
            (output / "child-command.json").write_text(json.dumps(command, indent=2) + "\n", encoding="utf-8")
            completed = subprocess.run(command, capture_output=True, text=True)
            (output / "child-stdout.log").write_text(completed.stdout, encoding="utf-8")
            (output / "child-stderr.log").write_text(completed.stderr, encoding="utf-8")
            (output / "child-exit.json").write_text(json.dumps({"exitCode": completed.returncode}) + "\n", encoding="utf-8")
            print(completed.stdout, end="")
            require((output / "review.json").is_file(), "Frozen child did not retain review.json")
            return completed.returncode
        except Exception as error:
            output.mkdir(parents=True, exist_ok=True)
            failure = {"integrityStatus": "ERROR", "stage": "analysis-bootstrap",
                       "error": f"{type(error).__name__}: {error}", "analysisSources": records,
                       "landslideVerified": False, "scientificallyValidated": False}
            (output / "bootstrap-failure.json").write_text(json.dumps(failure, indent=2) + "\n", encoding="utf-8")
            if not (output / "review.json").exists():
                (output / "review.json").write_text(json.dumps(failure, indent=2) + "\n", encoding="utf-8")
            return 1
    source = args.frozen_analysis_dir.resolve()
    report = {"schema": "cl-mpm.gravity-composite-apex.review.v1", "createdUtc": datetime.now(timezone.utc).isoformat(),
              "landslideVerified": False, "scientificallyValidated": False}
    try:
        require(Path(__file__).resolve().parent == source, "Wrapper is not executing from frozen source")
        records = load_json(output / "analysis-source-before.json")
        report["analysisSources"] = records
        for row in records:
            require(Path(row["path"]).resolve().parent == source and digest(Path(row["path"])) == row["sha256"],
                    "Frozen source path/hash mismatch")
        sys.path.insert(0, str(source))
        def load_module(name, filename):
            spec = importlib.util.spec_from_file_location(name, source / filename)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            require(Path(module.__file__).resolve().parent == source, "Imported module is not frozen")
            return module
        load_module("plot_m5_cliff_comparison", "plot_m5_cliff_comparison.py")
        base = load_module("gravity_base_frozen", "review-gravity-slope.py")
        report["executedWrapperPath"] = str(Path(__file__).resolve())
        report["sourceVerification"] = verify_native_sources(run)
        base_report, states, config = base.inspect(run, source / args.contract.name, run / "source")
        report["baseReview"] = base_report
        require(base_report["integrityStatus"] == "PASS", "Shared unchanged native integrity audit failed")
        report["variantReview"] = verify_variant(base, run, load_json(source / args.contract.name), states, args.bounded_control)
        report["integrityStatus"] = "PASS"
        report["nativeComplete"] = base_report["nativeComplete"]
        report["boundedControlOnly"] = args.bounded_control
        report["media"] = []
        try:
            report["media"].append(base.file_record(base.render_static(states, config, output)))
            if args.video:
                report["media"].append(base.render_video(states, config, output))
        except Exception as error:
            report["mediaError"] = f"{type(error).__name__}: {error}"
        report["scope"] = "Explicit added volumetric apex flow; unchanged kinematic observer; human spatial mechanism review and same-factor refinement required before landslide verification"
    except Exception as error:
        report["integrityStatus"] = "ERROR" if "integrityStatus" not in report else report["integrityStatus"]
        report["error"] = f"{type(error).__name__}: {error}"
        (output / "failure-traceback.txt").write_text(traceback.format_exc(), encoding="utf-8")
    try:
        for row in report.get("analysisSources", []):
            require(digest(Path(row["path"])) == row["sha256"], "Frozen analysis source changed")
        report["analysisSourceAfterMatch"] = True
    except Exception as error:
        report["analysisSourceAfterMatch"] = False
        report["sourceAfterError"] = str(error)
    (output / "review.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"integrity": report["integrityStatus"], "nativeComplete": report.get("nativeComplete"),
                      "review": str(output / "review.json"), "error": report.get("error")}))
    return 0 if report["integrityStatus"] == "PASS" and not any(
        key in report for key in ("error", "mediaError", "sourceAfterError")) else 1


if __name__ == "__main__":
    sys.exit(main())
