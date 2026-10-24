"""Retain the existing baseline launch/live identity proof; no process requery."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "output/unnotched-gravity-2026-10-25"
RUN = RAW / "srf1-001"
PAIRED = RAW / "srf1p4-002"
PACKET = ROOT / "docs/evidence/unnotched-gravity-2026-10-25/srf1-001-launch"


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def record(path, relative_to=None):
    payload = path.read_bytes()
    return {"path": path.relative_to(relative_to).as_posix() if relative_to else str(path),
            "bytes": len(payload), "sha256": sha(payload)}


def retain(source, target):
    if target.exists():
        raise RuntimeError(f"Refuse overwrite: {target}")
    payload = source.read_bytes()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    if target.read_bytes() != payload:
        raise RuntimeError("Retained bytes changed")


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def main():
    if PACKET.exists() or not PACKET.resolve().is_relative_to(ROOT.resolve()):
        raise RuntimeError("Baseline launch packet must be fresh within workspace")
    baseline = read_json(RUN / "source/source-manifest.json")
    paired = read_json(PAIRED / "source/source-manifest.json")
    sources = {row["path"]: row for row in baseline["files"]}
    other = {row["path"]: row for row in paired["files"]}
    if len(sources) != 282 or set(sources) != set(other):
        raise RuntimeError("Unexpected executed source set")
    verified = []
    for relative, row in sorted(sources.items()):
        path = (RUN / relative).resolve()
        if not path.is_relative_to((RUN / "source").resolve()):
            raise RuntimeError("Source path escapes snapshot")
        actual = record(path)
        if (actual["sha256"], actual["bytes"]) != (row["sha256"], row["bytes"]):
            raise RuntimeError(f"Source bytes differ: {relative}")
        verified.append({"path": relative, "bytes": actual["bytes"], "sha256": actual["sha256"]})
    differences = [relative for relative in sorted(sources) if sources[relative]["sha256"] != other[relative]["sha256"]]
    if differences != ["source/case.lisp"]:
        raise RuntimeError(f"Unexpected paired source changes: {differences}")
    case = ROOT / "cases/benchmarks/gravity-slope-mc-srf-1.lisp"
    if case.read_bytes() != (RUN / "source/case.lisp").read_bytes():
        raise RuntimeError("Executed baseline case differs from reviewed input")
    matrix = read_json(RAW / "baseline-input-comparison.json")
    if matrix["baselineCase"]["sha256"] != sources["source/case.lisp"]["sha256"]:
        raise RuntimeError("Pre-launch baseline matrix case differs")
    provenance = read_json(RUN / "source-provenance.json")
    backend = provenance["nativeBackend"]
    if not (provenance["sourceSnapshotExactLoadedBytes"] and provenance["copiedByteEqualityBeforeLoad"]
            and set(provenance["copiedFiles"]) == set(sources)
            and backend["verifiedBy"] == "GetModuleHandleW/GetModuleFileNameW"
            and backend["sha256"] == sources["source/libs/kirchoff.dll"]["sha256"]):
        raise RuntimeError("Loaded source/DLL runtime proof differs")
    live = read_json(RAW / "srf1-001-live-process-verification.json")
    roles = {row["role"]: row for row in live["processes"]}
    if (set(roles) != {"wrapper", "nativeCommand", "sbcl", "detachedWorker"}
            or not all(row["identityMatched"] for row in roles.values())
            or roles["wrapper"]["parentPid"] != roles["detachedWorker"]["pid"]
            or roles["nativeCommand"]["parentPid"] != roles["wrapper"]["pid"]
            or roles["sbcl"]["parentPid"] != roles["nativeCommand"]["pid"]):
        raise RuntimeError("Stored exact live parent/creation identity proof is invalid")
    original_helper = (ROOT / ".tmp/capture-gravity-processes.ps1").read_bytes()
    helper = ROOT / ".tmp/capture-gravity-baseline-processes.ps1"
    replacement = original_helper.replace(
        b"$taskRun='output/unnotched-gravity-2026-10-25/srf1p4-002'",
        b"$taskRun='output/unnotched-gravity-2026-10-25/srf1-001'", 1)
    if replacement != helper.read_bytes():
        raise RuntimeError("Baseline helper changed more than the run path")
    PACKET.mkdir(parents=True)
    (PACKET / ".gitattributes").write_bytes(b"* -text\n")
    retain(Path(__file__), PACKET / "executed-pack-script.py")
    retain(helper, PACKET / "proof-support/executed-capture-gravity-baseline-processes.ps1")
    retain(RAW / "baseline-input-comparison.json", PACKET / "baseline-input-comparison.json")
    for name in ("source/source-manifest.json", "source/case.lisp", "source-provenance.json", "manifest.json"):
        retain(RUN / name, PACKET / name)
    for suffix in ("-launch.json", "-status.json", "-live-process-verification.json"):
        retain(RAW / ("srf1-001" + suffix), PACKET / "runtime" / ("srf1-001" + suffix))
    detached = RAW / "srf1-001-detached"
    for path in sorted(detached.rglob("*")):
        if path.is_file():
            retain(path, PACKET / "detached" / path.relative_to(detached))
    captured = read_json(PACKET / "manifest.json")
    if captured["config"] != matrix["expectedBaselineConfiguration"]:
        raise RuntimeError("Actual baseline configuration differs from pre-launch derivation")
    config_differences = [key for key in captured["config"]
                          if captured["config"][key] != read_json(PAIRED / "manifest.json")["config"][key]]
    if set(config_differences) != {"strengthReductionFactor", "cohesionPa", "frictionRad"}:
        raise RuntimeError("Undeclared paired physical/numerical change")
    write_json(PACKET / "source-and-case-verification.json", {
        "capturedUtc": datetime.now(timezone.utc).isoformat(), "sourceFilesVerified": len(sources),
        "allSourceManifestHashesAndLengthsMatch": True, "files": verified,
        "pairedCompletedSourceManifest": record(PAIRED / "source/source-manifest.json"),
        "identicalSourceEntriesWithCompletedSRF1p4": len(sources)-len(differences),
        "onlyDifferentSourceEntry": differences, "executedBaselineCaseMatchesCurrentAndPreLaunchMatrix": True,
        "actualConfigMatchesPreLaunchDerivedExpectedConfig": True,
        "onlyCompiledConfigDifferencesWithCompletedSRF1p4": config_differences,
        "actualMappedDll": backend,
        "sourceArchiveStatus": "NOT_CREATED_AT_LAUNCH; immutable source copies retained under output for terminal archive"})
    write_json(PACKET / "summary.json", {
        "schema": "cl-mpm.unnotched-gravity.baseline-launch-evidence.v1",
        "status": "LAUNCH_PROOF_ONLY", "sourceCommit": live["sourceCommit"],
        "liveProofCapturedUtc": live["capturedUtc"], "storedLiveProcesses": roles,
        "processesRecapturedByPackager": False,
        "capturedNativeState": {key: captured.get(key) for key in ("status", "phase", "timeS", "updates", "savedFrames", "complete")},
        "scientificallyValidated": False, "landslideVerified": False,
        "preLaunchMatrixProvenance": "Original JSON retained exactly; it was generated by inline Python tool invocation. Its exact executed script was not separately retained as a filesystem file and is not reconstructed here.",
        "liveHelperScope": "Separate copied helper changed only the run-path binding. Exact PID/session/creation ticks use original Process clock for wrapper/cmd/SBCL and original CIM clock for worker; parent chain checked once.",
        "limits": "Live identity proof applies at its own timestamp. Mutable manifest/status are copied separately. No sleep/logoff/reboot immunity, completion, landslide or calibrated runout guarantee.",
        "operations": "Read/copy/hash only; no new process query, input gate, projector, solver, rendering or physical review by this packager."})
    (PACKET / "README.md").write_text(
        "# SRF1 sequential baseline: launch proof only\n\n"
        "The predeclared unnotched SRF1 control uses the same recipe and production sources as completed SRF1.40. "
        "Only SRF, reduced cohesion and reduced friction differ. The exact baseline case matches all previous frozen input gates "
        "and the pre-launch hash matrix; the actual compiled configuration also matches its derived expectation.\n\n"
        "All282 copied source/input/DLL files match pre-load manifest hashes and lengths, with actual mapped DLL proof retained. "
        "Only source/case.lisp differs from the paired SRF1.40 snapshot. Full immutable sources stay under output for terminal packaging.\n\n"
        "The separate copied live helper checks PID/session/creation time and parent chain once. It preserves the established "
        "Process timestamp clock for wrapper/cmd/SBCL and CIM clock for the detached worker. Packaging does not query processes again. "
        "Mutable status/manifest copies are not falsely presented as simultaneous with the stored live check.\n\n"
        "The pre-launch matrix JSON is retained byte for byte. Its original inline Python invocation was not saved as a separate "
        "script file; this packet does not invent an executed historical script. The executed live helper and packer are retained exactly.\n\n"
        "This packet establishes a native launch, not completion or landslide. No additional solver/input test/replay/render ran "
        "for packaging, and no survival of sleep/logoff/reboot is guaranteed. Raw bytes are preserved by * -text.\n",
        encoding="utf-8", newline="\n")
    artifacts = [record(path, PACKET) for path in sorted(PACKET.rglob("*")) if path.is_file()]
    write_json(PACKET / "artifact-index.json", {"schema": "cl-mpm.evidence.artifact-index.v1", "artifacts": artifacts,
               "note": "Index excludes itself; verify staged Git bytes before commit."})
    for row in artifacts:
        if record(PACKET / row["path"], PACKET) != row:
            raise RuntimeError("Indexed artifact changed")
    print(json.dumps({"packet": str(PACKET), "status": "LAUNCH_PROOF_ONLY", "artifacts": len(artifacts),
                      "verifiedSources": len(sources), "actualConfigDifferences": config_differences,
                      "liveProofCapturedUtc": live["capturedUtc"]}))


if __name__ == "__main__":
    main()
