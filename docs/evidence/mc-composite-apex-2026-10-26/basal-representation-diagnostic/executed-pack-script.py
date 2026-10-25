"""Collect one existing no-timestep basal representation diagnostic; rerun none."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "output/mc-composite-apex-2026-10-26"
NAME = "basal-representation-001"
RUN = RAW / NAME
PACKET = ROOT / "docs/evidence/mc-composite-apex-2026-10-26/basal-representation-diagnostic"
HELPER = ROOT / ".tmp/pack-gravity-completed-002.py"


def main():
    if PACKET.exists():
        raise RuntimeError("Preserve earlier packet; refuse overwrite")
    spec = importlib.util.spec_from_file_location("_copy_hash_zip_helpers", HELPER)
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)  # Definitions only; no historical main execution.
    h.PACKET = PACKET
    exit_record = h.read_json(RAW / (NAME + ".exit.json"))
    command = h.read_json(RAW / (NAME + ".command.json"))
    result = h.read_json(RUN / "result.json")
    if command["executable"] != "windows/cl-mpm.cmd" or command["arguments"] != [
            "tests/benchmarks/gravity-basal-representation.lisp",
            "output/mc-composite-apex-2026-10-26/basal-representation-001"]:
        raise RuntimeError("Actual recorded diagnostic launcher invocation differs")
    rows = h.read_json(RUN / "source/source-manifest.json")["files"]
    index = {row["path"]: row for row in rows}
    if len(index) != len(rows):
        raise RuntimeError("Duplicate original source entry")
    checked = []
    for name, expected in index.items():
        path = (RUN / name).resolve()
        if not path.is_relative_to((RUN / "source").resolve()):
            raise RuntimeError("Source escaped frozen tree")
        actual = h.record(path)
        if (actual["bytes"], actual["sha256"]) != (expected["bytes"], expected["sha256"]):
            raise RuntimeError("Original frozen source changed")
        checked.append({"path": name, "bytes": actual["bytes"], "sha256": actual["sha256"]})
    source_proofs = []
    for phase in ("before", "after"):
        proof = h.read_json(RUN / f"source-proof-{phase}.json")["files"]
        if len(proof) != len(index) or {r["path"]: r["sha256"] for r in proof} != {k: r["sha256"] for k, r in index.items()}:
            raise RuntimeError("Original before/after source hashes disagree")
        source_proofs.append({"phase": phase, "hashesMatched": len(proof)})
    runtime = []
    for filename in ("source-provenance-before.json", "source-provenance.json"):
        proof = h.read_json(RUN / filename)
        backend, dll = proof["nativeBackend"], RUN / "source/libs/kirchoff.dll"
        if not (proof["sourceSnapshotExactLoadedBytes"] and proof["copiedByteEqualityBeforeLoad"]
                and set(proof["copiedFiles"]) == set(index)
                and backend["verifiedBy"] == "GetModuleHandleW/GetModuleFileNameW"
                and Path(backend["modulePath"]).resolve() == dll.resolve()
                and backend["sha256"] == h.record(dll)["sha256"]):
            raise RuntimeError("Actual recorded source/runtime-DLL proof disagrees")
        runtime.append({"file": filename, "actualNativeBackend": backend, "copiedSourcesVerified": len(index)})
    complete = result["status"] == "READ_ONLY_KINEMATIC_DIAGNOSTIC_COMPLETE"
    if complete and not (exit_record["exitCode"] == 0 and result["mpmCallsAttempted"] == 0
            and result["constitutiveCallsAttempted"] == 0
            and len(result["meshSummaries"]) == 2
            and all(row["actualInitialParticleStateUnchanged"] for row in result["meshSummaries"])):
        raise RuntimeError("Diagnostic completion contradicts zero-call/unchanged-MP proof")
    members = {name: path for name, path in h.tree_files(RUN).items() if ".native-cache" not in Path(name).parts}
    members.update({"adjacent/" + path.name: path for path in sorted(RAW.glob(NAME + ".*")) if path.is_file()})
    if sum(name.endswith("source/source-manifest.json") for name in members) != 1:
        raise RuntimeError("Expected exactly one full native source manifest")
    PACKET.mkdir(parents=True)
    (PACKET / ".gitattributes").write_bytes(b"* -text\n*.zip binary\n")
    h.copy(Path(__file__), PACKET / "executed-pack-script.py")
    h.copy(HELPER, PACKET / "executed-copy-hash-zip-helpers.py")
    prior = RAW / "basal-representation-pack-attempt-001"
    for name, path in h.tree_files(prior).items():
        h.copy(path, PACKET / "prior-collector-attempt-001" / name)
    archive = h.archive("complete-source-native-kernel-diagnostic-and-runtime", members)
    for name, path in members.items():
        if not name.startswith("source/"):
            h.copy(path, PACKET / "retained-diagnostic" / name)
    h.copy(RUN / "source/source-manifest.json", PACKET / "metadata/native-source-manifest-index.json")
    h.write_json(PACKET / "source-and-runtime-verification.json", {"sourceCount": len(rows), "files": checked,
        "beforeAfterProofs": source_proofs, "recordedRuntimeProofs": runtime,
        "scope": "Retained file hash/length and existing loaded-module record comparison only; no gate or kernel invocation repeated"})
    h.write_json(PACKET / "archive-member-verification.json", {"archives": [archive],
        "actualNativeSourceMembers": len(rows), "totalDecodedMembers": archive["decodedMembers"],
        "allCrcAndDecodedPayloadChecksPassed": True})
    h.write_json(PACKET / "summary.json", {"createdUtc": datetime.now(timezone.utc).isoformat(),
        "nativeLauncherExit": exit_record, "sourceCheckpoint": command["sourceCommit"],
        "actualInvocation": command,
        "invocationHelperProofScope": "Actual record is direct windows/cl-mpm.cmd invocation without invoker-helper SHA; no unrelated helper is claimed executed. Original selected launcher/driver bytes remain in the native snapshot.",
        "priorCollectorFailure": "Metadata-schema assumption KeyError before packet/source hashing; exact failed collector and error retained; no diagnostic repeat",
        "diagnosticStatusAsReceived": result["status"], "failureAsReceived": result["failure"],
        "nativeSourceCount": len(rows), "mpmCallsAttempted": result["mpmCallsAttempted"],
        "constitutiveCallsAttempted": result["constitutiveCallsAttempted"],
        "actualInitialMpUnchangedProofAsReceived": result["meshSummaries"],
        "physicalResult": result["physicalResult"], "scientificallyValidated": False, "landslideVerified": False,
        "scope": "Actual native GIMP stencil/representation diagnostic using hypothetical prescribed kinematics; not a time integration, solved velocity, trajectory, new static search or landslide result",
        "operations": "Read/copy/hash/ZIP/CRC/all-member decoded-byte comparison only; no native, kernel, test, analysis, renderer or process query"})
    (PACKET / "README.md").write_text(
        "# Read-only basal representation diagnostic\n\n"
        "This packet preserves the FIRST frozen no-timestep diagnostic invocation, its source/input/runtime proofs, actual-initial-MP CSV, separately labelled hypothetical arc-profile CSV, selected native stencils, result and any failure. Prescribed field evaluations are not solved velocities or a simulation trajectory.\n\n"
        "The actual native GIMP kernel is queried without constitutive or MPM steps. Completion, zero attempted calls and unchanged actual MP states are recorded separately; no physical slide or scientific validation is asserted. Historical static-circle data is an immutable input, not a repeated static search.\n\n"
        "One ZIP contains the original source manifest and all indexed source/input/DLL payloads, original CSV/result and modern invocation log/command/exit. Before/after/current copied hashes and recorded actual mapped DLL match; the archive is CRC-tested and every decoded member byte-compared. Originals remain untouched, private caches are excluded, and collection repeats no diagnostic/kernel/test or process query. * -text preserves exact bytes; root owns independent verification/staging.\n",
        encoding="utf-8", newline="\n")
    artifacts = [h.record(path, PACKET) for path in sorted(PACKET.rglob("*")) if path.is_file()]
    h.write_json(PACKET / "artifact-index.json", {"schema": "cl-mpm.evidence.artifact-index.v1", "artifacts": artifacts,
        "note": "Index excludes itself. Raw bytes protected by * -text; source payload appears once."})
    for row in artifacts:
        if h.record(PACKET / row["path"], PACKET) != row:
            raise RuntimeError("Indexed artifact changed")
    print(json.dumps({"packet": str(PACKET), "indexedArtifacts": len(artifacts),
        "decodedZipMembers": archive["decodedMembers"], "nativeSourceFiles": len(rows),
        "diagnosticStatus": result["status"], "mpmCallsAttempted": result["mpmCallsAttempted"],
        "constitutiveCallsAttempted": result["constitutiveCallsAttempted"]}, indent=2))


if __name__ == "__main__":
    main()
