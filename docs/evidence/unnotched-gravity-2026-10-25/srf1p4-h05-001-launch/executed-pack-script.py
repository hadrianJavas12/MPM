"""Read/copy/hash the h0.5 launch and stored live proof; no process requery."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "output/unnotched-gravity-2026-10-25"
NAME = "srf1p4-h05-001"
RUN = RAW / NAME
COARSE = RAW / "srf1p4-002"
PACKET = ROOT / "docs/evidence/unnotched-gravity-2026-10-25/srf1p4-h05-001-launch"
COMMIT = "1a9f29a85cf268cf812d0e2e4ce99473e19098a6"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def record(path, relative_to=None):
    payload = path.read_bytes()
    return {"path": path.relative_to(relative_to).as_posix() if relative_to else str(path),
            "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}


def retain(source, target):
    if target.exists():
        raise RuntimeError(f"Refuse overwrite: {target}")
    payload = source.read_bytes()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    if payload != target.read_bytes():
        raise RuntimeError("Copy mismatch")


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def main():
    if PACKET.exists() or not PACKET.resolve().is_relative_to(ROOT.resolve()):
        raise RuntimeError("Packet must be fresh within workspace")
    manifest = read_json(RUN / "source/source-manifest.json")
    sources = {row["path"]: row for row in manifest["files"]}
    old_sources = {row["path"]: row for row in read_json(COARSE / "source/source-manifest.json")["files"]}
    if len(sources) != 282 or set(sources) != set(old_sources):
        raise RuntimeError("Unexpected source set")
    verified = []
    for relative, expected in sorted(sources.items()):
        path = (RUN / relative).resolve()
        if not path.is_relative_to((RUN / "source").resolve()):
            raise RuntimeError("Source escapes snapshot")
        actual = record(path)
        if (actual["sha256"], actual["bytes"]) != (expected["sha256"], expected["bytes"]):
            raise RuntimeError(f"Copied source mismatch: {relative}")
        verified.append({"path": relative, "bytes": actual["bytes"], "sha256": actual["sha256"]})
    changed = [key for key in sorted(sources) if sources[key]["sha256"] != old_sources[key]["sha256"]]
    if changed != ["source/case.lisp"]:
        raise RuntimeError(f"Unexpected source differences: {changed}")
    case = ROOT / "cases/benchmarks/gravity-slope-mc-srf-1p4-h05.lisp"
    coarse_case = ROOT / "cases/benchmarks/gravity-slope-mc-srf-1p4.lisp"
    if case.read_bytes() != (RUN / "source/case.lisp").read_bytes():
        raise RuntimeError("Current fine case differs from executed bytes")
    coarse_bytes = coarse_case.read_bytes()
    if (coarse_bytes.count(b":mesh-size 1d0") != 1
            or coarse_bytes.replace(b":mesh-size 1d0", b":mesh-size .5d0", 1) != case.read_bytes()
            or coarse_bytes != (COARSE / "source/case.lisp").read_bytes()):
        raise RuntimeError("Only mesh literal should differ in exact physical recipes")
    provenance = read_json(RUN / "source-provenance.json")
    backend = provenance["nativeBackend"]
    if not (provenance["sourceSnapshotExactLoadedBytes"] and provenance["copiedByteEqualityBeforeLoad"]
            and set(provenance["copiedFiles"]) == set(sources)
            and backend["verifiedBy"] == "GetModuleHandleW/GetModuleFileNameW"
            and backend["sha256"] == sources["source/libs/kirchoff.dll"]["sha256"]):
        raise RuntimeError("Actual loaded source/DLL proof is inconsistent")
    live = read_json(RAW / f"{NAME}-live-process-verification.json")
    roles = {row["role"]: row for row in live["processes"]}
    if (set(roles) != {"wrapper", "nativeCommand", "sbcl", "detachedWorker"}
            or not all(row["identityMatched"] for row in roles.values())
            or roles["wrapper"]["parentPid"] != roles["detachedWorker"]["pid"]
            or roles["nativeCommand"]["parentPid"] != roles["wrapper"]["pid"]
            or roles["sbcl"]["parentPid"] != roles["nativeCommand"]["pid"]
            or live["sourceCommit"] != COMMIT):
        raise RuntimeError("Stored full live chain proof invalid")
    helper = ROOT / ".tmp/capture-gravity-h05-processes.ps1"
    original = (ROOT / ".tmp/capture-gravity-baseline-processes.ps1").read_bytes()
    if original.replace(b"$taskRun='output/unnotched-gravity-2026-10-25/srf1-001'",
                        b"$taskRun='output/unnotched-gravity-2026-10-25/srf1p4-h05-001'", 1) != helper.read_bytes():
        raise RuntimeError("Helper changed beyond run path")
    PACKET.mkdir(parents=True)
    (PACKET / ".gitattributes").write_bytes(b"* -text\n")
    retain(Path(__file__), PACKET / "executed-pack-script.py")
    retain(helper, PACKET / "proof-support/executed-capture-gravity-h05-processes.ps1")
    for relative in ("source/source-manifest.json", "source/case.lisp", "source-provenance.json", "manifest.json"):
        retain(RUN / relative, PACKET / relative)
    for suffix in ("-launch.json", "-status.json", "-live-process-verification.json", "-live-proof-initial-failure.json", ".stdout.log", ".stderr.log"):
        retain(RAW / (NAME + suffix), PACKET / "runtime" / (NAME + suffix))
    detached = RAW / (NAME + "-detached")
    for path in sorted(detached.rglob("*")):
        if path.is_file():
            retain(path, PACKET / "detached" / path.relative_to(detached))
    contracts = []
    for filename in ("contract.json", "refinement-contract.json", "refinement-audit-contract.json"):
        relative = f"research/references/unnotched-mc-ssr/{filename}"
        path = ROOT / relative
        blob = subprocess.run(["git", "show", f"{COMMIT}:{relative}"], cwd=ROOT, check=True, capture_output=True).stdout
        if blob != path.read_bytes():
            raise RuntimeError(f"Contract not exact launch commit bytes: {filename}")
        retain(path, PACKET / "protocol" / filename)
        contracts.append({**record(path), "matchesLaunchCommitGitBlobExactly": True})
    for relative in ("docs/evidence/unnotched-gravity-2026-10-25/refinement-controls/summary.json",
                     "docs/evidence/unnotched-gravity-2026-10-25/refinement-controls/result.json",
                     "docs/evidence/unnotched-gravity-2026-10-25/refinement-controls/artifact-index.json",
                     "output/unnotched-gravity-2026-10-25/refinement-controls-root-verification.json"):
        path = ROOT / relative
        retain(path, PACKET / "prelaunch-gates" / path.name)
    captured = read_json(PACKET / "manifest.json")
    coarse_config = read_json(COARSE / "manifest.json")["config"]
    differences = [{"key": key, "coarse": coarse_config[key], "fine": value}
                   for key, value in captured["config"].items() if value != coarse_config[key]]
    if differences != [{"key": "meshSize", "coarse": 1.0, "fine": 0.5}]:
        raise RuntimeError(f"Unexpected actual configuration change: {differences}")
    protocol = read_json(PACKET / "protocol/refinement-contract.json")
    audit = read_json(PACKET / "protocol/refinement-audit-contract.json")
    if not (captured["particleCount"] == audit["expectedParticleCount"] == 3520
            and audit["numerics"]["meshSizeM"] == 0.5
            and audit["sourceContracts"]["refinementStudy"]["sha256"] == record(PACKET / "protocol/refinement-contract.json")["sha256"]):
        raise RuntimeError("Declared fine protocol differs from actual run")
    write_json(PACKET / "source-and-case-verification.json", {
        "capturedUtc": datetime.now(timezone.utc).isoformat(), "sourceFilesVerified": len(verified),
        "allSourceManifestHashesAndLengthsMatch": True, "files": verified,
        "identicalSourcesWithCompletedCoarse1p4": len(sources)-1, "onlyChangedSource": changed,
        "exactCaseOnlyMeshLiteralChanged": True, "actualCompiledConfigurationDifferences": differences,
        "actualMappedDll": backend, "protocols": contracts,
        "fullSourceArchive": "DEFERRED_UNTIL_TERMINAL; immutable complete sources remain under output"})
    write_json(PACKET / "metre-observer-protocol-status.json", {
        "status": "FROZEN_PROTOCOL_ONLY_IMPLEMENTATION_TESTS_PENDING_AT_CAPTURE",
        "source": contracts[1], "comparisonObserver": protocol["comparisonObserver"],
        "nativeAuditRole": audit["refinementRole"],
        "limits": "No executed metre-observer test/result existed at capture. Do not infer observer verification from native mesh/input gates or reinterpret h-scaled diagnostics as cross-mesh success."})
    launch = read_json(PACKET / "runtime" / f"{NAME}-launch.json")
    write_json(PACKET / "summary.json", {
        "schema": "cl-mpm.unnotched-gravity.refinement-launch-evidence.v1", "status": "LAUNCH_PROOF_ONLY",
        "sourceCommit": COMMIT, "startedUtc": launch["startedUtc"], "wallDeadlineUtc": launch["wallDeadlineUtc"],
        "maxWallHours": launch["maxWallHours"], "storedLiveProofCapturedUtc": live["capturedUtc"],
        "storedLiveProcesses": roles, "processesRecapturedByPackager": False,
        "capturedNativeState": {key: captured.get(key) for key in ("status", "phase", "timeS", "updates", "savedFrames", "complete")},
        "sourceCount": len(sources), "actualConfigDifferences": differences,
        "physicalObserverImplementationStatus": "PENDING_AT_CAPTURE; protocol frozen in launch commit",
        "initialProofHelperFailureRetained": True,
        "initialFailureScope": "Proof helper called before nativeCommand/SBCL identities populated, Id=null binding failure; wrapper may already have been queried; exact partial unreturned process records not fabricated. No solver effect.",
        "landslideVerified": False, "scientificallyValidated": False,
        "limits": "Stored live identity applies only to its timestamp; mutable state/logs captured separately, not atomically. User-session worker has no demonstrated sleep/logoff/reboot immunity. Launch does not establish motion or completion.",
        "packagingOperations": "Read/copy/hash only; no new process query, replay, native test, solver, rendering or result analysis by this packager."})
    (PACKET / "README.md").write_text(
        "# h0.5 same-physics refinement: launch proof only\n\n"
        "The refined native run starts25October14:53:10WIB, source1a9f29a, with3h wall budget to17:53:10WIB. "
        "All282 immutable source/input/DLL files match their manifest and actual mapped backend proof. "
        "Only the exact case file differs from completed coarse SRF1.40: meshSize1m becomes0.5m. "
        "The actual compiled configuration differs only in meshSize;3520 particles are present. "
        "Stable timestep consequently changes, so this is coupled space/time refinement, not isolated mesh convergence.\n\n"
        "The original copied live helper's run-path replacement is the only helper change. Its successful full "
        "PID/session/original-clock/parent-chain capture is retained. One earlier helper invocation encountered "
        "unpopulated nativeCommand/SBCL identities and failed on Id=null; its error is retained and did not restart the solver. "
        "Packaging does not query processes again. Status/manifest/log snapshots have separate capture times.\n\n"
        "Study, refinement and fine-audit contracts match launch commit bytes exactly. The physical metre observer "
        "is a frozen protocol only at capture: its implementation/tests were still pending, and no fabricated "
        "observer PASS is included. Native h-scaled diagnostics remain separately identified. Pre-launch native "
        "mesh/input/bounded-output gate summaries and their index/root verification are included.\n\n"
        "No full source ZIP is made at launch; immutable originals remain under output for terminal packaging. "
        "This is not completed native, coherent-slide, runout or scientific validation evidence. "
        "No sleep/logoff/reboot immunity is proved; * -text preserves artifact bytes.\n",
        encoding="utf-8", newline="\n")
    artifacts = [record(path, PACKET) for path in sorted(PACKET.rglob("*")) if path.is_file()]
    write_json(PACKET / "artifact-index.json", {"schema": "cl-mpm.evidence.artifact-index.v1", "artifacts": artifacts,
               "note": "Index excludes itself; verify staged Git blob bytes before commit"})
    for row in artifacts:
        if record(PACKET / row["path"], PACKET) != row:
            raise RuntimeError("Indexed payload changed")
    print(json.dumps({"packet": str(PACKET), "status": "LAUNCH_PROOF_ONLY", "indexedArtifacts": len(artifacts),
                      "sourceFilesVerified": len(sources), "physicalObserverImplementationStatus": "PENDING_AT_CAPTURE",
                      "actualConfigDifferences": differences, "liveProofCapturedUtc": live["capturedUtc"]}))


if __name__ == "__main__":
    main()
