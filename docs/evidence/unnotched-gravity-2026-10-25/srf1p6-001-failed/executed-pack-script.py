"""Preserve terminal SRF1.6 native failure and existing first review/replay.

This collector never launches native code, a replay, an audit, rendering or
process discovery. Execute only after root confirms both agents are terminal.
"""
from datetime import datetime, timezone
import argparse
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
PACKET = ROOT / f"docs/evidence/unnotched-gravity-2026-10-25/{NAME}-failed"
HELPER = ROOT / ".tmp/pack-gravity-completed-002.py"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-dir", type=Path, required=True)
    parser.add_argument("--replay-dir", type=Path, required=True)
    parser.add_argument("--replay-exit", type=Path, required=True,
                        help="Existing authoritative terminal replay exit proof")
    args = parser.parse_args()
    if PACKET.exists():
        raise RuntimeError("Preserve previous collector attempt; do not overwrite")
    spec = importlib.util.spec_from_file_location("_copy_hash_zip_helpers", HELPER)
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)  # Definitions only; its main is never executed.
    h.RUN, h.PACKET = RUN, PACKET
    review_dir, replay_dir = args.review_dir.resolve(), args.replay_dir.resolve()
    if not review_dir.is_relative_to(RUN.resolve()) or not replay_dir.is_relative_to((ROOT / "output").resolve()):
        raise RuntimeError("Review/replay directories must remain under their workspace output")
    status = h.read_json(RAW / f"{NAME}-status.json")
    worker = h.read_json(RAW / f"{NAME}-detached/worker-exit.json")
    manifest = h.read_json(RUN / "manifest.json")
    if (status["status"] != "FAILED_NATIVE" or status["nativeExitCode"] != 1
            or status["nativeComplete"] or manifest["complete"] or worker["exitCode"] != 1
            or status["sourceCommit"] != COMMIT):
        raise RuntimeError("Not the expected actual non-complete native1/worker1 failure")
    review_exit = h.read_json(review_dir / "review-exit.json")
    review = h.read_json(review_dir / "review.json")
    replay_exit = h.read_json(args.replay_exit)
    if review.get("nativeComplete") or review.get("savedScope") != "partial-saved-states-only":
        raise RuntimeError("Partial saved review unexpectedly claims completed native scope")
    source_members = h.immutable_sources()  # All282 original executed members.
    source_index = h.read_json(RUN / "source/source-manifest.json")
    old = {row["path"]: row for row in h.read_json(COARSE / "source/source-manifest.json")["files"]}
    new = {row["path"]: row for row in source_index["files"]}
    if set(old) != set(new) or [key for key in sorted(new) if new[key]["sha256"] != old[key]["sha256"]] != ["source/case.lisp"]:
        raise RuntimeError("Original noncase numerical sources differ from completed coarse1.4")
    old_case, new_case = (COARSE / "source/case.lisp").read_bytes(), (RUN / "source/case.lisp").read_bytes()
    if old_case.count(b"(srf 1.4d0)") != 1 or old_case.replace(b"(srf 1.4d0)", b"(srf 1.6d0)", 1) != new_case:
        raise RuntimeError("Original frozen case differs beyond literal SRF1.4 to1.6")
    old_config, config = h.read_json(COARSE / "manifest.json")["config"], manifest["config"]
    if set(old_config) != set(config):
        raise RuntimeError("Original compiled configuration sets differ")
    changes = [{"key": key, "coarse1p4": old_config[key], "srf1p6": config[key]}
               for key in sorted(config) if config[key] != old_config[key]]
    if {row["key"] for row in changes} != {"strengthReductionFactor", "cohesionPa", "frictionRad"}:
        raise RuntimeError("Original compiled changes exceed declared SRF/c/phi")
    provenance = h.read_json(RUN / "source-provenance.json")
    backend = provenance["nativeBackend"]
    if not (provenance["sourceSnapshotExactLoadedBytes"] and provenance["copiedByteEqualityBeforeLoad"]
            and backend["verifiedBy"] == "GetModuleHandleW/GetModuleFileNameW"
            and backend["sha256"] == h.record(RUN / "source/libs/kirchoff.dll")["sha256"]):
        raise RuntimeError("Original frozen source/DLL runtime proof disagrees")

    verified_records = []
    def verify_record(row, path=None):
        path = path or Path(row["path"])
        actual = h.record(path)
        if (actual["bytes"], actual["sha256"]) != (row["bytes"], row["sha256"]):
            raise RuntimeError(f"Recorded executed support/input differs: {path}")
        verified_records.append({"path": str(path), "bytes": actual["bytes"], "sha256": actual["sha256"]})

    pre = h.read_json(review_dir / "analysis-pre-execution.json")
    for row in pre["sourceCopies"]:
        verify_record(row, review_dir / "analysis-support" / Path(row["path"]).name)
    for row in review.get("inputHashes", []):
        verify_record(row)
    for row in review.get("media", []):
        verify_record(row, review_dir / Path(row["path"]).name)
    # Replay evidence is collected as received, including all of its own source,
    # input, call-count, exit and failure records. It is NOT executed by us.
    live = h.read_json(RAW / f"{NAME}-live-process-verification.json")
    roles = {row["role"]: row for row in live["processes"]}
    if (set(roles) != {"wrapper", "nativeCommand", "sbcl", "detachedWorker"}
            or not all(row["identityMatched"] for row in roles.values())
            or roles["wrapper"]["parentPid"] != roles["detachedWorker"]["pid"]
            or roles["nativeCommand"]["parentPid"] != roles["wrapper"]["pid"]
            or roles["sbcl"]["parentPid"] != roles["nativeCommand"]["pid"]
            or live["sourceCommit"] != COMMIT):
        raise RuntimeError("Existing historical live proof is inconsistent")

    PACKET.mkdir(parents=True)
    (PACKET / ".gitattributes").write_bytes(b"* -text\n*.zip binary\n")
    h.copy(Path(__file__), PACKET / "executed-pack-script.py")
    h.copy(HELPER, PACKET / "executed-copy-hash-zip-helpers.py")
    for filename in ("capture-gravity-srf1p6-processes.ps1", "capture-gravity-srf1p6-launch.py"):
        h.copy(ROOT / ".tmp" / filename, PACKET / "launch-capture-support" / filename)
    h.write_json(PACKET / "launch-capture-support/status.json", {
        "status": "LIVE_CAPTURE_COMPLETED_LAUNCH_PACKER_NOT_EXECUTED_BEFORE_NATIVE_FAILURE",
        "liveCaptureCalls": 1, "liveCapturedUtc": live["capturedUtc"],
        "liveHelperExit": "0 as observed from original invocation; exact helper stdout and stored proof retained",
        "launchPackerExecuted": False,
        "preparedLaunchPackerScope": "Retained exact prepared source, not represented as an executed archive operation",
        "processesRecapturedAfterFailure": False,
        "limits": "Only the historical timestamped NATIVE_RUNNING proof is asserted; no active process or completed launch archive is invented"})
    # Include source extras (ASDF action/load proof) but exclude private caches.
    native_members = dict(source_members)
    native_members.update({"source/" + name: path for name, path in h.tree_files(RUN / "source").items()
                           if ".native-cache" not in Path(name).parts})
    analysis_roots = {review_dir.name}
    if replay_dir.parent == RUN.resolve():
        analysis_roots.add(replay_dir.name)
    native_members.update({name: path for name, path in h.tree_files(RUN).items()
                           if Path(name).parts[0] not in analysis_roots | {"source"}})
    runtime = {"adjacent/" + path.name: path for path in sorted(RAW.glob(f"{NAME}*")) if path.is_file()}
    runtime.update({"detached/" + name: path for name, path in h.tree_files(RAW / f"{NAME}-detached").items()})
    native_members.update(runtime)
    archives = [h.archive("original-native-source-partial-raw-and-runtime", native_members)]
    archives.append(h.archive("first-saved-partial-review-and-media", h.tree_files(review_dir)))
    replay_members = {name: path for name, path in h.tree_files(replay_dir).items()
                      if ".native-cache" not in Path(name).parts}
    replay_adjacent = {"adjacent/" + path.name: path for path in sorted(replay_dir.parent.glob(replay_dir.name + "*"))
                       if path.is_file()}
    replay_members.update(replay_adjacent)
    replay_support = {name: ROOT / ".tmp" / name for name in
                      ("gravity-srf16-failure-replay.lisp", "run-gravity-srf16-failure-replay.ps1", "verify-srf16-replay.py")}
    replay_members.update({"received-execution-and-verification-support/" + name: path
                           for name, path in replay_support.items()})
    if args.replay_exit.resolve().is_relative_to(replay_dir):
        pass
    else:
        replay_members["adjacent-authoritative-exit/" + args.replay_exit.name] = args.replay_exit
    archives.append(h.archive("first-actual-capsule-replay-as-received", replay_members))
    for name in ("manifest.json", "source-provenance.json", "mc-integration-failure.json"):
        h.copy(RUN / name, PACKET / "native" / name)
    h.copy(RUN / "source/source-manifest.json", PACKET / "metadata/native-source-manifest-index.json")
    h.copy(RUN / "source/case.lisp", PACKET / "metadata/executed-case.lisp")
    for name, path in runtime.items():
        h.copy(path, PACKET / "native" / name)
    for name, path in h.tree_files(review_dir).items():
        if "actual-frames" not in Path(name).parts:
            h.copy(path, PACKET / "saved-review" / name)
    h.copy(args.replay_exit, PACKET / "replay/authoritative-exit.json")
    for name, path in replay_adjacent.items():
        h.copy(path, PACKET / "replay" / name)
    for name, path in replay_support.items():
        h.copy(path, PACKET / "replay/received-execution-and-verification-support" / name)
    # Direct replay JSON/log summaries permit inspection; full snapshot is in ZIP.
    for name, path in replay_members.items():
        if len(Path(name).parts) == 1 and path.suffix.lower() in (".json", ".log", ".txt", ".md"):
            h.copy(path, PACKET / "replay" / name)
    protocols = []
    for name in ("contract.json", "refinement-contract.json", "response-ladder-contract.json", "response-ladder-audit-contract.json"):
        relative = f"research/references/unnotched-mc-ssr/{name}"
        path = ROOT / relative
        original = subprocess.run(["git", "show", f"{COMMIT}:{relative}"], cwd=ROOT,
                                  capture_output=True, check=True).stdout
        if original != path.read_bytes():
            raise RuntimeError("Frozen response/reference contract changed after native launch")
        h.copy(path, PACKET / "protocol" / name)
        protocols.append({**h.record(path), "matchesNativeLaunchCommit": True})
    references = {
        "coarse1p4-native-manifest.json": COARSE / "manifest.json",
        "coarse1p4-native-review.json": COARSE / "review-001/review.json",
        "h05-completed-summary.json": ROOT / "docs/evidence/unnotched-gravity-2026-10-25/srf1p4-h05-001-completed/summary.json",
        "input-gate-summary.json": ROOT / "docs/evidence/unnotched-gravity-2026-10-25/response-ladder-inputs/summary.json",
        "input-gate-result.json": ROOT / "docs/evidence/unnotched-gravity-2026-10-25/response-ladder-inputs/result.json",
    }
    for name, path in references.items():
        h.copy(path, PACKET / "historical-reference-and-input-gate" / name)
    h.write_json(PACKET / "source-and-input-verification.json", {
        "sourceCount": len(source_members), "files": source_index["files"],
        "allOriginalSourceHashesAndLengthsMatched": True,
        "noncaseSourcesIdenticalToCoarse1p4": 281, "onlySourceDifference": "source/case.lisp",
        "exactCaseOnlySrfLiteralChanged": True, "actualConfigurationChanges": changes,
        "actualMappedDll": backend, "protocols": protocols,
        "recordedSupportInputAndMediaChecks": verified_records,
        "scope": "Hash/length and existing-record verification only; no native or saved-data analysis repeated"})
    h.write_json(PACKET / "archive-member-verification.json", {"archives": archives,
        "actualNativeSourceMembers": len(source_members), "totalDecodedMembers": sum(row["decodedMembers"] for row in archives),
        "allCrcAndDecodedPayloadChecksPassed": True})
    h.write_json(PACKET / "summary.json", {
        "schema": "cl-mpm.unnotched-gravity.failed-native-evidence.v1", "createdUtc": datetime.now(timezone.utc).isoformat(),
        "nativeSourceCommit": COMMIT, "nativeExit": status["nativeExitCode"], "workerExit": worker["exitCode"],
        "nativeComplete": False, "supervisorStatus": status["status"],
        "manifestTimeS": manifest.get("timeS"), "lastSavedTimeS": manifest.get("lastSavedTimeS"),
        "savedFrames": manifest.get("savedFrames"), "acceptedUpdates": manifest.get("updates"),
        "lastSavedTimeIsNotAssertedAsExactFailureTime": True,
        "actualNativeSources": len(source_members), "actualConfigurationChanges": changes,
        "partialReviewExitAsReceived": review_exit, "savedIntegrity": review.get("integrityStatus"),
        "savedScope": review.get("savedScope"), "savedMediaAsReceived": review.get("media"),
        "replayExitAsReceived": replay_exit, "replayExecutedByCollector": False,
        "historicalLiveCaptureUtc": live["capturedUtc"], "launchPacketNeverExecutedBeforeFailure": True,
        "landslideVerified": False, "scientificallyValidated": False,
        "classification": "Numerical/material rejection is not a landslide or unstable FoS bound; factor2 not launched by this collector",
        "legacyMetadata": "Runner's fixed SRF1.40 narrative is historical wording; actual original case/config/law recordsSRF1.6",
        "scope": "Original failed native attempt, first saved partial review/media and first actual capsule replay preserved separately. Partial review success cannot relabel native failure as complete.",
        "operations": "Read/copy/hash/ZIP/CRC/all-member decoded-byte verification only; no process query, solver, material test, replay, audit, comparison, rendering or media decode invoked"})
    (PACKET / "README.md").write_text(
        "# First SRF1.6 screen: native failure retained\n\n"
        "Original native and worker exit1; native complete=false. Full original282 source/input/DLL members, raw partial CSV/VTK, failure capsule, runtime provenance, modern logs/status/launch and detached exits are retained. "
        "The manifest-indexed source ZIP includes every original indexed payload; direct metadata indexes are separately named.\n\n"
        "A single historical live creation/session/parent proof was captured while the run was active. Its exact helper/log/proof is retained. The prepared launch packer was never executed before failure; no earlier launch archive or new live proof is invented. "
        "First saved-data review/media and first actual capsule replay have separate exact-source, output and exit records. Packaging repeats neither. Partial saved integrity/media success is not native completion.\n\n"
        "Replay command/log/exit, mathematical diagnosis, complete replay snapshot and received helper/wrapper/verifier are retained. The replay helper's inherited template header is historical wording; actual command/capsule/source proofs identify this invocation without editing executed bytes.\n\n"
        "Only literal SRF and derived SRF/c/phi differ from completed coarse1.4;281 noncase sources match. Frozen response/reference contracts and explicitly historical metadata are retained. "
        "Numerical rejection is not physical instability, a factor-of-safety bracket, verified landslide or scientific validation. Last saved time does not locate the exact failing unsaved update.\n\n"
        "All ZIP members are CRC-tested, decoded and byte-compared against original files; private native/Python caches are excluded. Originals remain untouched. * -text preserves indexed bytes; root must verify staged blobs.\n",
        encoding="utf-8", newline="\n")
    rows = [h.record(path, PACKET) for path in sorted(PACKET.rglob("*")) if path.is_file()]
    h.write_json(PACKET / "artifact-index.json", {"schema": "cl-mpm.evidence.artifact-index.v1", "artifacts": rows,
        "note": "Index excludes itself; raw bytes preserved. Original native/replay source-manifest archive members carry their full payloads."})
    for row in rows:
        if h.record(PACKET / row["path"], PACKET) != row:
            raise RuntimeError("Final indexed artifact changed")
    print(json.dumps({"packet": str(PACKET), "indexedArtifacts": len(rows),
        "actualNativeSourceFiles": len(source_members), "decodedZipMembers": sum(row["decodedMembers"] for row in archives),
        "nativeExit": 1, "nativeComplete": False, "landslideVerified": False}, indent=2))


if __name__ == "__main__":
    main()
