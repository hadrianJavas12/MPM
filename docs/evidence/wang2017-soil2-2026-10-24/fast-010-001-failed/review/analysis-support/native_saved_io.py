"""Read-only, non-interpolated Wang2017 saved-output comparison. No solver calls."""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return [{key: float(value.lower().replace("d", "e")) for key, value in row.items()}
                for row in csv.DictReader(stream)]


def vtk(path):
    data, offset = path.read_bytes(), 0

    def line():
        nonlocal offset
        end = data.index(b"\n", offset)
        result = data[offset:end].decode("ascii").rstrip("\r")
        offset = end + 1
        return result

    def array(count):
        nonlocal offset
        if offset + count * 8 > len(data):
            raise ValueError("Truncated VTK array")
        result = np.frombuffer(data, dtype=">f8", count=count, offset=offset).astype(float)
        offset += count * 8
        if line() != "" or not np.isfinite(result).all():
            raise ValueError("Nonfinite or malformed VTK array")
        return result

    if not line().startswith("# vtk DataFile Version"):
        raise ValueError("Missing VTK signature")
    line()
    if line() != "BINARY" or line() != "DATASET UNSTRUCTURED_GRID":
        raise ValueError("Unsupported VTK layout")
    header = line().split()
    if header[0] != "POINTS" or header[2] != "double":
        raise ValueError("Unsupported coordinates")
    count = int(header[1])
    points = array(3 * count).reshape(count, 3)
    if line() != f"POINT_DATA {count}":
        raise ValueError("Point count mismatch")
    fields = {}
    while offset < len(data):
        text = line()
        if not text:
            continue
        header = text.split()
        if header[0] != "SCALARS" or header[2] != "double" or line() != "LOOKUP_TABLE default":
            raise ValueError("Unsupported scalar layout")
        fields[header[1]] = array(count)
    ids = fields["unique-id"]
    if len(np.unique(ids)) != count or not (ids == np.floor(ids)).all():
        raise ValueError("Invalid particle IDs")
    order = np.argsort(ids)
    return points[order], {key: value[order] for key, value in fields.items()}


