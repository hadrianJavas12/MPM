#!/usr/bin/env python3
"""Review saved drive/hold MPM output by particle identity, without failure labels."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np

from plot_m5_cliff_comparison import read_cliff_vtk


WORK_COLUMN = "command_work_rectangle_J_per_m"


def file_record(path: Path, run: Path) -> dict:
    return {
        "path": str(path.relative_to(run)).replace("\\", "/"),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
    }


def native_csv(path: Path) -> list[dict[str, float]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = [
            {key: float(value.lower().replace("d", "e")) for key, value in row.items()}
            for row in csv.DictReader(stream)
        ]
    if not rows or not all(np.isfinite(list(row.values())).all() for row in rows):
        raise ValueError(f"Empty or nonfinite native CSV: {path}")
    return rows


def particle_ids(fields: dict, expected_count: int) -> np.ndarray:
    ids = fields["unique-id"]
    if (len(ids) != expected_count or not np.isfinite(ids).all()
            or not np.equal(ids, np.rint(ids)).all() or np.any(np.abs(ids) > 2**53)):
        raise ValueError("Missing, nonintegral or inexact native particle IDs")
    ids = ids.astype(np.int64)
    if len(np.unique(ids)) != expected_count:
        raise ValueError("Duplicate native particle IDs")
    return ids


def bounds(points: np.ndarray) -> dict:
    return {axis: {"minimum": float(points[:, index].min()),
                   "maximum": float(points[:, index].max())}
            for index, axis in enumerate(("x", "y", "z"))}


def sample_counts(rows: list[dict[str, float]]) -> dict:
    return {
        "samples": len(rows),
        "positiveReactionSamples": sum(row["reaction_upward_N_per_m"] > 0 for row in rows),
        "zeroReactionSamples": sum(row["reaction_upward_N_per_m"] == 0 for row in rows),
        "samplesWithActiveContacts": sum(row["active_contacts"] > 0 for row in rows),
        "samplesWithoutActiveContacts": sum(row["active_contacts"] == 0 for row in rows),
    }


def inspect(run: Path) -> dict:
    manifest_path = run / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    config = manifest["config"]
    if (manifest.get("complete") is not True or manifest.get("status") != "completed"
            or manifest.get("scenario") != "slope-creep"
            or config.get("loadingKind") != "crest-pusher"
            or not manifest.get("gravityConverged")
            or not manifest.get("reportingResetPreservedState")):
        raise ValueError("Review requires a complete, initialized slope-creep pusher run")
    velocity = config["pusherVelocity"]
    travel = config["pusherTravelM"]
    if not np.isfinite([velocity, travel]).all() or min(velocity, travel) <= 0:
        raise ValueError("Drive/hold review requires positive finite velocity and travel")
    stop_time = travel / velocity
    history_path, loading_path = run / "creep-history.csv", run / "loading-history.csv"
    history, loading = native_csv(history_path), native_csv(loading_path)
    if len(history) != config["frames"] or len(loading) != len(history):
        raise ValueError("Complete run frame counts differ from its declared configuration")
    times = np.array([row["time_s"] for row in history])
    if (times[0] != 0 or np.any(np.diff(times) <= 0)
            or not np.isclose(times[-1], config["duration"], rtol=1e-10, atol=1e-9)
            or not times[-1] > stop_time):
        raise ValueError("Drive/hold review requires increasing times through a post-stop hold")
    expected_count = manifest["particleCount"]
    if not isinstance(expected_count, int) or expected_count <= 0:
        raise ValueError("The native manifest must declare a positive particle count")
    frames, vtk_records = [], []
    baseline_ids = baseline_points = baseline_mass = region = None
    initial_centroid = None
    slope_radians = np.deg2rad(config["slope"])
    downslope = np.array([np.cos(slope_radians), -np.sin(slope_radians)])
    viewport = {"x": [0.0, float(config["width"])],
                "y": [0.0, float(config["baseHeight"] + config["height"] + config["meshSize"])]}
    mass_errors = []
    for index, (row, contact) in enumerate(zip(history, loading)):
        if (row["frame"] != index or contact["frame"] != index
                or not np.isclose(contact["time_s"], row["time_s"], rtol=1e-10, atol=1e-11)):
            raise ValueError("Native frame or contact times are inconsistent")
        if row["particle_count"] != expected_count or row["min_J"] <= 0:
            raise ValueError("Invalid particle count or saved minimum Jacobian")
        if abs(row["mass_error_fraction"]) > 1e-12:
            raise ValueError("Native history mass conservation failed")
        expected_command = min(velocity * row["time_s"], travel)
        if not np.isclose(contact["commanded_settlement_m"], expected_command,
                          rtol=1e-10, atol=1e-11):
            raise ValueError("Saved driver command differs from the declared drive/hold protocol")
        reaction = contact["reaction_upward_N_per_m"]
        if reaction < 0 or not np.isclose(reaction, contact["mapped_reaction_upward_N_per_m"],
                                          rtol=1e-9, atol=1e-6):
            raise ValueError("Tensile contact force or inconsistent mapped reaction")
        if (min(contact["active_contacts"], contact["separated_contacts"]) < 0
                or (row["time_s"] > 0 and contact["active_contacts"] + contact["separated_contacts"]
                    != manifest["pusherContactCount"])):
            raise ValueError("Invalid tracked contact counts")
        if WORK_COLUMN not in contact or contact[WORK_COLUMN] < 0:
            raise ValueError("Missing or negative per-update command-work diagnostic")
        path = run / "vtk" / f"particles_{index:04d}.vtk"
        points, fields = read_cliff_vtk(path)
        required = ("unique-id", "mass", "volume", "vel_x", "vel_y")
        if not all(name in fields for name in required):
            raise ValueError("Native VTK lacks required identity/mass/volume/velocity fields")
        if (len(points) != expected_count or not np.isfinite(points).all()
                or not all(np.isfinite(values).all() for values in fields.values())
                or np.any(fields["volume"] <= 0)):
            raise ValueError("Nonfinite native state or invalid particle count/volume")
        ids = particle_ids(fields, expected_count)
        order = np.argsort(ids)
        ids, points = ids[order], points[order]
        mass = fields["mass"][order]
        velocities = np.column_stack((fields["vel_x"][order], fields["vel_y"][order]))
        total_mass = float(mass.sum())
        relative_mass_error = (total_mass - manifest["initialMassKgPerM"]) / manifest["initialMassKgPerM"]
        mass_errors.append(abs(relative_mass_error))
        if not np.isclose(total_mass, manifest["initialMassKgPerM"], rtol=1e-11, atol=1e-8):
            raise ValueError("Saved VTK total mass differs from the initial mass")
        if index == 0:
            baseline_ids, baseline_points, baseline_mass = ids.copy(), points.copy(), mass.copy()
            region = baseline_points[:, 1] > config["baseHeight"]
            if not region.any():
                raise ValueError("The initial above-base particle region is empty")
            initial_centroid = np.average(baseline_points[region, :2], axis=0,
                                          weights=baseline_mass[region])
        elif (not np.array_equal(ids, baseline_ids)
              or not np.allclose(mass, baseline_mass, rtol=1e-12, atol=1e-12)):
            raise ValueError("Native particle identity set or identity-aligned particle mass changed")
        weights = baseline_mass[region]
        centroid = np.average(points[region, :2], axis=0, weights=weights)
        centroid_displacement = centroid - initial_centroid
        mean_velocity = np.average(velocities[region], axis=0, weights=weights)
        moving_right, moving_down = velocities[region, 0] > 0, velocities[region, 1] < 0
        right_down = moving_right & moving_down
        speed = np.linalg.norm(velocities, axis=1)
        kinetic_energy = float(.5 * np.sum(mass * speed**2))
        max_speed = float(speed.max())
        if (not np.isclose(kinetic_energy, row["kinetic_J_per_m"], rtol=1e-8, atol=1e-8)
                or not np.isclose(max_speed, row["max_speed_m_per_s"], rtol=1e-8, atol=1e-10)):
            raise ValueError("Recomputed two-dimensional velocity/KE differs from native CSV")
        coordinate_bounds = bounds(points)
        viewport_inside = all(coordinate_bounds[axis]["minimum"] >= limits[0]
                              and coordinate_bounds[axis]["maximum"] <= limits[1]
                              for axis, limits in viewport.items())
        frames.append({
            "frame": index, "timeS": float(row["time_s"]), "particleCount": expected_count,
            "massKgPerM": total_mass, "aboveBaseCentroidXM": float(centroid[0]),
            "aboveBaseCentroidYM": float(centroid[1]),
            "aboveBaseCentroidDxM": float(centroid_displacement[0]),
            "aboveBaseCentroidDyM": float(centroid_displacement[1]),
            "aboveBaseCentroidDownslopeDisplacementM": float(centroid_displacement @ downslope),
            "aboveBaseMassWeightedVxMPerS": float(mean_velocity[0]),
            "aboveBaseMassWeightedVyMPerS": float(mean_velocity[1]),
            "aboveBaseMassWeightedDownslopeVelocityMPerS": float(mean_velocity @ downslope),
            "aboveBaseRightDownMassFraction": float(weights[right_down].sum() / weights.sum()),
            "aboveBaseRightDownCountFraction": float(np.mean(right_down)),
            "aboveBaseRightwardMassFraction": float(weights[moving_right].sum() / weights.sum()),
            "aboveBaseDownwardMassFraction": float(weights[moving_down].sum() / weights.sum()),
            "maxVelocityNormMPerS": max_speed, "totalKineticEnergyJPerM": kinetic_energy,
            "minimumJFromNativeHistory": float(row["min_J"]),
            "coordinateBoundsM": coordinate_bounds, "allParticleCentersInsideOverviewViewport": viewport_inside,
            "driverReactionUpwardNPerM": reaction, "driverActiveContacts": int(contact["active_contacts"]),
            "driverCommandWorkRectangleJPerM": contact[WORK_COLUMN],
        })
        vtk_records.append(file_record(path, run))
    work = np.array([row[WORK_COLUMN] for row in loading])
    if work[0] != 0 or np.any(np.diff(work) < 0):
        raise ValueError("Command-work diagnostic does not start at zero and increase monotonically")
    hold_indices = np.flatnonzero(times >= stop_time)
    midpoint = (stop_time + float(times[-1])) / 2
    selected = [int(hold_indices[np.argmin(np.abs(times[hold_indices] - target))])
                for target in (stop_time, midpoint, float(times[-1]))]
    if not selected[0] < selected[1] < selected[2]:
        raise ValueError("Insufficient saved hold frames for two nonempty centroid secants")
    first, middle, last = [frames[index] for index in selected]

    def secant(start: dict, end: dict) -> dict:
        duration = end["timeS"] - start["timeS"]
        return {
            "startFrame": start["frame"], "endFrame": end["frame"],
            "startTimeS": start["timeS"], "endTimeS": end["timeS"],
            "centroidVxSecantMPerS": (end["aboveBaseCentroidDxM"] - start["aboveBaseCentroidDxM"]) / duration,
            "centroidVySecantMPerS": (end["aboveBaseCentroidDyM"] - start["aboveBaseCentroidDyM"]) / duration,
            "downslopeCentroidSecantMPerS": (end["aboveBaseCentroidDownslopeDisplacementM"]
                                             - start["aboveBaseCentroidDownslopeDisplacementM"]) / duration,
        }

    return {
        "reviewedAtUtc": datetime.now(timezone.utc).isoformat(),
        "scope": "Saved native output measurements; no laboratory calibration or failure threshold",
        "landslideVerified": False, "morphologyReview": "PENDING_INDEPENDENT_VISUAL_REVIEW",
        "nativeComplete": True,
        "integrity": {"finiteFields": True, "uniqueIdentitySetUnchanged": True,
                      "identityAlignedMassUnchanged": True, "particleCount": expected_count,
                      "massConservationConsistent": True, "maximumAbsoluteRelativeMassError": max(mass_errors),
                      "recomputed2dSpeedAndKineticEnergyConsistentWithHistory": True,
                      "nonTensileMappedContactForceConsistent": True},
        "regionDefinition": {"membership": "Fixed t=0 native particle IDs whose y coordinate exceeds baseHeight",
                             "baseHeightM": config["baseHeight"], "particleCount": int(region.sum()),
                             "initialMassKgPerM": float(baseline_mass[region].sum()),
                             "weights": "Initial particle masses; identity-aligned mass invariance checked",
                             "initialCentroidXM": float(initial_centroid[0]),
                             "initialCentroidYM": float(initial_centroid[1])},
        "downslopeDirection": {"definition": "Unit tangent to the declared initial slope, +x and -y; projection also includes settlement and alone does not establish sliding",
                               "x": float(downslope[0]), "y": float(downslope[1])},
        "velocityConvention": "Two-dimensional vel_x/vel_y; strict sign fractions, no motion-size threshold",
        "viewport": {"limitsM": viewport, "testsParticleCentersOnly": True,
                     "allSavedCentersInside": all(frame["allParticleCentersInsideOverviewViewport"] for frame in frames)},
        "protocol": {"velocityMPerS": velocity, "travelM": travel,
                     "driverStopTimeS": stop_time, "finalTimeS": float(times[-1]),
                     "commandWorkConvention": manifest.get("pusherCommandWorkConvention",
                         "Per-update right-end reaction times command increment; not a closed energy budget")},
        "hold": {"selection": "Nearest existing frame at/after driver stop; nearest hold midpoint and final frame; no interpolation",
                 "requestedTimesS": [stop_time, midpoint, float(times[-1])],
                 "selectedFrames": selected, "selectedTimesS": [first["timeS"], middle["timeS"], last["timeS"]],
                 "firstHalfSecant": secant(first, middle), "secondHalfSecant": secant(middle, last),
                 "atFirstSavedHoldFrame": first, "atFinalFrame": last,
                 "commandWorkAtFirstSavedHoldFrameJPerM": float(work[selected[0]]),
                 "commandWorkAtFinalFrameJPerM": float(work[-1]),
                 "commandWorkExactlyConstantAcrossSavedHold": bool(np.all(work[hold_indices] == work[selected[0]])),
                 "sampledContact": sample_counts([loading[index] for index in hold_indices])},
        "sampledContact": {"excludesUnevaluatedInitialFrame": True,
                           "allAfterTimeZero": sample_counts(loading[1:]),
                           "beforeDriverStop": sample_counts([row for row in loading if 0 < row["time_s"] < stop_time])},
        "frames": frames,
        "inputs": [file_record(path, run) for path in (manifest_path, history_path, loading_path)] + vtk_records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    arguments = parser.parse_args()
    run = arguments.run_dir.resolve()
    source = Path(__file__).resolve()
    reader = source.with_name("plot_m5_cliff_comparison.py")
    source_hashes = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in (source, reader)}
    report = inspect(run)
    support = run / "analysis-support"
    support.mkdir(exist_ok=True)
    supporting_scripts = []
    for path, expected_hash in source_hashes.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
            raise RuntimeError("A supporting script changed during analysis")
        retained = support / path.name
        if path != retained:
            shutil.copyfile(path, retained)
        record = file_record(retained, run)
        if record["sha256"] != expected_hash:
            raise RuntimeError("Retained supporting script hash differs from the executed source")
        supporting_scripts.append(record)
    report["supportingScripts"] = supporting_scripts
    destination = run / "drive-hold-review.json"
    destination.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"review": str(destination), "landslideVerified": False,
                      "morphologyReview": report["morphologyReview"], "integrity": report["integrity"],
                      "hold": {key: value for key, value in report["hold"].items()
                               if key not in ("atFirstSavedHoldFrame", "atFinalFrame")}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
