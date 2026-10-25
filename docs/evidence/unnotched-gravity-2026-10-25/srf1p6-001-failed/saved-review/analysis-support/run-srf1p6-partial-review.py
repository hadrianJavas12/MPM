"""Freeze then execute the first saved-state-only partial SRF1.6 review."""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def record(path):
    payload = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest()}


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, value):
    if path.exists():
        raise RuntimeError(f"Preserve existing artifact: {path}")
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def now():
    return datetime.now(timezone.utc).isoformat()


def prepare(root):
    run = root / "output/unnotched-gravity-2026-10-25/srf1p6-001"
    review = run / "review-001"
    support = review / "analysis-support"
    if review.exists() or any(run.glob("review*")):
        raise RuntimeError("Fresh first-review directory required")
    support.mkdir(parents=True)
    inputs = [root / "scripts/review-gravity-slope.py", root / "scripts/plot_m5_cliff_comparison.py",
              root / "research/references/unnotched-mc-ssr/response-ladder-audit-contract.json",
              Path(__file__)]
    copies = []
    for source in inputs:
        target = support / source.name
        shutil.copyfile(source, target)
        if source.read_bytes() != target.read_bytes():
            raise RuntimeError("Analysis source copy mismatch")
        copies.append({"original": record(source), "copied": record(target)})
    command = [sys.executable, str(support / Path(__file__).name), "--frozen", str(run), str(review)]
    write(review / "orchestration-pre-execution.json", {
        "preparedUtc": now(), "copies": copies, "command": command,
        "scope": "First saved partial audit/video only; no solver, constitutive capsule or previous review execution"})
    return subprocess.run(command, cwd=root).returncode


