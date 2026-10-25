"""Archive SRF1.6 launch and one existing live proof; no process re-query."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "output/unnotched-gravity-2026-10-25"
NAME = "srf1p6-001"
RUN = RAW / NAME
COARSE = RAW / "srf1p4-002"
COMMIT = "b079f050c5c665640e5c479384938b3c7b1d0e53"
PACKET = ROOT / f"docs/evidence/unnotched-gravity-2026-10-25/{NAME}-launch"
HELPER = ROOT / ".tmp/pack-gravity-completed-002.py"


def main():
    if PACKET.exists():
        raise RuntimeError("Preserve earlier packet; use a fresh destination")
    spec = importlib.util.spec_from_file_location("_copy_helpers", HELPER)
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)  # Definitions only; its guarded main is not run.
    h.RUN, h.PACKET = RUN, PACKET
    source_members = h.immutable_sources()
    source_rows = h.read_json(RUN / "source/source-manifest.json")["files"]
    old = {row["path"]: row for row in h.read_json(COARSE / "source/source-manifest.json")["files"]}
    actual = {row["path"]: row for row in source_rows}
    if set(old) != set(actual):
        raise RuntimeError("Source set differs from completed coarse1.4")
    changed = [name for name in sorted(actual) if actual[name]["sha256"] != old[name]["sha256"]]
    if changed != ["source/case.lisp"]:
        raise RuntimeError(f"Unexpected original numerical source differences: {changed}")
    case = ROOT / "cases/benchmarks/gravity-slope-mc-srf-1p6.lisp"
    coarse_case = COARSE / "source/case.lisp"
    case_bytes = case.read_bytes()
    if case_bytes != (RUN / "source/case.lisp").read_bytes():
        raise RuntimeError("Current case differs from frozen executed case")
    if (coarse_case.read_bytes().count(b"(srf 1.4d0)") != 1
            or coarse_case.read_bytes().replace(b"(srf 1.4d0)", b"(srf 1.6d0)", 1) != case_bytes):
        raise RuntimeError("Executed recipes differ beyond literal strength reduction factor")
    provenance = h.read_json(RUN / "source-provenance.json")
    backend = provenance["nativeBackend"]
    if not (provenance["sourceSnapshotExactLoadedBytes"] and provenance["copiedByteEqualityBeforeLoad"]
            and set(provenance["copiedFiles"]) == set(source_members)
            and backend["verifiedBy"] == "GetModuleHandleW/GetModuleFileNameW"
            and backend["sha256"] == actual["source/libs/kirchoff.dll"]["sha256"]):
        raise RuntimeError("Original loaded-source/mapped-DLL proof disagrees")
    captured = h.read_json(RUN / "manifest.json")
    coarse_manifest = h.read_json(COARSE / "manifest.json")
    config, old_config = captured["config"], coarse_manifest["config"]
    if set(config) != set(old_config):
        raise RuntimeError("Actual configuration key sets changed")
    differences = [{"key": key, "coarse": old_config[key], "srf1p6": config[key]}
                   for key in sorted(config) if config[key] != old_config[key]]
    if {row["key"] for row in differences} != {"strengthReductionFactor", "cohesionPa", "frictionRad"}:
        raise RuntimeError(f"Unexpected compiled assignment differences: {differences}")
    if config["strengthReductionFactor"] != 1.6 or captured["particleCount"] != 880:
        raise RuntimeError("Wrong actual first screening case")
    live_path = RAW / f"{NAME}-live-process-verification.json"
    failure_path = RAW / f"{NAME}-live-proof-failure.json"
    live = h.read_json(live_path) if live_path.is_file() else None
    if live:
        roles = {row["role"]: row for row in live["processes"]}
        if (set(roles) != {"wrapper", "nativeCommand", "sbcl", "detachedWorker"}
                or not all(row["identityMatched"] for row in roles.values())
                or roles["wrapper"]["parentPid"] != roles["detachedWorker"]["pid"]
                or roles["nativeCommand"]["parentPid"] != roles["wrapper"]["pid"]
                or roles["sbcl"]["parentPid"] != roles["nativeCommand"]["pid"]
                or live["sourceCommit"] != COMMIT):
            raise RuntimeError("Stored actual live creation/session/parent proof is inconsistent")
    elif not failure_path.is_file():
        raise RuntimeError("Need actual live proof or explicitly retained helper failure")
    capture = ROOT / ".tmp/capture-gravity-srf1p6-processes.ps1"
    old_capture = (ROOT / ".tmp/capture-gravity-h05-processes.ps1").read_bytes()
    if old_capture.replace(b"srf1p4-h05-001", b"srf1p6-001", 1) != capture.read_bytes():
        raise RuntimeError("Live helper differs beyond run path")

    PACKET.mkdir(parents=True)
    (PACKET / ".gitattributes").write_bytes(b"* -text\n*.zip binary\n")
    h.copy(Path(__file__), PACKET / "executed-pack-script.py")
    h.copy(HELPER, PACKET / "executed-copy-hash-zip-helpers.py")
    h.copy(capture, PACKET / "proof-support/executed-capture-gravity-srf1p6-processes.ps1")
    members = dict(source_members)
    members["source/source-manifest.json"] = RUN / "source/source-manifest.json"
    # A source-manifest member always carries its complete original payloads.
    archives = [h.archive("original-native-source-at-launch", members)]
    for name in ("manifest.json", "source-provenance.json"):
        h.copy(RUN / name, PACKET / name)
    # Direct source index is explicitly metadata-only, not a second full tree.
    h.copy(RUN / "source/source-manifest.json", PACKET / "metadata/native-source-manifest-index.json")
    h.copy(RUN / "source/case.lisp", PACKET / "metadata/executed-case.lisp")
    runtime = {path.name: path for path in sorted(RAW.glob(f"{NAME}*")) if path.is_file()}
    for name, path in runtime.items():
        h.copy(path, PACKET / "runtime" / name)
    for name, path in h.tree_files(RAW / f"{NAME}-detached").items():
        h.copy(path, PACKET / "detached" / name)
    protocols = []
    for name in ("contract.json", "refinement-contract.json", "response-ladder-contract.json",
                 "response-ladder-audit-contract.json"):
        relative = f"research/references/unnotched-mc-ssr/{name}"
        source = ROOT / relative
        blob = subprocess.run(["git", "show", f"{COMMIT}:{relative}"], cwd=ROOT,
                              capture_output=True, check=True).stdout
        if source.read_bytes() != blob:
            raise RuntimeError(f"Protocol does not match exact native launch commit: {name}")
        h.copy(source, PACKET / "protocol" / name)
        protocols.append({**h.record(source), "matchesNativeLaunchCommit": True})
    # These old manifests/reviews are explicitly references, not this run's data.
    references = {
        "coarse1p4-native-manifest.json": COARSE / "manifest.json",
        "coarse1p4-native-review.json": COARSE / "review-001/review.json",
        "h05-completed-summary.json": ROOT / "docs/evidence/unnotched-gravity-2026-10-25/srf1p4-h05-001-completed/summary.json",
        "input-gate-summary.json": ROOT / "docs/evidence/unnotched-gravity-2026-10-25/response-ladder-inputs/summary.json",
        "input-gate-result.json": ROOT / "docs/evidence/unnotched-gravity-2026-10-25/response-ladder-inputs/result.json",
        "input-gate-original-artifact-index.json": ROOT / "docs/evidence/unnotched-gravity-2026-10-25/response-ladder-inputs/artifact-index.json",
    }
    for name, path in references.items():
        h.copy(path, PACKET / "historical-reference-and-input-gate" / name)
    h.write_json(PACKET / "source-and-case-verification.json", {
        "sourceFilesVerified": len(source_members), "files": source_rows,
        "allSourceManifestHashesAndLengthsMatched": True, "noncaseSourcesIdenticalToCoarse1p4": 281,
        "onlySourceDifference": changed, "exactCaseOnlyLiteralSrfChanged": True,
        "actualCompiledConfigurationDifferences": differences, "actualMappedDll": backend,
        "protocols": protocols,
        "sourceArchiveScope": "All282 original source/input/DLL payloads plus their original source manifest; direct metadata index is clearly separately named"})
    h.write_json(PACKET / "archive-member-verification.json", {"archives": archives,
        "actualNativeSourceMembers": len(source_members), "totalDecodedMembers": sum(a["decodedMembers"] for a in archives),
        "allCrcAndDecodedPayloadChecksPassed": True})
    launch = h.read_json(RAW / f"{NAME}-launch.json")
    h.write_json(PACKET / "summary.json", {
        "schema": "cl-mpm.unnotched-gravity.response-launch-evidence.v1", "status": "LAUNCH_PROOF_ONLY",
        "createdUtc": datetime.now(timezone.utc).isoformat(), "nativeSourceCommit": COMMIT,
        "startedUtc": launch["startedUtc"], "wallDeadlineUtc": launch["wallDeadlineUtc"],
        "maxWallHours": launch["maxWallHours"], "actualSourceFiles": len(source_members),
        "actualConfigDifferencesFromCoarse1p4": differences,
        "actualLiveProofCaptured": live is not None, "actualLiveProof": live,
        "liveProofFailureRetained": failure_path.is_file(), "processesRecapturedByPackager": False,
        "capturedNativeState": {key: captured.get(key) for key in ("status", "phase", "complete", "timeS", "updates", "savedFrames")},
        "historicalMetadataCaveat": "Native runner includes legacy fixed descriptive SRF1.40 critical-bracket wording. Actual frozen case/config/law is explicitlySRF1.6; legacy narrative is not a changed assignment or verified FoS claim.",
        "experiment": "FIRST finite preregistered response screen; strength intentionally reduced. No2.0 or fine confirmation launched by this packager.",
        "landslideVerified": False, "scientificallyValidated": False,
        "limits": "Stored live proof is timestamp-specific; mutable logs/manifest/status were not atomically captured. User-session worker has no proved logoff/sleep/reboot immunity. Launch is not completion or a physical result.",
        "operations": "Read/copy/hash/ZIP/CRC/decoded-byte verification only. No additional live process query, solver, tests, replay, saved-data review, comparison or render."})
    (PACKET / "README.md").write_text(
        "# First SRF1.6 unnotched response screen: launch evidence\n\n"
        "The actual frozen case changes only literal SRF1.4 to1.6; actual compiled SRF/cohesion/friction are the only configuration differences. All281 noncase sources are byte-identical to completed coarse1.4. "
        "All282 frozen source/input/DLL members match their original manifest and actual mapped-backend proof. The source ZIP contains every indexed source alongside that manifest; its separate direct index is metadata-only.\n\n"
        "The exact helper was prepared before its single live capture. Stored creation/session/parent proof or its actual failure is retained; this collector makes no further process query. Launch/status/manifest/log snapshots are separate moments. "
        "Original response contracts match native launch commit bytes. Old coarse/fine results and input-gate summaries are explicitly historical references. Native descriptive SRF1.40 text is legacy metadata; the executed case/config recordsSRF1.6.\n\n"
        "This is a disclosed strength-reduction experiment, not unchanged-soil collapse, a paper parameter, a FoS bracket, completion, verified landslide or scientific validation. No solver/test/analysis/render is repeated. "
        "Originals remain in output; all ZIP members are decoded, CRC-tested and byte-compared. * -text preserves artifact bytes; root must independently verify staged blobs.\n",
        encoding="utf-8", newline="\n")
    rows = [h.record(path, PACKET) for path in sorted(PACKET.rglob("*")) if path.is_file()]
    h.write_json(PACKET / "artifact-index.json", {"schema": "cl-mpm.evidence.artifact-index.v1", "artifacts": rows,
        "note": "Index excludes itself. Raw bytes preserved; direct native-source-manifest-index.json is metadata-only, full original snapshot is in the verified ZIP."})
    for row in rows:
        if h.record(PACKET / row["path"], PACKET) != row:
            raise RuntimeError("Indexed artifact changed")
    print(json.dumps({"packet": str(PACKET), "indexedArtifacts": len(rows),
        "sourceFilesVerified": len(source_members), "decodedZipMembers": sum(a["decodedMembers"] for a in archives),
        "actualLiveProofCaptured": live is not None, "actualLiveProofCapturedUtc": live and live["capturedUtc"],
        "actualConfigDifferences": differences, "landslideVerified": False}, indent=2))


if __name__ == "__main__":
    main()
