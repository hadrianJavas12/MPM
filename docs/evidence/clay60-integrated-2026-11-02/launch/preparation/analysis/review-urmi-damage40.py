#!/usr/bin/env python3
"""Audit saved Urmi-inspired MC strength-damage states, without running MPM.

CSV is consumed one frame at a time. Only one frame of all state variables,
fixed references, and one scalar velocity per particle per dynamic frame are
retained. Source, mapped DLL, CSV, VTK and material identities fail closed.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import traceback

import numpy as np

ATOL = RTOL = 1e-11
TIME_ATOL = TIME_RTOL = 1e-10
ROOT = Path(__file__).resolve().parents[1]
PROJECTION = "materials/models/plastic/mohr-coulomb-evolution/projection.lisp"
LAW = "materials/models/plastic/urmi-strength-damage/law.lisp"
REQUIRED_LOADED = [LAW, "materials/models/plastic/urmi-strength-damage/particle.lisp",
                   "scenarios/urmi-damage40/transfer.lisp", "scenarios/urmi-damage40/output.lisp",
                   "scenarios/urmi-damage40/runner.lisp"]
F_COLUMNS = [f"F_{i}{j}" for i in range(3) for j in range(3)]
STRESS_COLUMNS = [f"sig_{a}_pa" for a in ("xx", "yy", "zz", "yz", "xz", "xy")]
REQUIRED_COLUMNS = ["frame", "time_s", "native_time_s", "particle_id", "phase_code",
                    "x_m", "y_m", "vx_m_per_s", "vy_m_per_s", "initial_x_m", "initial_y_m",
                    "mass_kg_per_m", "volume_m3_per_m", "reference_volume_m3_per_m", "J",
                    "mc_kappa", "cohesion_pa", "friction_rad", "dilation_rad", "plastic_work_pa",
                    "plastic_volume", "yield_residual_kirchhoff_pa", "native_yield_tolerance_pa",
                    "native_projection_trial_scale_pa", "E_pa", "nu", "damage_active",
                    "strength_damage", "kappa_origin", "free_upper_reference_subset",
                    "particle_domain_margin_m"] + F_COLUMNS + STRESS_COLUMNS


def require(condition, message):
    if not condition:
        raise ValueError(message)


def close(a, b, *, time=False):
    return bool(np.allclose(a, b, atol=TIME_ATOL if time else ATOL,
                            rtol=TIME_RTOL if time else RTOL))


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def record(path):
    path = Path(path).resolve()
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": hasher.hexdigest()}


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def integers(values, label):
    require(np.isfinite(values).all() and np.equal(values, np.rint(values)).all()
            and (np.abs(values) <= 2**53).all(), f"Invalid integer {label}")
    return values.astype(np.int64)


def csv_frames(path):
    """Yield consecutive frame blocks; reject malformed/nonfinite or reordered data."""
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        names = reader.fieldnames
        require(names and len(names) == len(set(names)) and "frame" in names,
                f"Missing/duplicate CSV header: {path}")
        frame, rows = None, []
        frame_index = names.index("frame")
        for line, row in enumerate(reader, 2):
            require(None not in row and all(row.get(k) not in (None, "") for k in names),
                    f"Incomplete CSV line {line}: {path}")
            values = [float(row[k].replace("D", "e").replace("d", "e")) for k in names]
            require(np.isfinite(values).all(), f"Nonfinite CSV line {line}: {path}")
            current = values[frame_index]
            require(current == round(current), "Nonintegral CSV frame")
            current = int(current)
            if frame is not None and current != frame:
                require(current > frame, "CSV frame order is not strictly increasing")
                matrix = np.asarray(rows, dtype=float)
                yield frame, {key: matrix[:, i] for i, key in enumerate(names)}
                rows = []
            frame = current
            rows.append(values)
        if rows:
            matrix = np.asarray(rows, dtype=float)
            yield frame, {key: matrix[:, i] for i, key in enumerate(names)}


def history_rows(path):
    """Small frame history, still validated with the same streaming parser."""
    result = {}
    for frame, values in csv_frames(path):
        require(len(values["frame"]) == 1, "Duplicate frame in history")
        result[frame] = {key: float(value[0]) for key, value in values.items()}
    return result


def verified_sources(run):
    manifest_path = run / "source/source-manifest.json"
    manifest = load_json(manifest_path)
    frozen = (run / "source").resolve()
    sources = {}
    for row in manifest["files"]:
        relative = Path(row["path"].replace("\\", "/"))
        path = (run / relative).resolve()
        require(path.is_relative_to(frozen), "Frozen source escapes source directory")
        key = path.relative_to(frozen).as_posix()
        require(key not in sources, "Duplicate frozen source")
        actual = record(path)
        require(actual["bytes"] == row["bytes"] and actual["sha256"] == row["sha256"],
                f"Frozen source bytes/hash differ: {key}")
        sources[key] = actual
    provenance = load_json(run / "source-provenance.json")
    require(provenance.get("sourceSnapshotExactLoadedBytes") is True
            and provenance.get("copiedByteEqualityBeforeLoad") is True,
            "Missing exact-loaded-source runtime proof")
    loaded = {Path(r["source"]).resolve() for r in provenance["verifiedAsdfActions"]
              if r.get("firstParty") and r.get("operation") == "load-op" and r.get("event") == "performing"}
    for name in REQUIRED_LOADED:
        require(name in sources and (frozen / name).resolve() in loaded,
                f"Required owned source not recorded loaded: {name}")
    dll = provenance["nativeBackend"]
    expected = frozen / "libs/kirchoff.dll"
    require(Path(dll["modulePath"]).resolve() == expected.resolve()
            and dll["sha256"] == record(expected)["sha256"]
            and dll.get("verifiedBy") == "GetModuleHandleW/GetModuleFileNameW",
            "Actual mapped frozen DLL proof differs")
    constants = {}
    text = (frozen / PROJECTION).read_text(encoding="utf-8-sig")
    for name in ("stress-atol", "stress-rtol", "kappa-tol"):
        found = re.search(r"\(defconstant\s+\+" + name + r"\+\s+([\d.eEdD+-]+)\)", text)
        require(found, f"Frozen native constant missing: {name}")
        constants[name] = float(found.group(1).lower().replace("d", "e"))
    return {"status": "PASS", "frozenSourcesVerified": len(sources), "nativeBackend": dll,
            "sourceManifest": record(manifest_path), "provenance": record(run / "source-provenance.json"),
            "lawSource": sources[LAW], "projectionSource": sources[PROJECTION], "constants": constants}


def verify_law_source(run, material):
    """The independent table must describe the exact owned constants actually loaded."""
    source = (run / "source" / LAW).read_text(encoding="utf-8-sig")
    names = {"peak-strength-pa": "peakStrengthPa", "transition-strength-pa": "transitionStrengthPa",
             "remolded-strength-pa": "remoldedStrengthPa", "shear-modulus-pa": "shearModulusPa",
             "youngs-modulus-pa": "youngsModulusPa", "poisson-ratio": "poissonRatio",
             "gamma-peak": "gammaPeak", "gamma-transition": "gammaTransition", "gamma-remolded": "gammaRemolded",
             "beta": "beta", "table-tolerance-pa": "tableTolerancePa", "maximum-segments": "maximumSegments"}
    for lisp_name, key in names.items():
        found = re.search(r"\(defconstant\s+\+" + lisp_name + r"\+\s+([\d.eEdD+-]+)\)", source)
        require(found and float(found.group(1).lower().replace("d", "e")) == material[key],
                f"Frozen executed material constant differs: {lisp_name}")


def reference_table(material):
    """Independent deterministic transcription of the frozen declared law algorithm."""
    peak, transition, remolded = (material[k] for k in
                                  ("peakStrengthPa", "transitionStrengthPa", "remoldedStrengthPa"))
    g, beta = material["shearModulusPa"], material["beta"]
    sr = material["gammaTransition"] - material["gammaPeak"]
    end = material["gammaRemolded"] - material["gammaPeak"]
    scale = (peak - transition) / (1 - math.exp(-beta * sr))

    def node(s):
        if s == 0:
            c = peak
        elif s >= end:
            c = remolded
        elif s >= sr:
            c = transition - (transition - remolded) * (s - sr) / (end - sr)
        else:
            c = transition + scale * (math.exp(-beta * s) - math.exp(-beta * sr))
        return [s, (s + (peak - c) / g) / math.sqrt(3), c]

    def interval(left, right):
        alo, ahi = scale * math.exp(-beta * right), scale * math.exp(-beta * left)
        def curvature(a):
            return 3 * beta * beta * a / (1 + beta * a / g)**3
        critical = g / (2 * beta)
        bound = max(curvature(alo), curvature(ahi), curvature(critical) if alo <= critical <= ahi else 0)
        return [left, right, bound * (node(right)[1] - node(left)[1])**2 / 8 + material["roundingAllowancePa"]]

    intervals = [interval(0, sr)]
    while max(i[2] for i in intervals) > material["tableTolerancePa"]:
        require(len(intervals) + 1 < material["maximumSegments"], "Declared table segment budget exceeded")
        # Common Lisp REDUCE chooses the earlier interval on equal error.
        index = max(range(len(intervals)), key=lambda i: intervals[i][2])
        left, right, _ = intervals[index]
        mid = 0.5 * (left + right)
        intervals[index:index + 1] = [interval(left, mid), interval(mid, right)]
    nodes = np.array([node(0)] + [node(i[1]) for i in intervals] + [node(end)])
    require(len(nodes) - 1 == material["actualSegments"], "Independent table segment count differs")
    return nodes, max(i[2] for i in intervals)


def law_strength(kappa, origin, nodes):
    return np.interp(kappa - origin, nodes[:, 1], nodes[:, 2], left=nodes[0, 2], right=nodes[-1, 2])


def graph_for(positions, cohort, radius):
    """Spatial buckets avoid quadratic adjacency construction for thousands of MPs."""
    graph, buckets = {}, {}
    for i in np.flatnonzero(cohort):
        key = tuple(np.floor(positions[i] / radius).astype(int))
        buckets.setdefault(key, []).append(int(i))
        graph[int(i)] = []
    for i in graph:
        key = np.floor(positions[i] / radius).astype(int)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for j in buckets.get((int(key[0] + dx), int(key[1] + dy)), []):
                    if j > i and np.linalg.norm(positions[i] - positions[j]) <= radius:
                        graph[i].append(j)
                        graph[j].append(i)
    return graph


def largest_component(mask, graph, masses):
    remaining, best = set(map(int, np.flatnonzero(mask))), []
    while remaining:
        seed = min(remaining)
        remaining.remove(seed)
        group, queue = [], [seed]
        while queue:
            i = queue.pop()
            group.append(i)
            for j in graph[i]:
                if j in remaining:
                    remaining.remove(j)
                    queue.append(j)
        if not best or (masses[group].sum(), -min(group)) > (masses[best].sum(), -min(best)):
            best = group
    return np.asarray(sorted(best), dtype=np.int64)


def sustained_interval(times, mean_vx, observer):
    start = None
    for i, positive in enumerate(mean_vx > observer["minimumSustainedVxMPerS"]):
        start = (i if start is None else start) if positive else None
        if start is not None and times[i] - times[start] >= observer["minimumSustainedDurationS"] - TIME_ATOL:
            return {"status": "PASS", "startTimeS": float(times[start]), "endTimeS": float(times[i]),
                    "savedStates": i - start + 1, "minimumMeanVxMPerS": float(mean_vx[start:i + 1].min())}
    return {"status": "NOT_DETECTED" if len(times) > 1 and times[-1] - times[0] >= 1 - TIME_ATOL else "NOT_EVALUATED"}


def six_plane_residual(values):
    j = values["J"]
    stress = np.zeros((len(j), 3, 3))
    for (i, k), name in zip(((0, 0), (1, 1), (2, 2), (1, 2), (0, 2), (0, 1)), STRESS_COLUMNS):
        stress[:, i, k] = stress[:, k, i] = values[name] * j
    principal = np.linalg.eigvalsh(stress)
    sine = np.sin(values["friction_rad"])
    offset = 2 * j * values["cohesion_pa"] * np.cos(values["friction_rad"])
    return np.max(np.column_stack([(1 + sine) * principal[:, i] - (1 - sine) * principal[:, k] - offset
                                  for i in range(3) for k in range(3) if i != k]), axis=1)


def audit_frame(values, history, vtk_path, read_vtk, baseline, previous, phase, contract, constants, nodes):
    require(set(REQUIRED_COLUMNS) <= values.keys(), f"Missing particle columns: {set(REQUIRED_COLUMNS) - values.keys()}")
    ids = integers(values["particle_id"], "logical IDs")
    n = len(ids)
    require(np.array_equal(ids, np.arange(n)), "Logical IDs not exactly ordered 0..N-1")
    require(n == int(history["particle_count"]), "Particle count differs from history")
    require(np.all(values["phase_code"] == phase), "Unexpected material phase code")
    pos = np.column_stack([values["x_m"], values["y_m"]])
    initial = np.column_stack([values["initial_x_m"], values["initial_y_m"]])
    velocity = np.column_stack([values["vx_m_per_s"], values["vy_m_per_s"]])
    mass, j, v0 = values["mass_kg_per_m"], values["J"], values["reference_volume_m3_per_m"]
    f = np.column_stack([values[k] for k in F_COLUMNS]).reshape(n, 3, 3)
    require((mass > 0).all() and (j > 0).all() and (v0 > 0).all(), "Nonpositive mass/J/reference V0")
    require(close(np.linalg.det(f), j) and close(values["volume_m3_per_m"], j * v0), "F9/J/global V=J*V0 mismatch")
    points, fields = read_vtk(vtk_path)
    require(points.shape == (n, 3) and close(points[:, :2], pos) and close(points[:, 2], 0), "CSV/VTK coordinates differ")
    unique = integers(fields["unique-id"], "native VTK IDs")
    require(len(np.unique(unique)) == n, "VTK native IDs duplicate")
    if baseline is None:
        baseline = {"mass": mass.copy(), "initial": initial.copy(), "v0": v0.copy(),
                    "vtk_ids": unique.copy(), "initial_kappa": values["mc_kappa"].copy()}
        require(close(initial, pos), "Initial saved geometry differs from original reference")
    require(np.array_equal(mass, baseline["mass"]) and np.array_equal(initial, baseline["initial"])
            and np.array_equal(v0, baseline["v0"]), "Logical reference/mass/V0 changed")
    require(np.array_equal(unique, baseline["vtk_ids"]), "Preserved native unique IDs changed, including declared clone transfer")
    field_map = {"mass": "mass_kg_per_m", "mc-kappa": "mc_kappa", "mc-cohesion-pa": "cohesion_pa",
                 "mc-friction-rad": "friction_rad", "mc-dilation-rad": "dilation_rad",
                 "mc-plastic-volume": "plastic_volume", "mc-plastic-work-j-m3": "plastic_work_pa",
                 "mc-yield-residual-kirchhoff-pa": "yield_residual_kirchhoff_pa",
                 "mc-strength-damage": "strength_damage", "mc-damage-active": "damage_active",
                 "mc-kappa-origin": "kappa_origin"}
    for vtk, column in field_map.items():
        require(vtk in fields and close(fields[vtk], values[column]), f"CSV/VTK field differs: {vtk}")
    require(close(values["time_s"], history["time_s"], time=True)
            and close(values["native_time_s"], history["native_time_s"], time=True), "Saved clock differs")
    observer, material, config = contract["observer"], contract["material"], contract["configuration"]
    cohort = (initial[:, 0] > observer["cohortInitialXGreaterM"]) & (initial[:, 1] > observer["cohortInitialYGreaterM"])
    require(cohort.any() and np.array_equal(values["free_upper_reference_subset"], cohort.astype(float)), "Fixed physical cohort differs")
    require((pos[:, 0] >= 0).all() and (pos[:, 0] <= config["domainWidth"]).all()
            and (pos[:, 1] >= 0).all() and (pos[:, 1] <= config["domainHeight"]).all(), "Saved center exited domain/floor")
    kappa, work = values["mc_kappa"], values["plastic_work_pa"]
    require((kappa >= 0).all() and (work >= 0).all(), "Negative accumulated history/work")
    if previous is not None:
        require((kappa >= previous["mc_kappa"] - constants["kappa-tol"]).all(), "Saved kappa decreased beyond native allowance")
        require((work >= previous["plastic_work_pa"] - ATOL - RTOL * np.abs(previous["plastic_work_pa"])).all(), "Saved accumulated work decreased")
    if phase < 2:
        require((values["damage_active"] == 0).all() and (values["strength_damage"] == 0).all(), "Preparation damage not explicitly inactive")
        expected_c, expected_phi, expected_e, expected_nu = config["drainedCohesionPa"], math.radians(config["drainedFrictionDeg"]), config["drainedE"], config["drainedNu"]
    else:
        require((values["damage_active"] == 1).all() and (kappa >= values["kappa_origin"] - constants["kappa-tol"]).all(), "Owned active/history origin invalid")
        expected_c = law_strength(kappa, values["kappa_origin"], nodes)
        expected_phi, expected_e, expected_nu = 0, material["youngsModulusPa"], material["poissonRatio"]
        require(close(values["strength_damage"], 1 - values["cohesion_pa"] / material["peakStrengthPa"]), "D_s is not actual constitutive strength loss")
        require((values["strength_damage"] >= 0).all() and (values["strength_damage"] <= 1 - material["remoldedStrengthPa"] / material["peakStrengthPa"] + ATOL).all(), "Strength damage out of declared range")
        if phase == 3:
            require(np.array_equal(values["kappa_origin"], baseline["origin"]), "Per-particle activation origin changed")
        else:
            baseline["origin"] = values["kappa_origin"].copy()
    require(close(values["cohesion_pa"], expected_c) and close(values["friction_rad"], expected_phi)
            and close(values["dilation_rad"], 0) and close(values["E_pa"], expected_e) and close(values["nu"], expected_nu), "Actual phase material/law differs")
    tolerance = constants["stress-atol"] + constants["stress-rtol"] * np.maximum(1, values["native_projection_trial_scale_pa"])
    require((values["native_projection_trial_scale_pa"] >= 0).all() and close(tolerance, values["native_yield_tolerance_pa"]), "Native admissibility scale/tolerance differs")
    residual = six_plane_residual(values)
    require((residual <= tolerance).all() and (np.abs(residual - values["yield_residual_kirchhoff_pa"]) <= tolerance).all(), "Independent six-plane yield/residual check failed")
    kinetic = float(np.sum(0.5 * mass * np.sum(velocity**2, axis=1)))
    require(close(mass.sum(), history["mass_kg_per_m"]) and close(kinetic, history["kinetic_energy_j_per_m"])
            and close(j.min(), history["min_J"]), "Saved aggregate history differs")
    result = {"frame": int(history["frame"]), "timeS": history["time_s"], "nativeTimeS": history["native_time_s"],
              "phaseCode": phase, "particleCount": n, "massKgPerM": float(mass.sum()), "minJ": float(j.min()),
              "maximumYieldResidualPa": float(residual.max()), "maximumNativeTolerancePa": float(tolerance.max()),
              "maximumStrengthDamage": float(values["strength_damage"].max()), "maximumKappa": float(kappa.max()),
              "minimumCohesionPa": float(values["cohesion_pa"].min()), "kineticJPerM": kinetic,
              "minimumDomainMarginM": float(values["particle_domain_margin_m"].min()),
              "touchingDomainMassFraction": float(mass[values["particle_domain_margin_m"] <= 0].sum() / mass.sum()),
              "plasticWorkCurrentVolumeProxyJPerM": float(np.sum(values["volume_m3_per_m"] * work)),
              "vtk": record(vtk_path)}
    return baseline, result, pos, velocity, cohort


def preparation_check(path, contract, complete):
    config = contract["configuration"]
    count, last_time = 0, -1.0
    damped_count, damped_start, damped_end = 0, None, None
    hold_count, hold_start, hold_end = 0, None, None
    hold_started, confirmed_damped = False, False
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for raw in csv.DictReader(stream):
            row = {k: float(v.replace("D", "e").replace("d", "e")) for k, v in raw.items()}
            require(all(math.isfinite(v) for v in row.values()), "Nonfinite preparation history")
            require(row["native_time_s"] > last_time and row["updates"] == count + 1, "Preparation clock/update continuity failed")
            prior_time = last_time
            last_time, count = row["native_time_s"], count + 1
            require(count <= config["maxPreparationUpdates"] and last_time <= config["maxPreparationTimeS"] + TIME_ATOL,
                    "Preparation exceeded preregistered time/update cap")
            denom, num = row["free_force_denominator2"], row["free_force_numerator2"]
            require(num >= 0 and denom >= 0 and row["free_nodal_mass"] > 0 and row["free_KE"] >= 0, "Invalid free force/KE measures")
            defined = denom > 0
            require(row["force_defined"] == int(defined), "Undefined force denominator mislabelled")
            if defined:
                require(close(row["RF"], math.sqrt(num / denom)), "Free-force norm mismatch")
            rk = row["free_KE"] / (row["free_nodal_mass"] * abs(config["gravity"]) * config["height"])
            require(close(rk, row["RK"]), "Free nodal kinetic norm mismatch")
            passed = defined and row["native_time_s"] >= config["gravityRampDuration"] and row["RF"] < config["forceTolerance"] and rk < config["kineticTolerance"]
            require(row["damping"] >= 0, "Negative preparation damping")
            if row["damping"] > 0:
                require(not hold_started, "Preparation damping restarted after undamped release")
                if passed:
                    if damped_start is None:
                        damped_start = last_time
                    damped_count += 1
                    damped_end = last_time
                else:
                    damped_count, damped_start, damped_end = 0, None, None
            else:
                if not hold_started:
                    hold_started = True
                    confirmed_damped = (damped_count >= config["consecutiveChecks"] and damped_start is not None
                                        and damped_end - damped_start >= config["consecutiveDurationS"] - TIME_ATOL)
                    hold_start = prior_time
                require(passed, "An undamped saved preparation check failed")
                hold_count += 1
                hold_end = last_time
    if complete:
        require(confirmed_damped and hold_count >= config["undampedHoldUpdates"] and hold_start is not None
                and hold_end - hold_start >= config["undampedHoldDurationS"] - TIME_ATOL,
                "Actual50-check/1s damped convergence plus100-check/1s undamped hold not retained")
    return {"status": "PASS" if complete else "PARTIAL", "updates": count, "lastNativeTimeS": last_time,
            "dampedPassingChecks": damped_count, "dampedPassingDurationS": damped_end - damped_start if damped_start is not None else 0,
            "undampedPassingChecks": hold_count, "undampedPassingDurationS": hold_end - hold_start if hold_end is not None else 0,
            "scope": "Saved norms and actual terminal convergence window; raw nodal fields are not reconstructed"}


def transfer_check(run, manifest, drained, release):
    ledger_path = run / manifest["transferLedgerFile"]
    ledger = load_json(ledger_path)
    entries = ledger["entries"]
    n = len(release["particle_id"])
    require(len(entries) == n and ledger["mpmUpdates"] == 0,
            "Transfer ledger missing entries or contains MPM updates")
    require(close(ledger["nativeTimeS"], manifest["transferNativeTimeS"], time=True)
            and close(drained["native_time_s"], release["native_time_s"], time=True),
            "Transfer advanced/reset native clock")
    for name in ["x_m", "y_m", "vx_m_per_s", "vy_m_per_s", "mass_kg_per_m",
                 "reference_volume_m3_per_m", "volume_m3_per_m", "J"] + F_COLUMNS:
        require(close(drained[name], release[name]), f"Transfer changed preserved physical field: {name}")
    require(close(release["kappa_origin"], drained["mc_kappa"]), "Transfer erased/replaced original drained kappa")
    for i, entry in enumerate(entries):
        require(entry["particleIndex"] == i and entry["nativeMaterialCalls"] == 1
                and entry["mpmUpdates"] == 0 and entry["physicalTimeAdvancedS"] == 0,
                "Transfer per-particle call/time identity differs")
        for key, array in (("J", release["J"]), ("kappaOrigin", release["kappa_origin"]),
                           ("kappaBefore", drained["mc_kappa"]), ("kappaAfter", release["mc_kappa"]),
                           ("damageAfter", release["strength_damage"]), ("cohesionAfterPa", release["cohesion_pa"]),
                           ("plasticWorkBeforePa", drained["plastic_work_pa"]), ("plasticWorkAfterPa", release["plastic_work_pa"])):
            require(close(entry[key], array[i]), f"Transfer ledger field differs: {key}, ID{i}")
        before = np.array([drained[key][i] for key in STRESS_COLUMNS])
        after = np.array([release[key][i] for key in STRESS_COLUMNS])
        require(close(entry["cauchyBeforePa"], before) and close(entry["cauchyPredictorPa"], before)
                and close(entry["cauchyAfterReleasePa"], after), "Transfer Cauchy predictor/release identity differs")
        require(close(entry["materialSwitchProxyDifferenceJPerM"],
                      entry["elasticProxyPredictorJPerM"] - entry["elasticProxyBeforeJPerM"])
                and close(entry["instantaneousReleaseProxyDifferenceJPerM"],
                          entry["elasticProxyAfterReleaseJPerM"] - entry["elasticProxyPredictorJPerM"]),
                "Transfer elastic proxy bookkeeping differs")
    return {"status": "PASS", "particles": n, "nativeMaterialCalls": n, "mpmUpdates": 0,
            "ledger": record(ledger_path),
            "materialSwitchProxyDifferenceJPerM": sum(e["materialSwitchProxyDifferenceJPerM"] for e in entries),
            "instantaneousReleaseProxyDifferenceJPerM": sum(e["instantaneousReleaseProxyDifferenceJPerM"] for e in entries),
            "scope": "Actual cloned dt0 material release, not clock advance, whole-MPM restart, or closed energy budget"}


def inspect(run, contract, partial, read_vtk):
    manifest = load_json(run / "manifest.json")
    require(manifest.get("scenario") == contract["scenario"], "Wrong native scenario")
    complete = manifest.get("complete") is True
    require(complete or partial, "Incomplete run requires explicit --allow-partial")
    require(manifest.get("status") in ("complete", "failed"), "Refusing active/unknown native status")
    for name, expected in contract["configuration"].items():
        require(name in manifest["config"] and close(manifest["config"][name], expected), f"Native configuration differs: {name}")
    require(contract["serialization"] == {"absolute": ATOL, "relative": RTOL, "timeAbsolute": TIME_ATOL, "timeRelative": TIME_RTOL}, "Serialization tolerances changed")
    sources = verified_sources(run)
    verify_law_source(run, contract["material"])
    nodes, bound = reference_table(contract["material"])
    require(manifest["model"]["referencePdfSha256"] == contract["referencePdfSha256"]
            and close(manifest["model"]["tableNodes_s_kappa_cPa"], nodes)
            and close(manifest["model"]["maximumErrorBoundPa"], bound), "Actual native reference table/source differs")
    inputs = [record(run / "manifest.json")]
    preparation = preparation_check(run / manifest["preparationHistoryFile"], contract, complete)
    inputs.append(record(run / manifest["preparationHistoryFile"]))
    baseline, previous, audits, drained = None, None, [], None
    for frame, values in csv_frames(run / manifest["preparationParticleFile"]):
        history = history_rows(run / manifest["preparationStateFile"])
        require(frame in (0, 1) and frame in history, "Unexpected preparation saved frame")
        baseline, result, _, _, _ = audit_frame(values, history[frame], run / manifest["initialVtk" if frame == 0 else "drainedVtk"], read_vtk, baseline, previous, frame, contract, sources["constants"], nodes)
        audits.append(result)
        if frame == 1:
            drained = {k: value.copy() for k, value in values.items()}
        previous = {k: values[k].copy() for k in ("mc_kappa", "plastic_work_pa")}
    require(baseline is not None, "No initial saved frame")
    if complete:
        require(len(audits) == 2, "Complete native run lacks initial/drained snapshots")
    inputs += [record(run / manifest[k]) for k in ("preparationParticleFile", "preparationStateFile")]
    dynamic_path = run / manifest["particleFile"]
    states, velocities, candidate, transfer = [], [], None, None
    if dynamic_path.exists():
        history = history_rows(run / manifest["historyFile"])
        graph, release, cohort, switch_time = None, None, None, manifest.get("transferNativeTimeS")
        for frame, values in csv_frames(dynamic_path):
            require(frame == len(states) and frame in history, "Dynamic frame/history sequence mismatch")
            phase = 2 if frame == 0 else 3
            vtk = run / (manifest["dynamicVtkPattern"] % frame)
            baseline, result, pos, velocity, cohort = audit_frame(values, history[frame], vtk, read_vtk, baseline, previous, phase, contract, sources["constants"], nodes)
            require(close(result["nativeTimeS"] - switch_time, result["timeS"], time=True), "Native clock was reset/misaligned at transfer")
            require(close(result["timeS"], frame * 0.2, time=True), "Dynamic saved time differs from predeclared cadence")
            if release is None:
                require(drained is not None, "Dynamic release exists without drained reference snapshot")
                transfer = transfer_check(run, manifest, drained, values)
                inputs.append(transfer["ledger"])
                release = pos.copy()
                graph = graph_for(baseline["initial"], cohort, contract["observer"]["adjacencyM"])
            displacement = pos - release
            beta, observer, mass = math.radians(contract["configuration"]["slope"]), contract["observer"], baseline["mass"]
            downslope = displacement @ np.array([math.cos(beta), -math.sin(beta)])
            moving = cohort & (displacement[:, 0] >= observer["minimumDxM"]) & (downslope >= observer["minimumDownslopeM"])
            ids = largest_component(moving, graph, mass)
            fraction = float(mass[ids].sum() / mass[cohort].sum()) if len(ids) else 0.0
            velocities.append(velocity[:, 0].copy())
            result.update(cohortCentroidDisplacementM=np.average(displacement[cohort], weights=mass[cohort], axis=0).tolist(),
                          connectedMovingFractionOfCohortMass=fraction,
                          toeRunoutMassFraction=float(mass[pos[:, 0] > manifest["config"]["toeX"] + observer["toeOffsetM"]].sum() / mass.sum()),
                          frontXM=float(pos[:, 0].max()))
            positive = float(mass[ids][displacement[ids, 0] > 0].sum() / mass[ids].sum()) if len(ids) else 0
            if len(ids) and fraction >= observer["minimumConnectedFractionOfCohortMass"] and positive >= observer["minimumPositiveDxFractionOfComponentMass"]:
                means = np.asarray([np.average(v[ids], weights=mass[ids]) for v in velocities])
                interval = sustained_interval(np.array([s["timeS"] for s in states] + [result["timeS"]]), means, observer)
                result["fixedComponentVelocityInterval"] = interval
                if interval["status"] == "PASS" and candidate is None:
                    candidate = {"frame": frame, "timeS": result["timeS"], "logicalIds": ids.tolist(),
                                 "fractionOfCohortMass": fraction, "positiveDxMassFraction": positive, "sustainedVelocity": interval}
            states.append(result)
            previous = {k: values[k].copy() for k in ("mc_kappa", "plastic_work_pa")}
        require(len(states) == len(history), "Particle/history saved frame counts differ")
        inputs += [record(dynamic_path), record(run / manifest["historyFile"])]
    if complete:
        require(len(states) == contract["configuration"]["frames"] and close(states[-1]["timeS"], 60, time=True), "Native complete flag lacks all301 actual states/60dynamic seconds")
    require(len(states) == manifest.get("savedFrames", 0), "Manifest savedFrames differs from actual data")
    return {"schema": "cl-mpm.urmi-strength-damage40.review.v1", "integrity": "PASS", "completeNativeRun": complete,
            "reviewScope": "COMPLETE" if complete else "PARTIAL_SAVED_STATES_ONLY", "sourceProof": sources,
            "preparation": preparation, "transfer": transfer, "preparationSnapshots": audits, "states": states,
            "motionCandidate": candidate, "motionStatus": "DETECTED_REQUIRES_SPATIAL_REVIEW" if candidate else "NOT_DETECTED",
            "runoutGateDetected": any(s["toeRunoutMassFraction"] >= contract["observer"]["minimumRunoutFractionOfTotalMass"] for s in states),
            "landslideVerified": False, "scientificallyValidated": False, "manualSpatialReviewRequired": True,
            "inputs": inputs, "limitations": contract["limits"] + ["Only saved states; unsaved return/compliance state is not reconstructed", "Plastic-work current-volume sum is a proxy, not a closed energy balance", "Declared clone transfer preserves native unique IDs and vector-order logical IDs; object identity itself is not asserted"]}


def render(report, output, contract, read_vtk, video):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    states = report["states"]
    images = report["preparationSnapshots"] + states
    if not images:
        return {"status": "NOT_EVALUATED", "reason": "No saved states"}
    # All audited centers are retained and lie in this full computational box.
    config = contract["configuration"]
    frames = output / "frames"
    frames.mkdir()
    for state in images:
        points, fields = read_vtk(Path(state["vtk"]["path"]))
        fig, ax = plt.subplots(figsize=(15, 5.5), constrained_layout=True)
        dots = ax.scatter(points[:, 0], points[:, 1], c=fields["mc-strength-damage"], cmap="inferno", norm=Normalize(0, 1), s=5, linewidths=0)
        ax.set(xlim=(-0.5, config["domainWidth"] + 0.5), ylim=(-0.5, config["domainHeight"] + 0.5), xlabel="x (m)", ylabel="y (m)")
        ax.set_aspect("equal", adjustable="box")
        label = {0: "initial drained soil; strength damage inactive", 1: "equilibrated drained soil; strength damage inactive",
                 2: "instantaneous material release; no clock advance", 3: "undrained dynamics"}[state["phaseCode"]]
        ax.set_title(f"Urmi-inspired MC strength damage D_s = 1 - c/40.5kPa | {label}\ndynamic t={state['timeS']:.3f}s; native t={state['nativeTimeS']:.6f}s | actual particles, coordinate scale 1")
        fig.colorbar(dots, ax=ax, label="Constitutive strength loss D_s (not crack opening)", shrink=0.75)
        if state["phaseCode"] < 2:
            fig.savefig(output / f"preparation_{state['frame']:02d}.png", dpi=120)
        else:
            fig.savefig(frames / f"frame_{state['frame']:04d}.png", dpi=120)
        if state is images[-1]:
            fig.savefig(output / "damage-summary.png", dpi=150)
        plt.close(fig)
    media = {"status": "PASS", "actualStates": len(states), "colourRange": [0, 1], "coordinateScale": 1, "interpolation": False,
             "summary": record(output / "damage-summary.png"), "frames": str(frames)}
    if video and states:
        executable = shutil.which("ffmpeg")
        if executable is None:
            import imageio_ffmpeg
            executable = imageio_ffmpeg.get_ffmpeg_exe()
        destination = output / "strength-damage.mp4"
        command = [executable, "-y", "-framerate", str(contract["media"]["framesPerSecond"]), "-i", str(frames / "frame_%04d.png"),
                   "-frames:v", str(len(states)), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", str(destination)]
        result = subprocess.run(command, capture_output=True, text=True)
        (output / "video-command.json").write_text(json.dumps(command, indent=2), encoding="utf-8")
        (output / "video.stderr.log").write_text(result.stderr, encoding="utf-8")
        require(result.returncode == 0, "Video encoder failed; native saved data remains valid")
        decode = subprocess.run([executable, "-v", "error", "-i", str(destination), "-f", "null", "-"], capture_output=True, text=True)
        (output / "video-decode.stderr.log").write_text(decode.stderr, encoding="utf-8")
        require(decode.returncode == 0 and not decode.stderr.strip(), "Full video decode failed")
        media.update(video=record(destination), fullDecodeExitCode=decode.returncode, playbackDurationS=len(states) / contract["media"]["framesPerSecond"])
    return media


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--contract", type=Path, default=ROOT / "research/references/urmi-mc-damage40/contract.json")
    parser.add_argument("--video", action="store_true")
    parser.add_argument("--allow-partial", action="store_true", help="Terminal failed run only; never promotes partial output to full completion")
    parser.add_argument("--frozen-analysis-dir", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    run, output = args.run_dir.resolve(), args.output_dir.resolve()
    if args.frozen_analysis_dir is None:
        require(not output.exists(), "Choose a fresh review output directory")
        frozen = output / "analysis-source"
        frozen.mkdir(parents=True)
        records = []
        for original in (Path(__file__), Path(__file__).with_name("plot_m5_cliff_comparison.py"), args.contract):
            copied = frozen / original.name
            shutil.copyfile(original, copied)
            require(record(copied)["sha256"] == record(original)["sha256"], "Pre-execution analysis copy differs")
            records.append({"original": record(original), "copy": record(copied)})
        write_json(output / "analysis-freeze.json", {"createdUtc": datetime.now(timezone.utc).isoformat(), "records": records,
                                                     "scope": "Copied before review child execution; pre-native timing must be proved by launch preparation separately"})
        command = [sys.executable, str(frozen / Path(__file__).name), "--run-dir", str(run), "--output-dir", str(output),
                   "--contract", str(frozen / args.contract.name), "--frozen-analysis-dir", str(frozen)]
        if args.video:
            command.append("--video")
        if args.allow_partial:
            command.append("--allow-partial")
        write_json(output / "command.json", command)
        with (output / "stdout.log").open("w", encoding="utf-8") as stdout, (output / "stderr.log").open("w", encoding="utf-8") as stderr:
            child = subprocess.run(command, stdout=stdout, stderr=stderr)
        write_json(output / "exit.json", {"exitCode": child.returncode, "finishedUtc": datetime.now(timezone.utc).isoformat()})
        return child.returncode
    from plot_m5_cliff_comparison import read_cliff_vtk
    status_path = Path(str(run) + "-status.json")
    stage = "native-terminal-status"
    try:
        if status_path.exists():
            require(load_json(status_path).get("status") not in ("STARTING", "NATIVE_RUNNING", "POSTPROCESSING"), "Refusing review during active native execution")
        contract = load_json(args.contract)
        stage = "saved-state-audit"
        report = inspect(run, contract, args.allow_partial, read_cliff_vtk)
        write_json(output / "integrity.json", report)
        stage = "saved-state-media"
        report["media"] = render(report, output, contract, read_cliff_vtk, args.video)
        report["analysisBinding"] = load_json(output / "analysis-freeze.json")
        write_json(output / "review.json", report)
        print(json.dumps({"integrity": report["integrity"], "scope": report["reviewScope"], "actualDynamicStates": len(report["states"]), "motionStatus": report["motionStatus"], "landslideVerified": False}))
        return 0 if report["completeNativeRun"] else 2
    except Exception as error:
        write_json(output / "stage-failure.json", {"stage": stage, "error": str(error), "traceback": traceback.format_exc(),
                                                   "nativeSolverRerun": False, "savedInputsPreserved": True})
        raise


if __name__ == "__main__":
    raise SystemExit(main())