def frozen(run, review):
    support = review / "analysis-support"
    manifest = load(run / "manifest.json")
    if manifest["complete"] or manifest["status"] == "complete":
        raise RuntimeError("This orchestration is explicitly partial-only")
    status_path = run.parent / f"{run.name}-status.json"
    worker_path = run.parent / f"{run.name}-detached/worker-exit.json"
    status, worker = load(status_path), load(worker_path)
    if status["status"] != "FAILED_NATIVE" or status["nativeExitCode"] != 1 or worker["exitCode"] != 1:
        raise RuntimeError("Expected recorded failed native and worker exits, not active native")
    before = [record(path) for path in sorted(support.iterdir()) if path.is_file()]
    command = [sys.executable, str(support / "review-gravity-slope.py"), "--run-dir", str(run),
               "--source-root", str(run / "source"), "--contract",
               str(support / "response-ladder-audit-contract.json"), "--output-dir", str(review), "--video"]
    write(review / "analysis-pre-execution.json", {"preparedUtc": now(), "sourceCopies": before,
          "command": command, "workingDirectory": str(run.parent.parent.parent),
          "expectedNativeComplete": False, "expectedReviewScope": "partial-saved-states-only",
          "reviewerExitConvention": "Unmodified reviewer returns0 for integrity PASS even if incomplete; orchestration maps successful partial review to2"})
    started = now()
    with (review / "review-execution.log").open("x", encoding="utf-8") as stream:
        process = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, text=True)
    after = [record(path) for path in sorted(support.iterdir()) if path.is_file()]
    if before != after:
        raise RuntimeError("Analysis input source changed during review")
    report = load(review / "review.json")
    partial_ok = (process.returncode == 0 and report.get("integrityStatus") == "PASS"
                  and report.get("nativeComplete") is False and "mediaError" not in report)
    code = 2 if partial_ok else 1
    write(review / "review-exit.json", {"startedUtc": started, "finishedUtc": now(),
          "reviewerExitCode": process.returncode, "orchestrationExitCode": code,
          "nativeExitCode": status["nativeExitCode"], "workerExitCode": worker["exitCode"],
          "nativeComplete": report.get("nativeComplete"), "savedScope": report.get("savedScope"),
          "integrityStatus": report.get("integrityStatus"), "allAnalysisSourcesUnchanged": True,
          "sourceCopiesBefore": before, "sourceCopiesAfter": after,
          "scope": "Exit2 marks successfully reviewed incomplete saved states; no completion requirement weakened"})
    source_rows = load(run / "source/source-manifest.json")["files"]
    verified = []
    for row in source_rows:
        source = (run / row["path"]).resolve()
        if not source.is_relative_to((run / "source").resolve()):
            raise RuntimeError("Native source escaped frozen root")
        actual = record(source)
        if (actual["sha256"], actual["bytes"]) != (row["sha256"], row["bytes"]):
            raise RuntimeError("Native source terminal hash mismatch")
        verified.append({"path": row["path"], "bytes": actual["bytes"], "sha256": actual["sha256"]})
    provenance = load(run / "source-provenance.json")
    dll = next(row for row in verified if row["path"] == "source/libs/kirchoff.dll")
    backend = provenance["nativeBackend"]
    if not (len(verified) == 282 and provenance["sourceSnapshotExactLoadedBytes"]
            and provenance["copiedByteEqualityBeforeLoad"] and backend["sha256"] == dll["sha256"]
            and backend["verifiedBy"] == "GetModuleHandleW/GetModuleFileNameW"):
        raise RuntimeError("Recorded source/native DLL proof mismatch")
    write(review / "source-files-terminal-verification.json", {"sourceFiles": len(verified), "allMatched": True,
          "files": verified, "actualMappedDll": backend, "sourceManifest": record(run / "source/source-manifest.json"),
          "runtimeProvenance": record(run / "source-provenance.json"), "nativeStatus": status,
          "workerExit": worker, "verificationScript": record(Path(__file__)),
          "scope": "Terminal immutable-file hashes and retained native loading proof; no native/replay rerun"})
    if partial_ok:
        with (run / "history.csv").open(encoding="utf-8-sig", newline="") as stream:
            rows = [{key: float(value.lower().replace("d", "e")) for key, value in row.items()}
                    for row in csv.DictReader(stream)]
        yield_rows = [check for frame in report["frameIntegrity"] for check in frame["checks"]
                      if check["name"] == "six-plane-current-state-admissibility"]
        peak = max(rows, key=lambda row: row["kinetic_energy_j_per_m"])
        summary = {"nativeComplete": False, "nativeExitCode": 1, "workerExitCode": 1,
                   "scope": "Actual saved states0 through1.7s only; manifest updates include later unsaved work",
                   "savedFrames": report["savedFrames"], "lastSavedTimeS": report["lastSavedTimeS"],
                   "particlesPerState": manifest["particleCount"],
                   "materialCsvRows": manifest["particleCount"] * report["savedFrames"],
                   "manifestUpdatesIncludingUnsaved": manifest["updates"],
                   "lastSavedUpdates": rows[-1]["updates"], "integrityStatus": report["integrityStatus"],
                   "initialMassKgPerM": rows[0]["mass_kg_per_m"],
                   "minimumSavedJ": min(row["min_J"] for row in rows),
                   "maximumSavedDisplacementM": max(row["max_displacement_m"] for row in rows),
                   "maximumSavedSpeedMPerS": max(row["max_speed_m_per_s"] for row in rows),
                   "maximumSavedKappa": max(row["max_kappa"] for row in rows),
                   "maximumIndependentYieldResidualPa": max(row["maximumYieldResidualPa"] for row in yield_rows),
                   "kineticPeak": {"timeS": peak["time_s"], "joulesPerM": peak["kinetic_energy_j_per_m"]},
                   "kineticLastSavedJPerM": rows[-1]["kinetic_energy_j_per_m"],
                   "finalHistory": rows[-1], "boundaryReview": report["boundaryReview"],
                   "motionWindows": {name: {"status": window["status"], "reason": window.get("reason"),
                       "referenceTimeS": window.get("referenceTimeS"),
                       "final": window.get("states", [None])[-1]} for name, window in report["motionWindows"].items()},
                   "maximumToeMassFraction": max(row["totalMassFractionPastToePlusHalfH"] for row in report["toeHistory"]),
                   "toeLastSaved": report["toeHistory"][-1], "media": report["media"],
                   "coherentMotionDetectedInPartialStates": report["coherentMotionDetected"],
                   "landslideVerified": False, "scientificallyValidated": False,
                   "visualInspection": "PENDING actual PNG inspection; metrics alone do not certify a failure mechanism",
                   "fullMPReplay": "NOT_EXECUTED; principal failure capsule is not a whole-MP transaction checkpoint"}
        write(review / "physical-spatial-review.json", summary)
    print(json.dumps({"review": str(review), "reviewerExit": process.returncode, "partialScopeExit": code,
                      "integrity": report.get("integrityStatus"), "savedFrames": report.get("savedFrames"),
                      "lastSavedTimeS": report.get("lastSavedTimeS"), "sourceFilesVerified": len(verified)}))
    return code


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--frozen":
        sys.exit(frozen(Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()))
    sys.exit(prepare(Path(__file__).resolve().parents[1]))
