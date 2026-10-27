#!/usr/bin/env python3
"""NEW saved-only1vs4worker experiment comparison; never run/stop/modify MPM."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import shutil
import traceback

import numpy as np

ATOL = RTOL = 1e-11
TIME_ATOL = TIME_RTOL = 1e-10
ROOT = Path(__file__).resolve().parents[1]
F = [f"F_{i}{j}" for i in range(3) for j in range(3)]
STRESS = [f"sig_{axis}_pa" for axis in ("xx", "yy", "zz", "yz", "xz", "xy")]
EXACT = {"frame", "particle_id", "phase_code", "damage_active", "free_upper_reference_subset", "particle_count",
         "updates", "dynamic_updates", "preparation_updates", "force_ratio_defined", "free_ke_ratio_defined"}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def close(a, b, *, time=False):
    return np.allclose(a, b, atol=TIME_ATOL if time else ATOL, rtol=TIME_RTOL if time else RTOL)


def numeric_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames
        require(columns and len(columns) == len(set(columns)), f"Duplicate/missing CSV columns: {path}")
        rows = [{key: float(value.replace("d", "e").replace("D", "E")) for key, value in row.items()} for row in reader]
    values = {key: np.asarray([row[key] for row in rows], dtype=float) for key in columns}
    require(rows and all(np.isfinite(a).all() for a in values.values()), f"Empty/nonfinite numeric CSV: {path}")
    return values


def compare_columns(a, b, label):
    require(a.keys() == b.keys(), f"Different columns/scalars: {label}")
    maximum = {}
    for key in a:
        require(a[key].shape == b[key].shape, f"Different shape: {label}/{key}")
        ok = np.array_equal(a[key], b[key]) if key in EXACT else close(a[key], b[key], time="time" in key)
        require(ok, f"Worker state differs: {label}/{key}")
        maximum[key] = float(np.max(np.abs(a[key] - b[key])))
    return maximum


def compare_json(a, b, label):
    if isinstance(a, dict):
        require(isinstance(b, dict) and a.keys() == b.keys(), f"JSON keys differ: {label}")
        for key in a:
            compare_json(a[key], b[key], f"{label}/{key}")
    elif isinstance(a, list):
        require(isinstance(b, list) and len(a) == len(b), f"JSON array differs: {label}")
        for i, (x, y) in enumerate(zip(a, b)):
            compare_json(x, y, f"{label}/{i}")
    elif isinstance(a, (int, float)) and not isinstance(a, bool):
        require(isinstance(b, (int, float)) and math.isfinite(a) and math.isfinite(b) and close(a, b), f"JSON number differs: {label}")
    else:
        require(a == b, f"JSON value differs: {label}")


def payload(directory):
    result = {}
    for row in load(directory / "source/source-manifest.json")["files"]:
        path = directory / row["path"]
        require(path.is_file() and sha(path) == row["sha256"], f"Frozen source payload hash differs: {path}")
        require(row["path"] not in result, f"Duplicate source record: {path}")
        result[row["path"]] = row["sha256"]
    return result


def native_constants(directory):
    text = (directory / "source/materials/models/plastic/mohr-coulomb-evolution/projection.lisp").read_text()
    values = {}
    for name in ("stress-atol", "stress-rtol", "kappa-tol"):
        found = re.search(r"\(defconstant\s+\+" + name + r"\+\s+([\d.eEdD+-]+)\)", text)
        require(found is not None, f"Missing frozen native constant: {name}")
        values[name] = float(found[1].replace("d", "e").replace("D", "E"))
    return values


def audit_states(directory, result, read_vtk):
    values = numeric_csv(directory / "material-state.csv")
    history = numeric_csv(directory / "history.csv")
    extra = numeric_csv(directory / "native-state-extra.csv")
    n = result["observations"]["particleCount"]
    require(n == 6714 and len(values["frame"]) == 2 * n and len(history["frame"]) == 2, "Expected two6714MP states")
    require(len(extra["frame"]) == 2 * n, "Missing native elastic/plastic increment arrays")
    config, material = result["observations"]["physicalConfig"], result["observations"]["materialReference"]
    constants, nodes = native_constants(directory), np.asarray(material["tableNodes_s_kappa_cPa"])
    summaries = []
    previous = None
    for frame, phase, name in ((0, 1, "drained.vtk"), (1, 3, "undrained.vtk")):
        use = values["frame"] == frame
        v = {key: array[use] for key, array in values.items()}
        e = {key: array[extra["frame"] == frame] for key, array in extra.items()}
        require(np.array_equal(v["particle_id"], np.arange(n)) and np.array_equal(e["particle_id"], np.arange(n)), "IDs/order/count differ")
        require((v["phase_code"] == phase).all(), "Wrong phase")
        require((v["mass_kg_per_m"] > 0).all() and (v["J"] > 0).all() and (v["reference_volume_m3_per_m"] > 0).all(), "Invalid mass/J/V0")
        matrix = np.column_stack([v[key] for key in F]).reshape(n, 3, 3)
        require(close(np.linalg.det(matrix), v["J"]) and close(v["volume_m3_per_m"], v["J"] * v["reference_volume_m3_per_m"]), "Global F/J/V0 identity failed")
        points, fields = read_vtk(directory / name)
        require(points.shape == (n, 3) and close(points[:, 0], v["x_m"]) and close(points[:, 1], v["y_m"]), "CSV/VTK positions differ")
        require(close(points[:, 2], 0) and np.array_equal(fields["unique-id"], np.arange(n)) and np.array_equal(fields["mc-logical-id"], np.arange(n)), "VTK logical/native IDs differ")
        mapping = {"mass": "mass_kg_per_m", "mc-kappa": "mc_kappa", "mc-cohesion-pa": "cohesion_pa",
                   "mc-friction-rad": "friction_rad", "mc-dilation-rad": "dilation_rad", "mc-plastic-volume": "plastic_volume",
                   "mc-plastic-work-j-m3": "plastic_work_pa", "mc-yield-residual-kirchhoff-pa": "yield_residual_kirchhoff_pa",
                   "mc-strength-damage": "strength_damage", "mc-damage-active": "damage_active", "mc-kappa-origin": "kappa_origin"}
        for field, key in mapping.items():
            require(close(fields[field], v[key]), f"CSV/VTK state mismatch: {field}")
        require((v["mc_kappa"] >= 0).all() and (v["plastic_work_pa"] >= 0).all(), "Negative accumulated history/work")
        if frame == 0:
            require((v["damage_active"] == 0).all() and (v["strength_damage"] == 0).all(), "Drained damage must be inactive")
            c, phi, young, nu = config["drainedCohesionPa"], math.radians(config["drainedFrictionDeg"]), config["drainedE"], config["drainedNu"]
        else:
            require(np.array_equal(v["mass_kg_per_m"], previous["mass_kg_per_m"]) and np.array_equal(v["reference_volume_m3_per_m"], previous["reference_volume_m3_per_m"]), "Transfer changed mass/V0")
            require(close(v["kappa_origin"], previous["mc_kappa"]) and (v["mc_kappa"] >= v["kappa_origin"] - constants["kappa-tol"]).all(), "Activation origin/history differs")
            require((v["damage_active"] == 1).all() and close(v["strength_damage"], 1 - v["cohesion_pa"] / material["peakStrengthPa"]), "Damage/strength identity failed")
            require((v["strength_damage"] >= 0).all() and (v["strength_damage"] <= material["damageMaximum"]).all(), "Damage bounds failed")
            c = np.interp(v["mc_kappa"] - v["kappa_origin"], nodes[:, 1], nodes[:, 2])
            phi, young, nu = 0, material["youngsModulusPa"], material["poissonRatio"]
        require(close(v["cohesion_pa"], c) and close(v["friction_rad"], phi) and close(v["dilation_rad"], 0) and close(v["E_pa"], young) and close(v["nu"], nu), "Phase law/elasticity differs")
        tau = np.zeros((n, 3, 3))
        for (i, j), key in zip(((0, 0), (1, 1), (2, 2), (1, 2), (0, 2), (0, 1)), STRESS):
            tau[:, i, j] = tau[:, j, i] = v[key] * v["J"]
        principal, sine = np.linalg.eigvalsh(tau), np.sin(v["friction_rad"])
        offset = 2 * v["J"] * v["cohesion_pa"] * np.cos(v["friction_rad"])
        residual = np.max(np.column_stack([(1 + sine) * principal[:, i] - (1 - sine) * principal[:, j] - offset
                                           for i in range(3) for j in range(3) if i != j]), axis=1)
        tolerance = constants["stress-atol"] + constants["stress-rtol"] * np.maximum(1, v["native_projection_trial_scale_pa"])
        require(close(tolerance, v["native_yield_tolerance_pa"]) and (residual <= tolerance).all()
                and (np.abs(residual - v["yield_residual_kirchhoff_pa"]) <= tolerance).all(), "Independent six-plane/native yield check failed")
        for i, key in enumerate(STRESS):
            require(close(e[f"tau_{i}"], v[key] * v["J"]), "Extra Kirchhoff stress differs from Cauchy/J")
        require(close(v["native_time_s"], history["native_time_s"][frame], time=True) and close(v["time_s"], history["time_s"][frame], time=True), "Clock alignment failed")
        require(close(v["mass_kg_per_m"].sum(), history["mass_kg_per_m"][frame]), "Aggregate mass differs")
        summaries.append({"frame": frame, "particles": n, "minJ": float(v["J"].min()), "maximumDamage": float(v["strength_damage"].max())})
        previous = v
    return values, history, extra, summaries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial-dir", required=True, type=Path)
    parser.add_argument("--parallel-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    out = args.output_dir.resolve()
    require(not out.exists(), "Use fresh comparison output; preserve previous evidence")
    (out / "analysis").mkdir(parents=True)
    source_reader = ROOT / "scripts/plot_m5_cliff_comparison.py"
    for source in (Path(__file__).resolve(), source_reader):
        shutil.copyfile(source, out / "analysis" / source.name)
    directories = [args.serial_dir.resolve(), args.parallel_dir.resolve()]
    records = [{"path": str(path), "sha256": sha(path)} for directory in directories
               for path in sorted(directory.rglob("*")) if path.is_file() and "source" not in path.relative_to(directory).parts]
    records += [{"path": str(path), "sha256": sha(path)} for path in sorted((out / "analysis").glob("*.py"))]
    (out / "inputs-before.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    report = {"passed": False, "scope": "NEW saved bounded worker equivalence/performance review; not full60s/plastic slope validation or speed guarantee"}
    try:
        results = [load(directory / "result.json") for directory in directories]
        require([result["workers"] for result in results] == [1, 4] and all(result["passed"] for result in results), "Need accepted worker1and4 native results")
        require(all(result["mpmUpdatesAccepted"] == 20 and len(result["passedGroups"]) == 4 for result in results), "Incomplete bounded native workload")
        require(payload(directories[0]) == payload(directories[1]), "Native source/input/DLL payloads differ")
        require(results[0]["nativeBackend"]["sha256"] == results[1]["nativeBackend"]["sha256"], "Mapped native DLL differs")
        for directory, result in zip(directories, results):
            module = Path(result["nativeBackend"]["modulePath"])
            require(module.is_file() and sha(module) == result["nativeBackend"]["sha256"], f"Actual mapped DLL bytes differ: {directory}")
        compare_json(results[0]["observations"]["physicalConfig"], results[1]["observations"]["physicalConfig"], "physicalConfig")
        compare_json(results[0]["observations"]["materialReference"], results[1]["observations"]["materialReference"], "materialReference")
        require(results[0]["counters"] == results[1]["counters"], "Worker native-call counters differ")
        for stage, attempted, accepted in (("drained", 67140, 67140), ("transfer", 6714, 6714),
                                            ("undrained", 67140, 67140), ("plastic-native", 72, 72), ("expected-failure", 1, 0)):
            row = next(item for item in results[0]["counters"] if item["stage"] == stage)
            require((row["attempted"], row["accepted"]) == (attempted, accepted), f"Wrong actual native call count: {stage}")
        spec = importlib.util.spec_from_file_location("frozen_worker_vtk_reader", out / "analysis" / source_reader.name)
        reader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reader)
        audited = [audit_states(directory, result, reader.read_cliff_vtk) for directory, result in zip(directories, results)]
        report["stateDeltas"] = {name: compare_columns(audited[0][i], audited[1][i], name)
                                 for i, name in enumerate(("particleCSV", "historyCSV", "nativeExtraCSV"))}
        for name in ("drained.vtk", "undrained.vtk"):
            a, af = reader.read_cliff_vtk(directories[0] / name)
            b, bf = reader.read_cliff_vtk(directories[1] / name)
            require(close(a, b), f"Worker VTK positions differ: {name}")
            report["stateDeltas"][name] = compare_columns(af, bf, name)
        for name in ("plastic-inputs-before.json", "plastic-results.json", "expected-rejection-input-before.json", "expected-rejection-capsule.json"):
            compare_json(load(directories[0] / name), load(directories[1] / name), name)
        material = results[0]["observations"]["materialReference"]
        nodes = np.asarray(material["tableNodes_s_kappa_cPa"])
        for directory in directories:
            fixtures, points = load(directory / "plastic-inputs-before.json")["fixtures"], load(directory / "plastic-results.json")["results"]
            require(len(fixtures) == len(points) == 72, "Missing72native plastic point results")
            require([row["regime"] for row in points].count("drained") == 36 and [row["regime"] for row in points].count("undrained") == 36,
                    "Missing drained or undrained plastic workload")
            for i, (fixture, point) in enumerate(zip(fixtures, points)):
                require(point["id"] == i and fixture["regime"] == point["regime"], "Plastic point identity/regime mismatch")
                require(point["kappa"] > 0 and point["workPa"] >= 0 and len(point["sixPlaneResidualsPa"]) == 6,
                        "Invalid native plastic history/work/residuals")
                require(max(point["sixPlaneResidualsPa"]) <= point["nativeStressTolerancePa"], "Native point six-plane yield rejection")
                expected_c = 3700 if point["regime"] == "drained" else np.interp(point["kappa"], nodes[:, 1], nodes[:, 2])
                require(close(point["cohesionPa"], expected_c), "Native plastic point law strength differs")
                expected_damage = 0 if point["regime"] == "drained" else 1 - point["cohesionPa"] / material["peakStrengthPa"]
                require(point["damageActive"] == (0 if point["regime"] == "drained" else 1)
                        and close(point["strengthDamage"], expected_damage), "Native plastic point damage differs")
        blocks = [{row["name"]: row for row in result["timings"]} for result in results]
        timings = {}
        for phase in ("drained", "undrained"):
            totals = [sum(blocks[i][f"{phase}-four-USF-block{block}"]["realSeconds"] for block in range(2)) for i in range(2)]
            require(min(totals) > 0, "Invalid measured timing")
            timings[phase] = {"serialEightStepsSeconds": totals[0], "fourWorkerEightStepsSeconds": totals[1], "observedRatio": totals[0] / totals[1]}
        plastic_times = [block["seventy-two-native-plastic-points"]["realSeconds"] for block in blocks]
        require(min(plastic_times) > 0, "Invalid measured plastic fixture timing")
        timings["syntheticNativePlastic72"] = {"serialSeconds": plastic_times[0], "fourWorkerSeconds": plastic_times[1],
                                               "observedRatio": plastic_times[0] / plastic_times[1]}
        report.update(passed=True, auditedStates=[row[3] for row in audited], timings=timings,
                      fixedTolerances={"stateAtol": ATOL, "stateRtol": RTOL, "timeAtol": TIME_ATOL, "timeRtol": TIME_RTOL},
                      timingLimits="Only two4step blocks per phase after2warmups; near-elastic geometry workload; native synthetic plastic fixture separate; active full001 and OS load confound timings; no claimed4x or reliable fullrun ETA")
        require(all(sha(Path(row["path"])) == row["sha256"] for row in records), "Compared/frozen inputs changed during review")
    except Exception as error:
        report["failure"] = str(error)
        (out / "failure.log").write_text(traceback.format_exc(), encoding="utf-8")
    (out / "review.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