def load(run):
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8-sig"))
    force, energy, gravity = [rows(run / name) for name in
                              ("force-displacement.csv", "energy-history.csv", "gravity-state.csv")]
    if not force or len(force) != len(energy):
        raise ValueError("Missing or inconsistent CSV rows")
    if any(not np.isfinite(list(row.values())).all() for group in (force, energy, gravity) for row in group):
        raise ValueError("Nonfinite CSV data")
    initial_p, initial_f = vtk(run / "vtk/gravity_initial.vtk")
    initial_ids, initial_volume = initial_f["unique-id"], initial_f["volume"]
    states, consumed = [], []
    finite_ids = positive_volume = positive_mass = True
    max_mass_error = max_kinetic_error = 0.0
    volume_ratio_min, volume_ratio_max = float("inf"), float("-inf")
    for row, en in zip(force, energy):
        path = run / "vtk" / f"particles_{int(row['frame']):04d}.vtk"
        points, fields = vtk(path)
        if not np.array_equal(fields["unique-id"], initial_ids):
            raise ValueError("Particle IDs changed")
        if len(points) != int(row["particle_count"]):
            raise ValueError("CSV/VTK particle count mismatch")
        positive_mass &= bool((fields["mass"] > 0).all())
        positive_volume &= bool((fields["volume"] > 0).all())
        ratio = fields["volume"] / initial_volume
        volume_ratio_min, volume_ratio_max = min(volume_ratio_min, float(ratio.min())), max(volume_ratio_max, float(ratio.max()))
        max_mass_error = max(max_mass_error, abs(float(fields["mass"].sum()) - force[0]["mass_kg_per_m"]))
        kinetic = .5 * float(np.sum(fields["mass"] * (fields["vel_x"]**2 + fields["vel_y"]**2)))
        max_kinetic_error = max(max_kinetic_error, abs(kinetic - row["kinetic_energy_J_per_m"]))
        if row["time_s"] != en["time_s"] or row["frame"] != en["frame"]:
            raise ValueError("Energy CSV alignment mismatch")
        states.append((points, fields))
        consumed.append({"path": path.relative_to(run).as_posix(), "sha256": sha(path)})
    with (run / "force-displacement.csv").open(encoding="utf-8-sig", newline="") as stream:
        commands = [Decimal(row["commanded_settlement_m"].lower().replace("d", "e")) for row in csv.DictReader(stream)]
    if len(set(commands)) != len(commands) or commands != sorted(commands):
        raise ValueError("Commanded displacement must increase uniquely")
    F = np.array([[[r[f"F_{i}{j}"] for j in range(3)] for i in range(3)] for r in gravity])
    determinants = np.linalg.det(F)
    source_manifest = json.loads((run / "source/source-manifest.json").read_text(encoding="utf-8-sig"))
    failed_hashes = [entry["path"] for entry in source_manifest["files"] if sha(run / entry["path"]) != entry["sha256"].lower()]
    if failed_hashes:
        raise ValueError(f"Frozen source mismatch: {failed_hashes}")
    proof = json.loads((run / "source-provenance.json").read_text(encoding="utf-8-sig"))
    sources = {entry["path"]: entry["sha256"].lower() for entry in source_manifest["files"]}
    for path in [run / name for name in ("force-displacement.csv", "energy-history.csv", "gravity-state.csv", "manifest.json", "source/source-manifest.json", "source-provenance.json")]:
        consumed.append({"path": path.relative_to(run).as_posix(), "sha256": sha(path)})
    summary = {
        "run": str(run), "nativeManifestStatus": manifest.get("status"), "nativeComplete": manifest.get("complete"),
        "nativeExitInterpretation": "Not inferred from saved outputs; wrapper/process audit handled separately",
        "loadingFrames": len(force), "particleCount": len(initial_ids), "physicalTimeS": force[-1]["time_s"],
        "lastCommandedSettlementM": force[-1]["commanded_settlement_m"], "allSavedNumericFieldsFinite": True,
        "particleIdsStableAndUnique": finite_ids, "positiveSavedVolumes": positive_volume, "positiveSavedMasses": positive_mass,
        "massKgPerM": force[0]["mass_kg_per_m"], "maxAbsoluteVtkMassErrorKgPerM": max_mass_error,
        "maxAbsRecomputed2DKineticMinusCsvJPerM": max_kinetic_error,
        "volumeOverInitialVolumeRange": [volume_ratio_min, volume_ratio_max],
        "gravityDeterminantFRange": [float(determinants.min()), float(determinants.max())],
        "loadingDeterminantJ": "NOT_DIRECTLY_SAVED: positive volume ratio is not independent det(F) evidence",
        "maxAbsoluteMeanTrackingErrorM": max(abs(r["penalty_gap_m"]) for r in force),
        "maxAbsoluteCommandMinusMeasuredMinusGapM": max(abs(r["commanded_settlement_m"] - r["measured_settlement_m"] - r["penalty_gap_m"]) for r in force),
        "maxIndividualTrackingGapM": max(r["max_gap_m"] for r in force),
        "maxAbsReactionPlusSoilForceNPerM": max(abs(r["reaction_upward_N_per_m"] + r["soil_force_y_N_per_m"]) for r in force),
        "maxAbsSoilMinusNodalForceNPerM": max(abs(r["soil_force_y_N_per_m"] - r["nodal_force_y_N_per_m"]) for r in force),
        "reactionRangeNPerM": [min(r["reaction_upward_N_per_m"] for r in force), max(r["reaction_upward_N_per_m"] for r in force)],
        "kineticRangeJPerM": [min(r["kinetic_energy_J_per_m"] for r in force), max(r["kinetic_energy_J_per_m"] for r in force)],
        "maxKineticOverElasticProxy": max(e["kinetic_over_elastic_proxy"] for e in energy),
        "maxFreeResidualRatio": max(r["free_residual_ratio"] for r in force),
        "lastHistoryRange": [float(states[-1][1].get("wang-paper-kps",states[-1][1].get("mc-kappa")).min()), float(states[-1][1].get("wang-paper-kps",states[-1][1].get("mc-kappa")).max())],
        "frozenSourcesHashVerifiedCount": len(source_manifest["files"]),
        "provenanceExactLoadedBytesClaim": proof["sourceSnapshotExactLoadedBytes"],
        "actualBackendSha256": proof["nativeBackend"]["sha256"],
        "noInterpolation": True,
    }
    return manifest, force, energy, states, commands, sources, summary, consumed


