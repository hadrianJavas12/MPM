"""Retain existing launch proof and immutable source metadata; no process queries."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "output/unnotched-gravity-2026-10-25"
RUN = RAW / "srf1p4-002"
OLD = ROOT / "output/unnotched-gravity-2026-10-24/srf1p4-001"
PACKET = ROOT / "docs/evidence/unnotched-gravity-2026-10-25/srf1p4-002-launch"


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def record(path, root=None):
    payload = path.read_bytes()
    return {"path": path.relative_to(root).as_posix() if root else str(path),
            "sha256": digest(payload), "bytes": len(payload)}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def retain(source, destination):
    # A running wrapper may update status/manifest between separate copies.
    # Read each file once, retain exactly those bytes, and label capture time;
    # do not fabricate simultaneous status or recapture any live process.
    if destination.exists():
        raise RuntimeError(f"Refuse overwrite: {destination}")
    payload = source.read_bytes()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    if destination.read_bytes() != payload:
        raise RuntimeError(f"Retained byte mismatch: {source}")


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                    encoding="utf-8", newline="\n")


def main():
    if PACKET.exists() or not PACKET.resolve().is_relative_to(ROOT.resolve()):
        raise RuntimeError("Launch packet must be fresh and inside workspace")
    old_manifest = read_json(OLD / "source/source-manifest.json")
    new_manifest = read_json(RUN / "source/source-manifest.json")
    old_sources = {row["path"]: row for row in old_manifest["files"]}
    new_sources = {row["path"]: row for row in new_manifest["files"]}
    if len(new_sources) != 282 or set(old_sources) != set(new_sources):
        raise RuntimeError("Unexpected launch source set/count")
    verified = []
    for relative, expected in sorted(new_sources.items()):
        path = (RUN / relative).resolve()
        if not path.is_relative_to((RUN / "source").resolve()):
            raise RuntimeError("Source entry escaped immutable source directory")
        actual = record(path)
        if (actual["sha256"], actual["bytes"]) != (expected["sha256"], expected["bytes"]):
            raise RuntimeError(f"Copied immutable source mismatch: {relative}")
        verified.append({"path": relative, "bytes": actual["bytes"], "sha256": actual["sha256"], "matchesManifest": True})
    changed = [{"path": relative, "oldFailedSha256": old_sources[relative]["sha256"],
                "newFixedSha256": entry["sha256"]}
               for relative, entry in sorted(new_sources.items())
               if entry["sha256"] != old_sources[relative]["sha256"]]
    expected_change = "source/materials/models/plastic/mohr-coulomb-evolution/projection.lisp"
    if [row["path"] for row in changed] != [expected_change]:
        raise RuntimeError(f"Unexpected executed source changes: {changed}")
    old_case, new_case = OLD / "source/case.lisp", RUN / "source/case.lisp"
    if old_case.read_bytes() != new_case.read_bytes():
        raise RuntimeError("Exact physical case changed between full attempts")
    provenance = read_json(RUN / "source-provenance.json")
    backend = provenance["nativeBackend"]
    if not (provenance["sourceSnapshotExactLoadedBytes"] and provenance["copiedByteEqualityBeforeLoad"]
            and set(provenance["copiedFiles"]) == set(new_sources)
            and backend["verifiedBy"] == "GetModuleHandleW/GetModuleFileNameW"
            and backend["sha256"] == new_sources["source/libs/kirchoff.dll"]["sha256"]):
        raise RuntimeError("Actual frozen-source/mapped-DLL runtime proof differs")
    live = read_json(RAW / "srf1p4-002-live-process-verification.json")
    roles = {row["role"]: row for row in live["processes"]}
    if (set(roles) != {"wrapper", "nativeCommand", "sbcl", "detachedWorker"}
            or not all(row["identityMatched"] for row in roles.values())
            or roles["nativeCommand"]["parentPid"] != roles["wrapper"]["pid"]
            or roles["sbcl"]["parentPid"] != roles["nativeCommand"]["pid"]
            or roles["wrapper"]["parentPid"] != roles["detachedWorker"]["pid"]):
        raise RuntimeError("Stored exact live identity/parent chain proof is inconsistent")
    PACKET.mkdir(parents=True)
    (PACKET / ".gitattributes").write_bytes(b"* -text\n")
    retain(Path(__file__), PACKET / "executed-pack-script.py")
    retain(ROOT / ".tmp/capture-gravity-processes.ps1", PACKET / "proof-support/capture-gravity-processes.ps1")
    for name in ("source/source-manifest.json", "source/case.lisp", "source-provenance.json", "manifest.json"):
        retain(RUN / name, PACKET / name)
    for suffix in ("-launch.json", "-status.json", "-live-process-verification.json",
                   "-live-proof-initial-failure.json", "-live-proof-clock-failure.json"):
        retain(RAW / ("srf1p4-002" + suffix), PACKET / "runtime" / ("srf1p4-002" + suffix))
    detached = RAW / "srf1p4-002-detached"
    for source in sorted(detached.rglob("*")):
        if source.is_file():
            retain(source, PACKET / "detached" / source.relative_to(detached))
    captured_manifest = read_json(PACKET / "manifest.json")
    old_config = read_json(OLD / "manifest.json")["config"]
    if captured_manifest["config"] != old_config:
        raise RuntimeError("Physical/numerical configuration changed between full attempts")
    write_json(PACKET / "source-and-case-verification.json", {
        "capturedUtc": datetime.now(timezone.utc).isoformat(), "sourceFilesVerified": len(verified),
        "allSourceManifestHashesAndLengthsMatch": True, "files": verified,
        "oldFailedSourceManifest": record(OLD / "source/source-manifest.json"),
        "newExecutedSourceManifest": record(RUN / "source/source-manifest.json"),
        "identicalSourceEntries": len(verified) - len(changed), "changedExecutedSourceEntries": changed,
        "exactCaseBytesUnchanged": True, "case": record(new_case),
        "allPhysicalAndNumericalConfigValuesUnchanged": True, "config": captured_manifest["config"],
        "actualMappedDll": backend,
        "sourceArchiveStatus": "NOT_CREATED_AT_LAUNCH; full sources remain immutable under output and will be archived at terminal state"})
    write_json(PACKET / "summary.json", {
        "schema": "cl-mpm.unnotched-gravity.relaunch-evidence.v1",
        "status": "LAUNCH_PROOF_ONLY", "sourceCommit": live["sourceCommit"],
        "storedLiveVerificationCapturedUtc": live["capturedUtc"],
        "storedLiveProcesses": roles, "liveProcessesRecapturedByPackager": False,
        "nativeComplete": False, "landslideVerified": False, "scientificallyValidated": False,
        "savedManifestScopeAtCopy": {key: captured_manifest.get(key) for key in ("status", "phase", "timeS", "savedFrames", "updates")},
        "sourceCount": len(verified), "sourceDifference": changed,
        "twoProofHarnessFailuresRetained": True,
        "failureScope": "Datetime conversion and CIM-vs-GetProcess clock mismatch are proof-helper failures; solver was not restarted. Successful helper compares exact PID/session/ticks using each record's original clock.",
        "proofHelperSource": record(PACKET / "proof-support/capture-gravity-processes.ps1", PACKET),
        "proofHelperSourceScope": "Retained successful executed helper; historical failed-helper versions are not claimed reconstructed.",
        "limits": "Stored live proof establishes identities at its own capture timestamp only. Mutable status/manifest copied separately, not a simultaneous new live check. WMI user-session worker is not proved immune to sleep/logoff/reboot.",
        "packagingOperations": "Read/copy/hash metadata only. No process query, solver, monitor, replay, rendering or scientific review run."})
    (PACKET / "README.md").write_text(
        "# Same-input SRF1.40 relaunch: launch proof only\n\n"
        "This packet retains the fresh native launch at25October03:57WIB, source3ed36a3, and the existing exact "
        "live-process proof captured at03:58:58WIB. It does not contain a completed simulation or evidence of landslide. "
        "The packager performs no new process query or solver/monitor/analysis run. Separate mutable status/manifest "
        "copies describe their own saved states, not a newly synchronized live check.\n\n"
        "All282 immutable executed source files match their manifest SHA256 and byte lengths. "
        "The sole source change from the failed001 snapshot is the scoped MC projection fix. "
        "The actual case bytes and every physical/numerical configuration value are unchanged, including SRF1.40, "
        "gravity-only smooth2s ramp,6s duration,61 states, grid/PPC, strength, dilation, damping and mass scale. "
        "Native provenance identifies the loaded frozen sources and actual mapped DLL. The full source archive "
        "is deferred until native terminal state; immutable originals remain under output/.\n\n"
        "Two earlier proof-helper failures are retained verbatim: datetime conversion lost UTC/subsecond identity, "
        "then a CIM microsecond timestamp was compared with a Get-Process100ns clock. Neither restarted the solver. "
        "The successful helper retains exact equality using each original clock and checks PID/session/parent chain. "
        "Its executed source is included; old failed-helper source versions are not fabricated.\n\n"
        "A live identity at the recorded timestamp does not guarantee later process health or survival of sleep, "
        "logoff or reboot. Full-ramp completion, coherent motion, runout and scientific agreement remain unverified.\n",
        encoding="utf-8", newline="\n")
    artifacts = [record(path, PACKET) for path in sorted(PACKET.rglob("*")) if path.is_file()]
    write_json(PACKET / "artifact-index.json", {"schema": "cl-mpm.evidence.artifact-index.v1", "artifacts": artifacts,
               "note": "Index excludes itself; * -text preserves retained bytes. Verify staged Git blobs before commit."})
    for expected in artifacts:
        if record(PACKET / expected["path"], PACKET) != expected:
            raise RuntimeError("Retained launch artifact changed during packaging")
    print(json.dumps({"packet": str(PACKET), "indexedArtifacts": len(artifacts),
                      "sourceFilesVerified": len(verified), "changedSourceEntries": len(changed),
                      "status": "LAUNCH_PROOF_ONLY"}, indent=2))


if __name__ == "__main__":
    main()
