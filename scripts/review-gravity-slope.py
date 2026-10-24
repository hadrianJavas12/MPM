#!/usr/bin/env python3
"""Independently audit saved native gravity-slope states; never run a solver.

Kinematic thresholds come from the pre-result study contract. A detected motion
candidate still needs inspection of its actual spatial failure mechanism.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import numpy as np

from plot_m5_cliff_comparison import read_cliff_vtk


REPOSITORY = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = REPOSITORY / "research/references/unnotched-mc-ssr/contract.json"
PROJECTION = Path("materials/models/plastic/mohr-coulomb-evolution/projection.lisp")
F_COLUMNS = [f"F_{i}{j}" for i in range(3) for j in range(3)]
STRESS_COLUMNS = [f"sig_{axis}_pa" for axis in ("xx", "yy", "zz", "yz", "xz", "xy")]
# These compare independently serialized double-precision geometry/state, not
# constitutive admissibility. Native stress tolerances are read separately.
STATE_ATOL, STATE_RTOL = 1e-11, 1e-11
TIME_ATOL, TIME_RTOL = 1e-10, 1e-10


def file_record(path: Path) -> dict:
    payload = path.read_bytes()
    return {"path": str(path.resolve()), "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload)}


def native_csv(path: Path) -> dict[str, np.ndarray]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError(f"Missing/duplicate CSV columns: {path}")
        names = reader.fieldnames
        rows = []
        for number, row in enumerate(reader, 2):
            if None in row or any(row.get(key) in (None, "") for key in names):
                raise ValueError(f"Incomplete CSV row {number}: {path}")
            rows.append([float(row[key].replace("D", "e").replace("d", "e")) for key in names])
    values = np.asarray(rows, dtype=float)
    if not rows or not np.isfinite(values).all():
        raise ValueError(f"Empty/nonfinite CSV: {path}")
    return {name: values[:, index] for index, name in enumerate(names)}


def require_columns(data: dict, names: list[str], label: str) -> None:
    missing = set(names) - set(data)
    if missing:
        raise ValueError(f"{label} missing columns: {sorted(missing)}")


def close(a, b, *, atol=STATE_ATOL, rtol=STATE_RTOL) -> bool:
    return bool(np.allclose(a, b, atol=atol, rtol=rtol))


def integral(values: np.ndarray, label: str) -> np.ndarray:
    if not np.equal(values, np.rint(values)).all() or np.any(np.abs(values) > 2**53):
        raise ValueError(f"Nonintegral/inexact {label}")
    return values.astype(np.int64)


def weighted_mean(values: np.ndarray, masses: np.ndarray):
    return np.average(values, axis=0, weights=masses)


def weighted_quantile(values: np.ndarray, masses: np.ndarray, q: float) -> float:
    order = np.argsort(values, kind="stable")
    index = np.searchsorted(np.cumsum(masses[order]), q * masses.sum(), side="left")
    return float(values[order[min(int(index), len(order) - 1)]])


def load_criteria(contract: dict) -> dict:
    """Bind executable thresholds to the exact predeclared textual conventions."""
    declared = contract["detectionConventions"]
    exact = {
        "cohort": "fixed initial particle IDs with x0>2h AND y0>2h; same for both trials",
        "adjacency": "initial-center distance <=1.01h within the fixed cohort",
        "movingNodes": "dx>=0.25h AND downslope projection of actual displacement>=0.5h",
        "sustainedVelocity": "component mass-weighted vx>0.001m/s for all saved states of some 1s interval; IDs remain the same over that interval",
        "runoutGateSeparate": "at least1% initial total mass has center x>initial_toe+0.5h; also report front, median and centroid",
    }
    for key, value in exact.items():
        if declared.get(key) != value:
            raise ValueError(f"Contract {key} changed; review executable criteria explicitly")
    if (declared["minimumLargestConnectedMovingFractionOfCohortMass"] != 0.1
            or declared["minimumPositiveDxMassFractionOfComponent"] != 0.75):
        raise ValueError("Contract component thresholds changed; no silent threshold replacement")
    return {"cohortCutoffH": 2, "adjacencyH": 1.01, "dxH": 0.25,
            "downslopeH": 0.5, "componentMassFraction": 0.1,
            "positiveDxMassFraction": 0.75, "sustainedVxMPerS": 0.001,
            "sustainedDurationS": 1, "toeOffsetH": 0.5, "toeTotalMassFraction": 0.01}


def stress_constants(run: Path, source_root: Path | None = None) -> tuple[dict, list[dict]]:
    root = source_root.resolve() if source_root else run / "source"
    frozen = root / PROJECTION
    if source_root and not frozen.is_file():
        raise ValueError(f"Explicit source root lacks frozen projection: {frozen}")
    source = frozen if frozen.is_file() else REPOSITORY / PROJECTION
    text = source.read_text(encoding="utf-8-sig")
    constants = {}
    for name in ("stress-atol", "stress-rtol"):
        match = re.search(r"\(defconstant\s+\+" + name + r"\+\s+([\d.eEdD+-]+)\)", text)
        if not match:
            raise ValueError(f"Cannot read native {name}: {source}")
        constants[name] = float(match.group(1).lower().replace("d", "e"))
    records = [file_record(source)]
    constants["selectedProjection"] = records[0]
    constants["sourceScope"] = "frozen-directory-execution-not-independently-proven" if frozen.is_file() else "workspace-fallback-not-executed-source-proof"
    source_manifest = root / "source-manifest.json"
    if source_root and not source_manifest.is_file():
        raise ValueError(f"Explicit source root lacks source-manifest.json: {root}")
    if frozen.is_file() and source_manifest.is_file():
        manifest = json.loads(source_manifest.read_text(encoding="utf-8-sig"))
        selected = []
        for entry in manifest["files"]:
            relative = Path(entry["path"].replace("\\", "/"))
            if relative.parts and relative.parts[0] == "source":
                relative = Path(*relative.parts[1:])
            if relative == PROJECTION:
                selected.append(entry)
        if len(selected) != 1:
            raise ValueError("Frozen source manifest must identify the selected projection exactly once")
        expected = selected[0]
        actual = records[0]
        if expected["sha256"].lower() != actual["sha256"] or expected["bytes"] != actual["bytes"]:
            raise ValueError("Selected frozen projection does not match source-manifest SHA256/bytes")
        records.append(file_record(source_manifest))
        constants["sourceScope"] = "frozen-projection-hash-matches-source-manifest; execution-provenance-requires-native-runtime-proof"
        constants["sourceManifestCheck"] = {"status": "PASS", "manifest": records[-1],
                                             "verifiedMember": expected["path"],
                                             "verifiedMemberCount": 1,
                                             "scope": "Selected projection hash/length only; other source members and manifest authenticity not independently certified here"}
    constants["scaleConvention"] = (
        "atol + rtol*max(1,max(abs(current Kirchhoff principal stress))). "
        "Native projection uses trial stress scale, unavailable in saved CSV; "
        "this independent current-state bound is not enlarged to match failures.")
    return constants, records


def check_record(checks: list, name: str, passed: bool, **details) -> None:
    checks.append({"name": name, "status": "PASS" if passed else "FAIL", **details})


def initial_graph(points: np.ndarray, selected: np.ndarray, h: float) -> dict[int, list[int]]:
    ids = np.flatnonzero(selected)
    result = {int(index): [] for index in ids}
    # The benchmark has hundreds of MPs. This avoids a new scipy dependency.
    for index, left in enumerate(ids):
        right = ids[index + 1:]
        near = right[np.linalg.norm(points[right] - points[left], axis=1) <= 1.01 * h]
        for neighbor in near:
            result[int(left)].append(int(neighbor))
            result[int(neighbor)].append(int(left))
    return result


def components(mask: np.ndarray, graph: dict[int, list[int]]) -> list[np.ndarray]:
    remaining = set(int(index) for index in np.flatnonzero(mask))
    found = []
    while remaining:
        seed = min(remaining)
        remaining.remove(seed)
        queue, group = [seed], []
        while queue:
            current = queue.pop()
            group.append(current)
            for neighbor in graph[current]:
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        found.append(np.asarray(sorted(group), dtype=np.int64))
    return found


def sustained_interval(times: np.ndarray, mean_vx: np.ndarray) -> dict:
    if len(times) < 2 or times[-1] - times[0] < 1 - TIME_ATOL:
        return {"status": "NOT_EVALUATED", "reason": "Less than one saved second available"}
    start = None
    for index, positive in enumerate(mean_vx > 0.001):
        if positive:
            if start is None:
                start = index
            if times[index] - times[start] >= 1 - TIME_ATOL:
                return {"status": "PASS", "startTimeS": float(times[start]),
                        "endTimeS": float(times[index]), "savedStates": index - start + 1,
                        "minimumMeanVxMPerS": float(mean_vx[start:index + 1].min())}
        else:
            start = None
    return {"status": "NOT_DETECTED", "reason": "No qualifying saved-state interval >=1s"}


def motion_window(states: list[dict], reference_index: int, graph: dict, cohort: np.ndarray,
                  masses: np.ndarray, h: float, beta: float, label: str) -> dict:
    initial = states[reference_index]["positions"]
    window = states[reference_index:]
    times = np.array([state["time"] for state in window])
    cohort_mass = float(masses[cohort].sum())
    direction = np.array([np.cos(beta), -np.sin(beta)])
    records, candidate = [], None
    for end, state in enumerate(window):
        displacement = state["positions"] - initial
        downslope = displacement @ direction
        moving = cohort & (displacement[:, 0] >= 0.25 * h) & (downslope >= 0.5 * h)
        groups = components(moving, graph)
        largest = max(groups, key=lambda ids: (float(masses[ids].sum()), -int(ids[0]))) if groups else np.array([], dtype=int)
        fraction = float(masses[largest].sum() / cohort_mass) if len(largest) else 0.0
        row = {"frame": state["frame"], "timeS": state["time"],
               "movingMassFraction": float(masses[moving].sum() / cohort_mass),
               "largestConnectedMovingMassFraction": fraction,
               "cohortCentroidDisplacementM": weighted_mean(displacement[cohort], masses[cohort]).tolist(),
               "cohortMedianDxM": weighted_quantile(displacement[cohort, 0], masses[cohort], 0.5),
               "cohortMeanVelocityMPerS": weighted_mean(state["velocity"][cohort], masses[cohort]).tolist()}
        if len(largest):
            row.update({"componentIds": largest.tolist(),
                        "componentMedianDxM": weighted_quantile(displacement[largest, 0], masses[largest], 0.5),
                        "componentMedianDownslopeM": weighted_quantile(downslope[largest], masses[largest], 0.5),
                        "componentPositiveDxMassFraction": float(masses[largest][displacement[largest, 0] > 0].sum() / masses[largest].sum())})
            velocities = np.array([weighted_mean(past["velocity"][largest, 0], masses[largest])
                                   for past in window[:end + 1]])
            interval = sustained_interval(times[:end + 1], velocities)
            row["fixedComponentSustainedVelocity"] = interval
            if (fraction >= 0.1 and row["componentPositiveDxMassFraction"] >= 0.75
                    and interval["status"] == "PASS" and candidate is None):
                candidate = {"detectionFrame": state["frame"], "detectionTimeS": state["time"],
                             "componentIds": largest.tolist(), "componentMassFraction": fraction,
                             "sustainedVelocity": interval}
        records.append(row)
    enough = len(times) >= 2 and times[-1] - times[0] >= 1 - TIME_ATOL
    return {"label": label, "referenceTimeS": float(times[0]), "referenceFrame": window[0]["frame"],
            "status": "PASS" if candidate else ("NOT_DETECTED" if enough else "NOT_EVALUATED"),
            "reason": None if enough else "Less than one saved second; bounded gate cannot assess sustained failure",
            "cohortMassKgPerM": cohort_mass, "candidate": candidate, "states": records,
            "selectionConvention": "Fixed initial cohort/graph; per-state displacement mask; largest component by mass, ties by smallest ID. Candidate IDs are held fixed for every saved velocity in the reported interval. No final-speed selection."}


def inspect(run: Path, contract_path: Path, source_root: Path | None = None) -> tuple[dict, list[dict], dict]:
    contract = json.loads(contract_path.read_text(encoding="utf-8-sig"))
    criteria = load_criteria(contract)
    manifest_path = run / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if manifest.get("scenario") != "gravity-slope":
        raise ValueError("Expected gravity-slope native manifest")
    config = manifest["config"]
    history_path, particles_path = run / "history.csv", run / "particles.csv"
    history, particles = native_csv(history_path), native_csv(particles_path)
    require_columns(history, ["frame", "time_s", "gravity_factor", "gravity_m_per_s2", "particle_count",
                             "mass_kg_per_m", "kinetic_energy_j_per_m", "min_J", "updates"], "history")
    require_columns(particles, ["frame", "time_s", "particle_id", "x_m", "y_m", "vx_m_per_s", "vy_m_per_s",
                               "initial_x_m", "initial_y_m", "free_upper_reference_subset", "mass_kg_per_m",
                               "volume_m3_per_m", "reference_volume_m3_per_m", "J", "mc_kappa", "cohesion_pa",
                               "friction_rad", "dilation_rad", "plastic_volume", "plastic_work_pa",
                               "yield_residual_kirchhoff_pa"] + F_COLUMNS + STRESS_COLUMNS, "particles")
    frames = integral(history["frame"], "history frames")
    if not np.array_equal(frames, np.arange(len(frames))):
        raise ValueError("Saved history frames must start at zero and remain contiguous")
    p_frames = integral(particles["frame"], "particle frames")
    if set(p_frames) != set(frames):
        raise ValueError("Particle/history saved frame sets differ")
    times = history["time_s"]
    if times[0] != 0 or np.any(np.diff(times) <= 0):
        raise ValueError("Saved times must start at zero and strictly increase")
    checks = []
    integral(history["particle_count"], "history particle counts")
    integral(history["updates"], "native update counts")
    constants, source_records = stress_constants(run, source_root)
    input_records = [file_record(path) for path in (manifest_path, history_path, particles_path, contract_path)]
    for path in (run / "effective-config.json",):
        if path.is_file():
            source_records.append(file_record(path))
    h = float(config["meshSize"])
    width, height = float(config["domainWidth"]), float(config["domainHeight"])
    beta = np.deg2rad(float(config["slope"]))
    expected_c = float(config["referenceCohesionPa"]) / float(config["strengthReductionFactor"])
    expected_phi = np.arctan(np.tan(np.deg2rad(float(config["referenceFrictionDeg"]))) / float(config["strengthReductionFactor"]))
    ramp_duration = float(config["gravityRampDuration"])
    r = np.clip(times / ramp_duration, 0, 1)
    factors = r * r * (3 - 2 * r)
    check_record(checks, "saved-gravity-schedule", close(history["gravity_factor"], factors)
                 and close(history["gravity_m_per_s2"], factors * config["gravity"]),
                 scope="Saved step endpoints only; CSV cannot prove every unsaved force evaluation")
    expected_times = config["duration"] * frames / (config["frames"] - 1)
    check_record(checks, "saved-frame-time-grid", close(times, expected_times, atol=TIME_ATOL, rtol=TIME_RTOL))
    check_record(checks, "updates-monotone", bool(history["updates"][0] == 0 and np.all(np.diff(history["updates"]) > 0)))
    complete = manifest.get("complete") is True and manifest.get("status") == "complete"
    check_record(checks, "manifest-terminal-flags", (manifest.get("complete") is True) == (manifest.get("status") == "complete"))
    check_record(checks, "manifest-saved-state-scope", len(frames) == manifest.get("savedFrames")
                 and close(times[-1], manifest.get("lastSavedTimeS", manifest.get("timeS")), atol=TIME_ATOL, rtol=TIME_RTOL))
    check_record(checks, "completion-consistency", (not complete) or
                 (len(frames) == config["frames"] and close(times[-1], config["duration"], atol=TIME_ATOL, rtol=TIME_RTOL)),
                 nativeComplete=complete, savedFrames=len(frames), requestedFrames=config["frames"])
    states, frame_audits, baseline, vtk_identity, previous_kappa = [], [], None, None, None
    total_floor_crossings = total_domain_exits = 0
    for frame in frames:
        indices = np.flatnonzero(p_frames == frame)
        ids = integral(particles["particle_id"][indices], f"frame{frame} captured IDs")
        if not np.array_equal(ids, np.arange(len(ids))):
            raise ValueError(f"Frame {frame}: captured IDs reordered, duplicate or missing")
        values = {name: column[indices] for name, column in particles.items()}
        n = len(ids)
        position = np.column_stack([values["x_m"], values["y_m"]])
        velocity = np.column_stack([values["vx_m_per_s"], values["vy_m_per_s"]])
        p0 = np.column_stack([values["initial_x_m"], values["initial_y_m"]])
        masses = values["mass_kg_per_m"]
        f = np.column_stack([values[name] for name in F_COLUMNS]).reshape(n, 3, 3)
        j = np.linalg.det(f)
        volume_ratio = values["volume_m3_per_m"] / values["reference_volume_m3_per_m"]
        stress = np.zeros((n, 3, 3))
        for (i, k), name in zip(((0, 0), (1, 1), (2, 2), (1, 2), (0, 2), (0, 1)), STRESS_COLUMNS):
            stress[:, i, k] = values[name]
            stress[:, k, i] = values[name]
        principal = np.linalg.eigvalsh(stress * j[:, None, None])
        sine = np.sin(values["friction_rad"])
        offset = 2 * values["cohesion_pa"] * np.cos(values["friction_rad"]) * j
        planes = np.column_stack([(1 + sine) * principal[:, i] - (1 - sine) * principal[:, k] - offset
                                  for i in range(3) for k in range(3) if i != k])
        residual = planes.max(axis=1)
        stress_tolerance = constants["stress-atol"] + constants["stress-rtol"] * np.maximum(1, np.abs(principal).max(axis=1))
        vtk_path = run / "vtk" / f"particles_{frame:04d}.vtk"
        points, fields = read_cliff_vtk(vtk_path)
        input_records.append(file_record(vtk_path))
        unique = integral(fields["unique-id"], "VTK unique IDs")
        if len(np.unique(unique)) != n:
            raise ValueError(f"Frame {frame}: VTK unique IDs duplicate or count changed")
        if baseline is None:
            baseline = {"ids": ids.copy(), "masses": masses.copy(), "positions": p0.copy(),
                        "volumes": values["reference_volume_m3_per_m"].copy()}
            vtk_identity = unique.copy()
        frame_checks = []
        def add(name, passed, **details):
            frame_checks.append({"name": name, "status": "PASS" if passed else "FAIL", **details})
        add("identity-count-mass", np.array_equal(ids, baseline["ids"]) and np.array_equal(unique, vtk_identity)
            and np.array_equal(masses, baseline["masses"]) and np.all(masses > 0)
            and n == int(history["particle_count"][frame]))
        add("reference-state-constant", np.array_equal(p0, baseline["positions"])
            and np.array_equal(values["reference_volume_m3_per_m"], baseline["volumes"]))
        add("CSV-VTK-position-mass", points.shape == (n, 3) and close(points[:, :2], position)
            and close(points[:, 2], 0) and close(fields["mass"], masses))
        add("F-determinant-and-volume-J", bool(np.all(j > 0) and np.all(values["volume_m3_per_m"] > 0)
                                              and np.all(values["reference_volume_m3_per_m"] > 0)
                                              and close(j, values["J"]) and close(j, volume_ratio)),
            maximumDeterminantCsvDifference=float(np.abs(j - values["J"]).max()),
            maximumVolumeRatioDifference=float(np.abs(j - volume_ratio).max()))
        add("perfect-Cauchy-SSR-law", close(values["cohesion_pa"], expected_c)
            and close(values["friction_rad"], expected_phi) and np.all(values["dilation_rad"] == 0))
        add("six-plane-current-state-admissibility", bool(np.all(residual <= stress_tolerance)),
            maximumYieldResidualPa=float(residual.max()), maximumNativeCurrentScaleTolerancePa=float(stress_tolerance.max()),
            violatingParticles=int(np.count_nonzero(residual > stress_tolerance)))
        add("independent-yield-diagnostic", bool(np.all(np.abs(residual - values["yield_residual_kirchhoff_pa"]) <= stress_tolerance)),
            maximumDifferencePa=float(np.abs(residual - values["yield_residual_kirchhoff_pa"]).max()))
        add("nonnegative-history-work", bool(np.all(values["mc_kappa"] >= 0) and np.all(values["plastic_work_pa"] >= 0)))
        add("accumulated-kappa-monotone", previous_kappa is None or bool(np.all(values["mc_kappa"] >= previous_kappa)))
        previous_kappa = values["mc_kappa"].copy()
        cohort = (p0[:, 0] > 2 * h) & (p0[:, 1] > 2 * h)
        add("fixed-upper-cohort", np.array_equal(values["free_upper_reference_subset"], cohort.astype(float)) and np.any(cohort))
        add("saved-time", close(values["time_s"], times[frame], atol=TIME_ATOL, rtol=TIME_RTOL))
        floor = position[:, 1] < 0
        exits = (position[:, 0] < 0) | floor | (position[:, 0] > width) | (position[:, 1] > height)
        total_floor_crossings += int(floor.sum())
        total_domain_exits += int(exits.sum())
        add("center-domain-and-floor", not bool(exits.any()), floorPenetratingCenters=int(floor.sum()),
            centerDomainExits=int(exits.sum()))
        kinetic = float((0.5 * masses * np.square(velocity).sum(axis=1)).sum())
        add("aggregate-history-identities", close(masses.sum(), history["mass_kg_per_m"][frame])
            and close(kinetic, history["kinetic_energy_j_per_m"][frame]) and close(j.min(), history["min_J"][frame]))
        frame_audits.append({"frame": int(frame), "timeS": float(times[frame]), "checks": frame_checks})
        states.append({"frame": int(frame), "time": float(times[frame]), "positions": position,
                       "velocity": velocity, "kappa": values["mc_kappa"], "J": j,
                       "kinetic": kinetic, "masses": masses})
    assert baseline is not None
    p0, masses = baseline["positions"], baseline["masses"]
    check_record(checks, "initial-coordinate-reference", close(states[0]["positions"], p0))
    spacing = h / config["mpsPerCell"]
    expected_initial = np.array([(x, y)
                                for x in np.arange(spacing / 2, config["width"], spacing)
                                for y in np.arange(spacing / 2, config["height"], spacing)
                                if y <= max(0, config["height"] - np.tan(beta) * max(0, x - config["crestLength"]))])
    observed_order = np.lexsort((p0[:, 1], p0[:, 0]))
    check_record(checks, "initial-unnotched-polygon-quadrature",
                 expected_initial.shape == p0.shape and close(p0[observed_order], expected_initial),
                 expectedParticles=len(expected_initial), actualParticles=len(p0),
                 convention="Every configured regular-lattice center under the unnotched continuous slope; no missing/notched/seeded centers")
    check_record(checks, "initial-volume-density", close(baseline["volumes"], spacing**2)
                 and close(masses / baseline["volumes"], config["density"]))
    check_record(checks, "initial-zero-velocity-stress-history", bool(np.all(states[0]["velocity"] == 0)
                 and np.all(states[0]["kappa"] == 0)
                 and all(np.all(particles[name][p_frames == 0] == 0) for name in STRESS_COLUMNS)
                 and all(np.all(particles[name][p_frames == 0] == 0) for name in ("plastic_volume", "plastic_work_pa"))))
    check_record(checks, "initial-identity-F", close(np.column_stack([particles[name][p_frames == 0]
                                                                    for name in F_COLUMNS]).reshape(-1, 3, 3), np.eye(3)))
    check_record(checks, "aggregate-mass-conservation", bool(np.all(np.abs(history["mass_kg_per_m"] / masses.sum() - 1) < 1e-12)))
    cohort = (p0[:, 0] > 2 * h) & (p0[:, 1] > 2 * h)
    graph = initial_graph(p0, cohort, h)
    windows = {"entire": motion_window(states, 0, graph, cohort, masses, h, beta, "entire saved run including gravity ramp")}
    hold = np.flatnonzero(np.isclose(times, 2, atol=TIME_ATOL, rtol=0))
    windows["post2s"] = (motion_window(states, int(hold[0]), graph, cohort, masses, h, beta,
                                      "constant-gravity hold; displacement relative to saved2s") if len(hold)
                          else {"status": "NOT_EVALUATED", "reason": "No actual saved2s state; no interpolation or reference substitution"})
    toe = float(config["toeX"])
    toe_history = []
    for state in states:
        x = state["positions"][:, 0]
        toe_history.append({"frame": state["frame"], "timeS": state["time"],
                            "totalMassFractionPastToePlusHalfH": float(masses[x > toe + 0.5 * h].sum() / masses.sum()),
                            "frontXM": float(x.max()), "medianXM": weighted_quantile(x, masses, 0.5),
                            "centroidXM": float(weighted_mean(x, masses))})
    failures = [row for row in checks if row["status"] == "FAIL"]
    failures.extend({"frame": frame["frame"], **row} for frame in frame_audits for row in frame["checks"] if row["status"] == "FAIL")
    coherent = not failures and any(window["status"] == "PASS" for window in windows.values())
    runout = not failures and total_floor_crossings == 0 and any(row["totalMassFractionPastToePlusHalfH"] >= 0.01 for row in toe_history)
    differences = []
    for key, value in (("duration", contract["numerics"]["durationS"]), ("frames", contract["numerics"]["frames"]),
                       ("gravityRampDuration", contract["gravity"]["rampDurationS"]),
                       ("meshSize", contract["numerics"]["meshSizeM"]), ("mpsPerCell", contract["numerics"]["particlesPerAxisPerCell"]),
                       ("timeStepScale", contract["numerics"]["timeStepScale"])):
        if config[key] != value:
            differences.append({"key": key, "study": value, "actual": config[key]})
    report = {"schema": "cl-mpm.gravity-slope.review.v1", "createdUtc": datetime.now(timezone.utc).isoformat(),
              "runDirectory": str(run.resolve()), "nativeStatus": manifest.get("status"), "nativeComplete": complete,
              "savedScope": "complete" if complete else "partial-saved-states-only", "savedFrames": len(states),
              "lastSavedTimeS": float(times[-1]), "integrityStatus": "PASS" if not failures else "FAIL",
              "scientificallyValidated": False, "landslideDetected": False,
              "coherentMotionDetected": coherent, "runoutGateDetected": runout,
              "manualSpatialReviewRequired": coherent,
              "landslideVerification": "MANUAL_SPATIAL_MECHANISM_REVIEW_REQUIRED" if coherent else "NOT_DETECTED",
              "criteria": criteria, "contract": file_record(contract_path), "studyConfigurationDifferences": differences,
              "nativeStressTolerances": constants, "serializationChecks": {"atol": STATE_ATOL, "rtol": STATE_RTOL},
              "checks": checks, "frameIntegrity": frame_audits, "failures": failures,
              "motionWindows": windows, "toeHistory": toe_history,
              "boundaryReview": {"floorPenetratingCenterSamples": total_floor_crossings,
                                 "domainExitCenterSamples": total_domain_exits,
                                 "minimumParticleDomainMarginM": float(history["min_particle_domain_margin_m"].min()) if "min_particle_domain_margin_m" in history else None,
                                 "runoutContactValidated": False},
              "limitations": ["A motion candidate requires actual scale1 spatial/plastic-shear review; no automatic scientific PASS.",
                              "Fixed grid bottom is not a calibrated Coulomb runout bed; particle-domain overlap/kernel support are not certified by center tests.",
                              "Explicit ramp, FLIP ringing, coarse grid/PPC, locking, timestep, domain and basal effects have not been sensitivity-validated.",
                              "Downslope projection includes settlement; horizontal displacement/coherence are tested separately.",
                              "Native completion, yield colour, maximum speed and toe-front extremum alone do not prove landslide.",
                              "Saved-state velocity persistence does not certify unsaved substep behavior; no closed energy balance is inferred."],
              "inputHashes": input_records, "sourceHashes": source_records, "analysisScript": file_record(Path(__file__)),
              "vtkReaderSource": file_record(Path(__file__).with_name("plot_m5_cliff_comparison.py"))}
    return report, states, config


def draw_geometry(ax, states: list[dict], config: dict, index: int, kind: str, maximum: float):
    initial, state = states[0]["positions"], states[index]
    values = (np.linalg.norm(state["positions"] - initial, axis=1) if kind == "displacement" else state["kappa"])
    ax.scatter(initial[:, 0], initial[:, 1], s=3, c="#c8c8c8", label="initial centers")
    plot = ax.scatter(state["positions"][:, 0], state["positions"][:, 1], c=values, s=8,
                      cmap="viridis", norm=Normalize(0, max(maximum, 1e-15)), label="actual native centers")
    ax.axvline(config["toeX"], color="0.5", lw=0.8, ls="--")
    ax.set(xlim=(0, config["domainWidth"]), ylim=(0, config["domainHeight"]), xlabel="x (m)", ylabel="y (m)")
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(f"t={state['time']:.6g} s; " + ("actual displacement (m)" if kind == "displacement" else "native accumulated plastic history κ"))
    ax.grid(alpha=0.2)
    return plot


def render_static(states: list[dict], config: dict, output: Path) -> Path:
    initial = states[0]["positions"]
    displacement_max = max(float(np.linalg.norm(state["positions"] - initial, axis=1).max()) for state in states)
    kappa_max = max(float(state["kappa"].max()) for state in states)
    fig, axes = plt.subplots(2, 2, figsize=(14, 8), constrained_layout=True)
    for ax, kind, maximum in ((axes[0, 0], "displacement", displacement_max), (axes[0, 1], "kappa", kappa_max)):
        plot = draw_geometry(ax, states, config, -1, kind, maximum)
        fig.colorbar(plot, ax=ax, shrink=0.65)
    h = config["meshSize"]
    cohort = (initial[:, 0] > 2 * h) & (initial[:, 1] > 2 * h)
    masses = states[0]["masses"][cohort]
    times = np.array([state["time"] for state in states])
    centroids = np.array([weighted_mean(state["positions"][cohort] - initial[cohort], masses) for state in states])
    axes[1, 0].plot(times, centroids[:, 0], label="fixed cohort Δx")
    axes[1, 0].plot(times, centroids[:, 1], label="fixed cohort Δy")
    axes[1, 0].set(xlabel="actual time (s)", ylabel="centroid displacement (m)")
    axes[1, 0].legend()
    axes[1, 1].plot(times, [state["kinetic"] for state in states])
    axes[1, 1].set(xlabel="actual time (s)", ylabel="native kinetic energy (J/m)")
    for ax in axes[1]:
        ramp_end = config["gravityRampDuration"]
        if times[0] <= ramp_end <= times[-1]:
            ax.axvline(ramp_end, color="0.5", ls="--", lw=0.8)
        if times[-1] > times[0]:
            ax.set_xlim(float(times[0]), float(times[-1]))
        ax.grid(alpha=0.2)
    fig.suptitle(f"Unnotched gravity/SSR adaptation · SRF={config['strengthReductionFactor']:g} · scale1 coordinates\n"
                 "Fixed bottom; coarse explicit MPM; κ is plastic history, not damage; no scientific validation inferred")
    path = output / "gravity-slope-review.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def render_video(states: list[dict], config: dict, output: Path) -> dict:
    executable = shutil.which("ffmpeg")
    if not executable:
        raise ValueError("ffmpeg unavailable; static/native data remain available")
    directory = output / "actual-frames"
    directory.mkdir(exist_ok=False)
    initial = states[0]["positions"]
    maximum = max(float(np.linalg.norm(state["positions"] - initial, axis=1).max()) for state in states)
    for index, state in enumerate(states):
        fig, ax = plt.subplots(figsize=(12, 4), constrained_layout=True)
        plot = draw_geometry(ax, states, config, index, "displacement", maximum)
        fig.colorbar(plot, ax=ax, shrink=0.6, label="actual displacement (m)")
        fig.suptitle(f"SRF={config['strengthReductionFactor']:g}; actual saved frame {state['frame']}; scale1; no interpolated states")
        fig.savefig(directory / f"actual-{index:04d}.png", dpi=120)
        plt.close(fig)
    path = output / "gravity-slope-actual.mp4"
    command = [executable, "-v", "error", "-y", "-framerate", "4", "-i", str(directory / "actual-%04d.png"),
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(path)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    subprocess.run([executable, "-v", "error", "-i", str(path), "-f", "null", "-"], check=True, capture_output=True, text=True)
    return {**file_record(path), "actualSavedStates": len(states), "playbackFramesPerSecond": 4,
            "physicalLastTimeS": states[-1]["time"], "interpolation": False, "deformationMagnification": 1,
            "fullDecodeExit": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--source-root", type=Path,
                        help="Explicit frozen source directory containing materials/ and source-manifest.json; default RUN/source. Selected projection SHA256/bytes must match its manifest.")
    parser.add_argument("--output-dir", type=Path, help="Default: RUN/review; native files are never altered")
    parser.add_argument("--video", action="store_true", help="Render actual saved states at4fps, without interpolation")
    args = parser.parse_args()
    run = args.run_dir.resolve()
    output = (args.output_dir or run / "review").resolve()
    output.mkdir(parents=True, exist_ok=True)
    destination = output / "review.json"
    if destination.exists():
        parser.error("review.json already exists; choose a fresh --output-dir to preserve prior analysis")
    try:
        report, states, config = inspect(run, args.contract.resolve(), args.source_root)
    except Exception as error:
        report = {"schema": "cl-mpm.gravity-slope.review.v1", "createdUtc": datetime.now(timezone.utc).isoformat(),
                  "runDirectory": str(run), "integrityStatus": "ERROR", "error": f"{type(error).__name__}: {error}",
                  "landslideDetected": False, "scientificallyValidated": False,
                  "analysisScript": file_record(Path(__file__)),
                  "vtkReaderSource": file_record(Path(__file__).with_name("plot_m5_cliff_comparison.py"))}
        states, config = [], None
    if states:
        report["media"] = []
        try:
            report["media"].append(file_record(render_static(states, config, output)))
            if args.video:
                if report["integrityStatus"] != "PASS":
                    report["mediaError"] = "Video refused because native integrity audit failed"
                else:
                    report["media"].append(render_video(states, config, output))
        except Exception as error:
            # Retain the completed independent audit if only rendering fails.
            report["mediaError"] = f"{type(error).__name__}: {error}"
    exit_code = 0 if report["integrityStatus"] == "PASS" and "mediaError" not in report else 1
    destination.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"review": str(destination), "integrity": report["integrityStatus"],
                      "landslideDetected": report["landslideDetected"], "nativeComplete": report.get("nativeComplete")}, indent=2))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
