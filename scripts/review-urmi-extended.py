#!/usr/bin/env python3
"""Saved-only extended rough Urmi MC observer and two actual-state movies.

This binds the NEW extended219MP/h2/PPC1/20s case, preserving the old physical
30MP observer cohort after the engine-coordinate translation. Fixed3s is
not an equilibrium claim. Complete and failed-terminal saved prefixes are
reported honestly; an explicit live prefix may show already finished frames.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

import numpy as np

SCOPE = "ROUGH_NUMERICAL_DEMO_NOT_SCIENTIFIC_VALIDATION"
EXPECTED = {"slope": 40, "height": 10, "crestLength": 24, "baseHeight": 8,
            "domainWidth": 72, "domainHeight": 24, "meshSize": 2, "mpsPerCell": 1,
            "workers": 1, "duration": 20, "frames": 41, "timeStepScale": .2,
            "gravityRampDuration": 2, "gravity": -9.80665, "drainedE": 10773000,
            "drainedNu": .33, "drainedCohesionPa": 3700, "drainedFrictionDeg": 30.6,
            "drainedDilationDeg": 0, "undrainedE": 11745000, "undrainedNu": .45,
            "observerInitialXGreater": 14, "observerInitialYGreater": 10,
            "displayOriginX": 12, "displayOriginY": 8}
SCENARIO = "urmi-damage40-extended"
PARTICLES = 219
COHORT_PARTICLES = 30
MOVIE_FPS = 1
F = [f"F_{i}{j}" for i in range(3) for j in range(3)]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def record(path):
    path = Path(path).resolve()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def now():
    return datetime.now(timezone.utc).isoformat()


def observer_cohort(initial, cfg):
    """Immutable old physical cohort; added foundation/left MPs never join it."""
    return ((initial[:, 0] > cfg["observerInitialXGreater"])
            & (initial[:, 1] > cfg["observerInitialYGreater"]))


def imported(path, name):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def relative(run, text):
    require(isinstance(text, str), "Native output relative path missing")
    part = Path(text)
    require(not part.is_absolute() and ".." not in part.parts, "Absolute/parent native output path refused")
    result = (run / part).resolve()
    require(result.is_relative_to(run), "Native output path escapes run")
    return result


def source_proof(run):
    source = (run / "source").resolve()
    manifest = load(source / "source-manifest.json")
    files = {}
    for row in manifest["files"]:
        path = relative(run, row["path"])
        require(path.is_relative_to(source), "Frozen source escapes source directory")
        key, actual = path.relative_to(source).as_posix(), record(path)
        require(key not in files and actual["sha256"] == row["sha256"] and actual["bytes"] == row["bytes"],
                f"Frozen source hash/size mismatch: {key}")
        files[key] = actual
    require("case.lisp" in files, "Executed case source not in actual source manifest")
    provenance = load(run / "source-provenance.json")
    require(provenance.get("sourceSnapshotExactLoadedBytes") is True
            and provenance.get("copiedByteEqualityBeforeLoad") is True, "Actual frozen runtime source proof missing")
    dll = provenance["nativeBackend"]
    native = source / "libs/kirchoff.dll"
    require(Path(dll["modulePath"]).resolve() == native and dll["verifiedBy"] == "GetModuleHandleW/GetModuleFileNameW"
            and dll["sha256"] == record(native)["sha256"], "Actual mapped frozen DLL mismatch")
    loaded = {Path(row["source"]).resolve() for row in provenance["verifiedAsdfActions"]
              if row.get("firstParty") is True and row.get("operation") == "load-op" and row.get("event") == "performing"}
    for key in ("materials/models/plastic/urmi-strength-damage/law.lisp",
                "materials/models/plastic/urmi-strength-damage/particle.lisp",
                "scenarios/urmi-damage40/transfer.lisp"):
        require(key in files and (source / key).resolve() in loaded, f"Required actual owned source not loaded: {key}")
    return {"status": "PASS", "sourceFilesVerified": len(files), "actualMappedDll": dll,
            "case": files["case.lisp"], "manifest": record(source / "source-manifest.json"),
            "runtimeProvenance": record(run / "source-provenance.json")}


def constants(run):
    import re
    text = (run / "source/materials/models/plastic/mohr-coulomb-evolution/projection.lisp").read_text(encoding="utf-8-sig")
    result = {}
    for name in ("stress-atol", "stress-rtol", "kappa-tol"):
        found = re.search(r"\(defconstant\s+\+" + name + r"\+\s+([\d.eEdD+-]+)\)", text)
        require(found, f"Actual frozen native tolerance missing: {name}")
        result[name] = float(found[1].lower().replace("d", "e"))
    return result


def complete_preparation_frames(path, particles):
    """Count at most two fully written preparation blocks, ignoring a failed tail."""
    if not path.is_file():
        return 0
    completed = 0
    with path.open("rb") as stream:
        header = stream.readline()
        if not header.endswith(b"\n"):
            return 0
        names = next(csv.reader([header.decode("utf-8-sig")]))
        require(len(names) == len(set(names)) and "frame" in names and "particle_id" in names, "Bad preparation CSV header")
        fi, identity = names.index("frame"), names.index("particle_id")
        for frame in range(2):
            for i in range(particles):
                raw = stream.readline()
                if not raw.endswith(b"\n"):
                    return completed
                row = next(csv.reader([raw.decode("utf-8")]))
                if len(row) != len(names) or not all(row):
                    return completed
                values = [float(v.replace("D", "e").replace("d", "e")) for v in row]
                require(np.isfinite(values).all() and values[fi] == frame and values[identity] == i,
                        "Preparation completed prefix data/order invalid")
            completed += 1
    return completed


def copied_inputs(run, output, manifest, copy_helper):
    data = output / "saved-inputs"
    data.mkdir()
    bindings = []
    n, frames = manifest["particleCount"], manifest["savedFrames"]
    preparation = complete_preparation_frames(relative(run, manifest["preparationParticleFile"]), n)
    for key, rows in (("preparationParticleFile", n), ("preparationStateFile", None)):
        if preparation:
            bindings.append(copy_helper.copy_csv_prefix(relative(run, manifest[key]), data / manifest[key], preparation, rows))
    for frame in range(preparation):
        key = "initialVtk" if frame == 0 else "drainedVtk"
        bindings.append(copy_helper.copy_closed(relative(run, manifest[key]), data / manifest[key]))
    for key, rows in (("particleFile", n), ("historyFile", None)):
        if frames:
            bindings.append(copy_helper.copy_csv_prefix(relative(run, manifest[key]), data / manifest[key], frames, rows))
    for frame in range(frames):
        name = manifest["dynamicVtkPattern"] % frame
        bindings.append(copy_helper.copy_closed(relative(run, name), data / name))
    if frames:
        name = manifest["transferLedgerFile"]
        bindings.append(copy_helper.copy_closed(relative(run, name), data / name))
    write(output / "input-copy-binding.json", {"scope": SCOPE, "copiedUtc": now(), "records": bindings,
          "copiedPreparationStates": preparation, "copiedDynamicStates": frames,
          "originalNativeManifestNeverModified": True, "unannouncedOrIncompleteTailNotClaimed": True})
    return data, preparation


def audit_frame(v, h, vtk, baseline, previous, phase, manifest, native, nodes, helper, read_vtk):
    require(set(helper.REQUIRED_COLUMNS) <= v.keys(), "Missing actual particle CSV columns")
    n = manifest["particleCount"]
    require(np.array_equal(v["particle_id"], np.arange(n)) and n == h["particle_count"], "Actual particle IDs/count/order differ")
    require((v["phase_code"] == phase).all(), "Saved material phase differs")
    points, fields = read_vtk(vtk)
    require(points.shape == (n, 3) and helper.close(points[:, 0], v["x_m"]) and helper.close(points[:, 1], v["y_m"])
            and helper.close(points[:, 2], 0), "Actual CSV/VTK positions differ")
    ids = helper.integers(fields["unique-id"], "VTK actual IDs")
    require(len(np.unique(ids)) == n, "Actual VTK IDs duplicate")
    mass, j, v0 = v["mass_kg_per_m"], v["J"], v["reference_volume_m3_per_m"]
    f = np.column_stack([v[k] for k in F]).reshape(n, 3, 3)
    require((mass > 0).all() and (j > 0).all() and (v0 > 0).all()
            and helper.close(np.linalg.det(f), j) and helper.close(v["volume_m3_per_m"], j * v0), "Finite positive F/J/globalV0/mass identity failed")
    initial = np.column_stack([v["initial_x_m"], v["initial_y_m"]])
    if baseline is None:
        require(helper.close(initial, points[:, :2]), "Initial saved points differ from original reference")
        baseline = {"mass": mass.copy(), "v0": v0.copy(), "ids": ids.copy(),
                    "initial": initial.copy()}
    require(np.array_equal(mass, baseline["mass"]) and np.array_equal(v0, baseline["v0"])
            and np.array_equal(ids, baseline["ids"]) and np.array_equal(initial, baseline["initial"]),
            "Saved IDs/mass/originalV0/initial positions changed")
    cohort = observer_cohort(initial, manifest["config"])
    require(int(cohort.sum()) == COHORT_PARTICLES, "Original physical30MP cohort differs")
    require(np.array_equal(v["free_upper_reference_subset"], cohort.astype(float)), "Fixed original physical cohort differs")
    mapping = {"mass": "mass_kg_per_m", "mc-kappa": "mc_kappa", "mc-cohesion-pa": "cohesion_pa",
               "mc-friction-rad": "friction_rad", "mc-dilation-rad": "dilation_rad",
               "mc-plastic-work-j-m3": "plastic_work_pa", "mc-plastic-volume": "plastic_volume",
               "mc-yield-residual-kirchhoff-pa": "yield_residual_kirchhoff_pa",
               "mc-strength-damage": "strength_damage", "mc-damage-active": "damage_active", "mc-kappa-origin": "kappa_origin"}
    for field, key in mapping.items():
        require(field in fields and helper.close(fields[field], v[key]), f"Actual field differs: {field}")
    kappa, work, model, cfg = v["mc_kappa"], v["plastic_work_pa"], manifest["model"], manifest["config"]
    require((kappa >= 0).all() and (work >= 0).all(), "Negative accumulated history/work")
    if previous is not None:
        require((kappa >= previous["mc_kappa"] - native["kappa-tol"]).all()
                and (work >= previous["plastic_work_pa"] - helper.ATOL - helper.RTOL * np.abs(previous["plastic_work_pa"])).all(), "Accumulated history/work decreased")
    if phase < 2:
        c, phi, young, nu = cfg["drainedCohesionPa"], math.radians(cfg["drainedFrictionDeg"]), cfg["drainedE"], cfg["drainedNu"]
        require((v["strength_damage"] == 0).all() and (v["damage_active"] == 0).all(), "Preparation damage must be explicitly inactive")
    else:
        require((v["damage_active"] == 1).all() and (kappa >= v["kappa_origin"] - native["kappa-tol"]).all(), "Active damage/history origin invalid")
        c, phi, young, nu = helper.law_strength(kappa, v["kappa_origin"], nodes), 0, model["youngsModulusPa"], model["poissonRatio"]
        require(helper.close(v["strength_damage"], 1 - v["cohesion_pa"] / model["peakStrengthPa"])
                and (v["strength_damage"] >= 0).all() and (v["strength_damage"] <= model["damageMaximum"] + helper.ATOL).all(), "D_s/law bounds differ")
        if phase == 2:
            baseline["origin"] = v["kappa_origin"].copy()
        else:
            require(np.array_equal(v["kappa_origin"], baseline["origin"]), "Per-particle damage origin changed")
    require(helper.close(v["cohesion_pa"], c) and helper.close(v["friction_rad"], phi)
            and helper.close(v["dilation_rad"], 0) and helper.close(v["E_pa"], young) and helper.close(v["nu"], nu), "Actual phase strength/elasticity law differs")
    tolerance = native["stress-atol"] + native["stress-rtol"] * np.maximum(1, v["native_projection_trial_scale_pa"])
    residual = helper.six_plane_residual(v)
    require((v["native_projection_trial_scale_pa"] >= 0).all()
            and helper.close(tolerance, v["native_yield_tolerance_pa"]) and (residual <= tolerance).all()
            and (np.abs(residual - v["yield_residual_kirchhoff_pa"]) <= tolerance).all(), "Independent actual yield identity failed")
    velocity = np.column_stack([v["vx_m_per_s"], v["vy_m_per_s"]])
    kinetic = float(np.sum(.5 * mass * np.sum(velocity**2, axis=1)))
    require(helper.close(mass.sum(), h["mass_kg_per_m"]) and helper.close(kinetic, h["kinetic_energy_j_per_m"])
            and helper.close(v["time_s"], h["time_s"], time=True)
            and helper.close(v["native_time_s"], h["native_time_s"], time=True), "Saved clock/mass/KE history differs")
    result = {"frame": int(h["frame"]), "timeS": h["time_s"], "nativeTimeS": h["native_time_s"], "phaseCode": phase,
              "particles": n, "massKgPerM": float(mass.sum()), "minJ": float(j.min()),
              "maximumStrengthDamage": float(v["strength_damage"].max()), "minimumCohesionPa": float(v["cohesion_pa"].min()),
              "maximumKappa": float(kappa.max()), "kineticJPerM": kinetic, "vtk": record(vtk),
              "plasticWorkCurrentVolumeProxyJPerM": float(np.sum(v["volume_m3_per_m"] * work)),
              "minimumDomainMarginM": float(v["particle_domain_margin_m"].min()),
              "centerOutsideDomainMassFraction": float(mass[(points[:, 0] < 0) | (points[:, 0] > cfg["domainWidth"])
                  | (points[:, 1] < 0) | (points[:, 1] > cfg["domainHeight"])].sum() / mass.sum()),
              "maximumYieldResidualPa": float(residual.max()), "maximumNativeYieldTolerancePa": float(tolerance.max())}
    return baseline, result, points[:, :2], velocity


def inspect(run, output, manifest, data, prep_count, helper, read_vtk):
    proof, native = source_proof(run), constants(run)
    require(manifest.get("scenario") == SCENARIO and manifest["particleCount"] == PARTICLES,
            "Extended native scenario/219MP contract differs")
    require(manifest.get("approximateDemo") is True and manifest.get("equilibriumVerified") is False,
            "NEW rough-demo/non-equilibrium metadata missing")
    for key, expected in EXPECTED.items():
        require(key in manifest["config"] and helper.close(manifest["config"][key], expected), f"NEW extended case parameter differs: {key}")
    model, cfg = manifest["model"], manifest["config"]
    helper.verify_law_source(run, model)
    nodes, bound = helper.reference_table(model)
    require(helper.close(nodes, model["tableNodes_s_kappa_cPa"]) and helper.close(bound, model["maximumErrorBoundPa"]), "Actual owned reference table differs")
    baseline, previous, prep_audits, drained = None, None, [], None
    if prep_count:
        history = helper.history_rows(data / manifest["preparationStateFile"])
        for frame, v in helper.csv_frames(data / manifest["preparationParticleFile"]):
            baseline, audit, _, _ = audit_frame(v, history[frame], data / manifest["initialVtk" if frame == 0 else "drainedVtk"],
                    baseline, previous, frame, manifest, native, nodes, helper, read_vtk)
            prep_audits.append(audit)
            if frame == 1:
                require(helper.close(audit["nativeTimeS"], 3, time=True), "Actual rough fixed preparation is not3s")
                drained = {key: value.copy() for key, value in v.items()}
            previous = {key: v[key].copy() for key in ("mc_kappa", "plastic_work_pa")}
    states, release, graph, velocities, candidates, transfer = [], None, None, [], [], None
    observer = {"minimumSustainedVxMPerS": .001, "minimumSustainedDurationS": 1}
    if manifest["savedFrames"]:
        require(drained is not None, "Dynamic states lack actual closed fixed-preparation snapshot")
        history = helper.history_rows(data / manifest["historyFile"])
        for frame, v in helper.csv_frames(data / manifest["particleFile"]):
            require(frame == len(states), "Actual dynamic frames not consecutive")
            baseline, audit, pos, velocity = audit_frame(v, history[frame], data / (manifest["dynamicVtkPattern"] % frame),
                    baseline, previous, 2 if frame == 0 else 3, manifest, native, nodes, helper, read_vtk)
            require(helper.close(audit["timeS"], frame * .5, time=True)
                    and helper.close(audit["nativeTimeS"] - manifest["transferNativeTimeS"], audit["timeS"], time=True), "Actual extended saved cadence/native clock reset differs")
            if release is None:
                transfer = helper.transfer_check(data, manifest, drained, v)
                release = pos.copy()
                cohort = observer_cohort(baseline["initial"], cfg)
                require(int(cohort.sum()) == COHORT_PARTICLES, "Original physical30MP cohort differs")
                graph = helper.graph_for(baseline["initial"], cohort, 1.01 * cfg["meshSize"] / cfg["mpsPerCell"])
            mass, displacement = baseline["mass"], pos - release
            downhill = displacement @ np.array([math.cos(math.radians(cfg["slope"])), -math.sin(math.radians(cfg["slope"]))])
            selected = helper.largest_component(cohort & (displacement[:, 0] >= .25) & (downhill >= .5), graph, mass)
            fraction = float(mass[selected].sum() / mass[cohort].sum()) if len(selected) else 0
            velocities.append(velocity[:, 0].copy())
            interval = {"status": "NOT_DETECTED"}
            if len(selected) and fraction >= .1:
                mean_vx = np.asarray([np.average(vx[selected], weights=mass[selected]) for vx in velocities])
                interval = helper.sustained_interval(np.array([s["timeS"] for s in states] + [audit["timeS"]]), mean_vx, observer)
                if interval["status"] == "PASS":
                    candidates.append({"frame": frame, "timeS": audit["timeS"], "logicalIds": selected.tolist(),
                                       "fractionOfUpperCohortMass": fraction, "fixedComponentVelocityInterval": interval})
            # Foundation already extends beyond the toe. It is excluded here:
            # only original upper-cohort MPs initially at/before toe+.5 qualify.
            toe_threshold = cfg["toeX"] + .5
            eligible = cohort & (baseline["initial"][:, 0] <= toe_threshold)
            crossed = eligible & (pos[:, 0] > toe_threshold)
            audit.update(maximumDisplacementFromReleaseM=float(np.linalg.norm(displacement, axis=1).max()),
                         upperCohortCentroidDisplacementM=np.average(displacement[cohort], weights=mass[cohort], axis=0).tolist(),
                         connectedMovingFractionOfUpperCohortMass=fraction,
                         originalUpperCohortNewlyPastToePlusHalfMetreCount=int(crossed.sum()),
                         originalUpperCohortNewlyPastToePlusHalfMetreMassFraction=float(mass[crossed].sum() / mass[cohort].sum()),
                         originalUpperCohortNewlyPastToePlusHalfMetreLogicalIds=np.flatnonzero(crossed).tolist(),
                         originalUpperCohortMaximumToeExcessM=max(0, float(pos[eligible, 0].max() - cfg["toeX"])),
                         fixedComponentVelocityInterval=interval)
            states.append(audit)
            previous = {key: v[key].copy() for key in ("mc_kappa", "plastic_work_pa")}
    require(len(states) == manifest["savedFrames"], "Observed completed savedFrames count differs")
    complete = manifest.get("complete") is True
    if complete:
        require(len(states) == 41 and helper.close(states[-1]["timeS"], 20, time=True), "Native completion lacks actual20s/41states")
    require(prep_audits or states, "No fully written native particle state available")
    return {"schema": "cl-mpm.urmi-extended.saved-review.v1", "createdUtc": now(), "scope": SCOPE,
            "savedIntegrity": "PASS", "nativeStatus": manifest["status"], "nativePhase": manifest["phase"],
            "nativeComplete": complete, "sourceProof": proof, "actualConfig": cfg,
            "particleCount": manifest["particleCount"], "preparationSnapshots": prep_audits, "states": states,
            "actualDynamicSavedFrames": len(states), "actualLastDynamicTimeS": states[-1]["timeS"] if states else 0,
            "preparation": "Fixed3s:2s gravity ramp+1s relaxation; NOT measured equilibrium; no field reset",
            "observer": {"initialXGreaterM": cfg["observerInitialXGreater"],
                         "initialYGreaterM": cfg["observerInitialYGreater"], "particles": COHORT_PARTICLES,
                         "cohort": "Original30MP physical upper cohort; added left/foundation MPs excluded",
                         "runoutDefinition": "Current original-cohort MPs newly past original toe+0.5m; initial-past-threshold MPs excluded; fraction of original upper cohort mass",
                         "runoutScientificValidation": False},
            "transfer": transfer, "qualitativeMotionCandidates": candidates,
            "landslideVerified": False, "scientificallyValidated": False, "manualSpatialReviewRequired": True,
            "limits": ["Coarse h2m/PPC1 rough demonstration; not convergence, calibrated runout, or exact Urmi reproduction",
                       "Fixed preparation is not an equilibrium test; dynamics include material release and preparation transients",
                       "Native finite/J/mass/law checks do not by themselves prove coherent landsliding",
                       "All saved MPs shown including boundary exits/outliers; no particle filtering or displacement amplification",
                       "Only completed saved states; unsaved/partial tail or missing restart state is not invented",
                       "D_s is constitutive strength loss; elastic stiffness unchanged; no fracture opening/pore-pressure solution"]}


def render(report, output, read_vtk, video):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    states = report["states"]
    displayed = states or report["preparationSnapshots"]
    coordinates = [read_vtk(Path(state["vtk"]["path"]))[0] for state in report["preparationSnapshots"] + states]
    all_points = np.concatenate(coordinates)
    cfg = report["actualConfig"]
    origin = np.array([cfg["displayOriginX"], cfg["displayOriginY"]])
    all_points = all_points[:, :2] - origin
    xmin = min(-origin[0], float(all_points[:, 0].min()))
    xmax = max(cfg["domainWidth"] - origin[0], float(all_points[:, 0].max()))
    ymin = min(-origin[1], float(all_points[:, 1].min()))
    ymax = max(cfg["domainHeight"] - origin[1], float(all_points[:, 1].max()))
    margin = max(1, .02 * max(xmax - xmin, ymax - ymin))
    bounds = [xmin - margin, xmax + margin, ymin - margin, ymax + margin]
    directories = {kind: output / f"actual-{kind}-frames" for kind in ("motion", "damage")}
    for directory in directories.values():
        directory.mkdir()
    for index, state in enumerate(displayed):
        points, fields = read_vtk(Path(state["vtk"]["path"]))
        world = points[:, :2] - origin
        for kind, directory in directories.items():
            fig = plt.figure(figsize=(14, 6))
            # Identical axes and common bounds in both movies, including every
            # outlier. The damage colourbar never changes the motion plot size.
            ax = fig.add_axes([.07, .15, .81, .67])
            options = ({"color": "#96704a"} if kind == "motion" else
                       {"c": fields["mc-strength-damage"], "cmap": "inferno", "norm": Normalize(0, 1)})
            dots = ax.scatter(world[:, 0], world[:, 1], s=24, linewidths=0, **options)
            ax.set(xlim=bounds[:2], ylim=bounds[2:], xlabel="world x (m)", ylabel="world y (m)")
            ax.set_aspect("equal", adjustable="box")
            ax.grid(alpha=.15)
            event = {0: "initial drained soil", 1: "fixed 3 s preparation; no equilibrium claim",
                     2: "instantaneous material release", 3: "actual undrained motion"}[state["phaseCode"]]
            status = "COMPLETE 20 s ROUGH DEMO" if report["nativeComplete"] else "PARTIAL ROUGH DEMO"
            channel = "Particle motion" if kind == "motion" else "MC strength damage"
            fig.suptitle(f"{channel} | {status}\n{event}; dynamic t={state['timeS']:.2f} s, native t={state['nativeTimeS']:.5f} s", fontsize=12)
            fig.text(.07, .035, f"All {report['particleCount']} MPs; equal metres; actual saved states; no interpolation or scientific validation", fontsize=10)
            if kind == "damage":
                cax = fig.add_axes([.915, .24, .018, .43])
                fig.colorbar(dots, cax=cax, label="Strength loss D_s = 1 - c / 40.5 kPa")
            fig.savefig(directory / f"frame_{index:04d}.png", dpi=100)
            if index == len(displayed) - 1:
                fig.savefig(output / f"rough-{kind}-result.png", dpi=140)
            plt.close(fig)
    media = {"status": "PASS", "scope": SCOPE, "actualMovieStates": len(displayed),
             "dynamicStates": len(states), "interpolation": False, "coordinateScale": 1, "colourRange": [0, 1],
             "allParticlesShown": True, "plotBoundsWorldM": bounds,
             "displayTranslationM": origin.tolist(), "sameActualStateSequenceAndTimingForBothMovies": True,
             "dynamicSavedTimesS": [state["timeS"] for state in states],
             "motionColour": "#96704a", "strengthDamageColourRangeFixed": [0, 1],
             "summaries": {kind: record(output / f"rough-{kind}-result.png") for kind in directories}, "movies": {}}
    if video:
        executable = shutil.which("ffmpeg")
        if executable is None:
            import imageio_ffmpeg
            executable = imageio_ffmpeg.get_ffmpeg_exe()
        for kind, directory in directories.items():
            destination = output / ("rough-motion.mp4" if kind == "motion" else "rough-strength-damage.mp4")
            command = [executable, "-v", "error", "-y", "-framerate", str(MOVIE_FPS), "-i", str(directory / "frame_%04d.png"),
                       "-frames:v", str(len(displayed)), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                       "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", str(destination)]
            write(output / f"{kind}-video-command.json", command)
            encoded = subprocess.run(command, capture_output=True, text=True)
            (output / f"{kind}-video.stderr.log").write_text(encoded.stderr, encoding="utf-8")
            require(encoded.returncode == 0, f"{kind} video encode failed; saved data preserved")
            decoded = subprocess.run([executable, "-v", "error", "-nostats", "-progress", "pipe:1", "-i", str(destination), "-f", "null", "-"], capture_output=True, text=True)
            (output / f"{kind}-video-decode.stdout.log").write_text(decoded.stdout, encoding="utf-8")
            (output / f"{kind}-video-decode.stderr.log").write_text(decoded.stderr, encoding="utf-8")
            counts = [int(line.split("=", 1)[1]) for line in decoded.stdout.splitlines() if line.startswith("frame=")]
            require(decoded.returncode == 0 and not decoded.stderr.strip() and counts and counts[-1] == len(displayed), f"{kind} full video decode/count failed")
            media["movies"][kind] = {"video": record(destination), "decodedFrames": counts[-1], "fullDecodeExitCode": 0,
                                    "framesPerSecond": MOVIE_FPS, "playbackDurationS": len(displayed) / MOVIE_FPS}
    return media


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--allow-partial", action="store_true", help="Actual failed native manifest only")
    parser.add_argument("--live-prefix", action="store_true", help="Explicitly observe completed saved dynamic frames of a running rough demo")
    parser.add_argument("--video", action="store_true")
    parser.add_argument("--frozen-dir", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    run, output = args.run_dir.resolve(), args.output_dir.resolve()
    if args.frozen_dir is None:
        observed_bytes = (run / "manifest.json").read_bytes()
        observed = json.loads(observed_bytes.decode("utf-8-sig"))
        require(observed.get("scenario") == SCENARIO, "Refusing non-extended native scenario")
        require(type(observed.get("savedFrames")) is int and 0 <= observed["savedFrames"] <= 41
                and type(observed.get("particleCount")) is int and observed["particleCount"] == PARTICLES, "Bad extended native saved/count metadata")
        require((observed.get("status") == "complete" and observed.get("complete") is True)
                or (args.allow_partial and observed.get("status") == "failed" and observed.get("complete") is False)
                or (args.live_prefix and observed.get("status") == "running" and observed["savedFrames"] > 0),
                "Need actual complete/failed terminal state or explicitly requested completed live prefix")
        require(not output.exists(), "Preserve prior rough review; choose a fresh output directory")
        frozen = output / "analysis-source"
        frozen.mkdir(parents=True)
        (output / "observed-native-manifest.json").write_bytes(observed_bytes)
        copied = []
        for path in (Path(__file__), Path(__file__).with_name("plot_m5_cliff_comparison.py"),
                     Path(__file__).with_name("review-urmi-damage40.py"), Path(__file__).with_name("preview-urmi-damage40.py")):
            destination = frozen / path.name
            shutil.copyfile(path, destination)
            require(record(path)["sha256"] == record(destination)["sha256"], "Rough analysis freeze mismatch")
            copied.append({"original": record(path), "copy": record(destination)})
        write(output / "analysis-freeze.json", {"createdUtc": now(), "records": copied,
              "scope": "Copied before review child execution; no pre-native analysis timing claim without separate launch evidence"})
        command = [sys.executable, str(frozen / Path(__file__).name), "--run-dir", str(run), "--output-dir", str(output), "--frozen-dir", str(frozen)]
        if args.video:
            command.append("--video")
        write(output / "command.json", command)
        with (output / "stdout.log").open("w", encoding="utf-8") as stdout, (output / "stderr.log").open("w", encoding="utf-8") as stderr:
            child = subprocess.run(command, stdout=stdout, stderr=stderr)
        write(output / "exit.json", {"exitCode": child.returncode, "finishedUtc": now(), "nativeSolverRerun": False})
        return child.returncode
    stage = "saved-input-copy"
    try:
        helper = imported(args.frozen_dir / "review-urmi-damage40.py", "rough_frozen_helpers")
        copy_helper = imported(args.frozen_dir / "preview-urmi-damage40.py", "rough_frozen_copy_helpers")
        reader = imported(args.frozen_dir / "plot_m5_cliff_comparison.py", "rough_frozen_vtk_reader")
        manifest = load(output / "observed-native-manifest.json")
        data, preparation = copied_inputs(run, output, manifest, copy_helper)
        stage = "quick-saved-state-audit"
        report = inspect(run, output, manifest, data, preparation, helper, reader.read_cliff_vtk)
        report["inputBinding"] = record(output / "input-copy-binding.json")
        report["analysisBinding"] = load(output / "analysis-freeze.json")
        write(output / "integrity.json", report)
        stage = "actual-saved-media"
        report["media"] = render(report, output, reader.read_cliff_vtk, args.video)
        write(output / "review.json", report)
        print(json.dumps({"savedIntegrity": report["savedIntegrity"], "scope": SCOPE, "nativeComplete": report["nativeComplete"],
              "actualStates": report["actualDynamicSavedFrames"], "actualLastDynamicTimeS": report["actualLastDynamicTimeS"],
              "motionCandidates": len(report["qualitativeMotionCandidates"]), "scientificallyValidated": False}))
        return 0 if report["nativeComplete"] else 2
    except Exception as error:
        write(output / "stage-failure.json", {"stage": stage, "error": str(error), "traceback": traceback.format_exc(),
              "nativeSolverRerun": False, "savedInputsPreserved": True, "scope": SCOPE})
        raise


if __name__ == "__main__":
    raise SystemExit(main())
