"""Summarize an already executed saved-data review and hash terminal sources.

No solver, constitutive return, VTK reader, renderer or kinematic audit runs.
"""
import csv
import hashlib
import json
from pathlib import Path


REVIEW = Path(__file__).resolve().parents[1]
RUN = REVIEW.parent
ADJACENT = RUN.parent


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def record(path):
    payload = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}


def write(name, value):
    path = REVIEW / name
    if path.exists():
        raise RuntimeError(f"Preserve previous terminal summary: {path}")
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


review = load(REVIEW / "review.json")
native = load(RUN / "manifest.json")
status_path = ADJACENT / (RUN.name + "-status.json")
worker_path = ADJACENT / (RUN.name + "-detached") / "worker-exit.json"
status, worker = load(status_path), load(worker_path)
if not (review["integrityStatus"] == "PASS" and native["complete"] and native["timeS"] == 6
        and status["nativeExitCode"] == 0 and status["nativeComplete"] and worker["exitCode"] == 0):
    raise RuntimeError("Original native/worker completion and saved review do not agree")
source_manifest = load(RUN / "source/source-manifest.json")
verified = []
for expected in source_manifest["files"]:
    source = (RUN / expected["path"]).resolve()
    if not source.is_relative_to((RUN / "source").resolve()):
        raise RuntimeError("Source member escapes frozen directory")
    actual = record(source)
    if (actual["sha256"], actual["bytes"]) != (expected["sha256"], expected["bytes"]):
        raise RuntimeError(f"Terminal executed source changed: {source}")
    verified.append({"path": expected["path"], "sha256": actual["sha256"], "bytes": actual["bytes"]})
if len(verified) != 282:
    raise RuntimeError("Unexpected executed source count")
provenance = load(RUN / "source-provenance.json")
backend = provenance["nativeBackend"]
dll = next(row for row in verified if row["path"] == "source/libs/kirchoff.dll")
if not (provenance["sourceSnapshotExactLoadedBytes"] and provenance["copiedByteEqualityBeforeLoad"]
        and backend["sha256"] == dll["sha256"]
        and backend["verifiedBy"] == "GetModuleHandleW/GetModuleFileNameW"):
    raise RuntimeError("Terminal source runtime/mapped DLL proof disagrees")
write("source-files-terminal-verification.json", {
    "scope": "Terminal file hash/length and recorded runtime proof; no solver/replay/analysis rerun",
    "sourceFiles": len(verified), "allMatched": True, "files": verified,
    "sourceManifest": record(RUN / "source/source-manifest.json"),
    "runtimeProvenance": record(RUN / "source-provenance.json"), "actualMappedDll": backend,
    "nativeStatus": status, "workerExit": worker, "statusFile": record(status_path),
    "workerExitFile": record(worker_path), "verificationScript": record(Path(__file__))})
with (RUN / "history.csv").open(encoding="utf-8-sig", newline="") as stream:
    history = [{key: float(value.lower().replace("d", "e")) for key, value in row.items()}
               for row in csv.DictReader(stream)]
peak = max(history, key=lambda row: row["kinetic_energy_j_per_m"])
yield_checks = [check for frame in review["frameIntegrity"] for check in frame["checks"]
                if check["name"] == "six-plane-current-state-admissibility"]
summary = {
    "scope": "Read already emitted review/history and recorded completion; no native or independent saved-data audit repetition",
    "nativeExit": 0, "workerExit": 0, "nativeComplete": True,
    "physicalDurationS": native["timeS"], "nativeUpdates": native["updates"],
    "savedStates": review["savedFrames"], "particlesPerState": native["particleCount"],
    "materialCsvRows": native["particleCount"] * review["savedFrames"],
    "initialMassKgPerM": history[0]["mass_kg_per_m"],
    "minimumSavedJ": min(row["min_J"] for row in history),
    "maximumSavedDisplacementM": max(row["max_displacement_m"] for row in history),
    "maximumSavedSpeedMPerS": max(row["max_speed_m_per_s"] for row in history),
    "maximumSavedKappa": max(row["max_kappa"] for row in history),
    "maximumIndependentYieldResidualPa": max(row["maximumYieldResidualPa"] for row in yield_checks),
    "kineticPeak": {"timeS": peak["time_s"], "joulesPerM": peak["kinetic_energy_j_per_m"]},
    "kineticFinalJPerM": history[-1]["kinetic_energy_j_per_m"],
    "motionWindows": {name: {"status": window["status"], "referenceTimeS": window["referenceTimeS"],
                            "final": window["states"][-1]} for name, window in review["motionWindows"].items()},
    "maximumToeMassFraction": max(row["totalMassFractionPastToePlusHalfH"] for row in review["toeHistory"]),
    "toeFinal": review["toeHistory"][-1], "boundaryReview": review["boundaryReview"],
    "coherentMotionDetected": review["coherentMotionDetected"],
    "landslideVerified": False, "scientificallyValidated": False,
    "visualInspection": {"image": record(REVIEW / "gravity-slope-review.png"),
        "coordinatesMagnification": 1,
        "finding": "Actual initial/final unnotched slope outlines remain almost coincident at scale1. Cohort motion plateaus after2s and kinetic energy falls. Native plastic history concentrates internally/toward toe; colour concentration alone does not establish a throughgoing sliding mechanism. Runout air remains empty."},
    "media": review["media"], "reviewExecution": load(REVIEW / "review-exit.json"),
    "analysisPreparedBeforeExecution": load(REVIEW / "analysis-pre-execution.json"),
    "summaryScript": record(Path(__file__))}
write("physical-spatial-review.json", summary)
print(json.dumps({key: summary[key] for key in ("savedStates", "materialCsvRows", "minimumSavedJ",
      "maximumSavedDisplacementM", "maximumSavedKappa", "maximumIndependentYieldResidualPa",
      "kineticPeak", "kineticFinalJPerM", "maximumToeMassFraction", "coherentMotionDetected")}, indent=2))
