"""Collect four CLOSED repair gates; never execute tests/native/analysis again.

Execute a frozen copy with its frozen helper and collector-source-before.json.
"""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys

ROOT = next(path for path in Path(__file__).resolve().parents if (path / "cl-mpm.asd").is_file() and (path / ".git").exists())
RAW = ROOT / "output/mc-composite-apex-2026-10-26"
PACKET = ROOT / "docs/evidence/mc-composite-apex-2026-10-26/composite-apex-repair-gates-001"
HELPER = Path(__file__).with_name("copy-hash-zip-helpers.py")
FREEZE = Path(__file__).with_name("collector-source-before.json")
GATES = {
    "stable-math-001": (290, "source-provenance.json", {
        "explicitProductionProjectorCalls": 33, "physicalUpdateAttempts": 0, "nativeConstitutiveCalls": 0,
        "oldControlsCalled": 0, "unchangedOldProjectorCalls": 0, "actualFailedTrialReplayCalls": 0}),
    "stable-regression-001": (289, "source-provenance-after.json", {
        "explicitNewPureProjectorCalls": 38, "explicitStrictComparatorCalls": 6,
        "nativeConstitutiveCalls": 10, "physicalUpdateAttempts": 0, "oldOriginalFailureReplayCalls": 0}),
    "capture-controls-001": (288, "source-provenance-after.json", {
        "explicitHelperOnlyFailures": 6, "optionalProjectorCalls": 7, "nativeConstitutiveCalls": 2,
        "optionalReplayAttempts": 9, "optionalReplayProjectorCalls": 2,
        "strictReplaySchemaRejectionAttempts": 1, "syntheticStrictDelegateCalls": 1,
        "physicalUpdateAttempts": 0, "originalFineFailureReplayCalls": 0}),
    "fine-repair-controls-001": (291, "source-provenance.json", {
        "physicalUpdatesExecuted": 2, "materialCallsAttempted": 7040, "materialCallsAccepted": 7040,
        "standaloneConstitutiveCallsAttempted": 0, "standaloneConstitutiveCallsAccepted": 0})}


def main():
    if PACKET.exists():
        raise RuntimeError("Preserve previous repair packet; no overwrite")
    spec = importlib.util.spec_from_file_location("_frozen_copy_hash_zip_helpers", HELPER)
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)  # Definitions only; guarded historical main is never called.
    h.PACKET = PACKET
    freeze = h.read_json(FREEZE)
    for row in freeze["files"]:
        actual = h.record(Path(row["path"]))
        if (actual["bytes"], actual["sha256"]) != (row["bytes"], row["sha256"]):
            raise RuntimeError("Frozen collector/helper changed before execution")
    if {Path(row["path"]).resolve() for row in freeze["files"]} != {Path(__file__).resolve(), HELPER.resolve()}:
        raise RuntimeError("Freeze record does not bind this executed collector and helper")
    comparison_path = RAW / "fine-repair-controls-001/original-output-byte-comparison.json"
    comparison = h.read_json(comparison_path)
    expected_names = {"history.csv", "particles.csv", *("vtk/particles_%04d.vtk" % i for i in range(3))}
    if (comparison["status"] != "PASS" or len(comparison["comparedFiles"]) != 5
            or {row["relative"] for row in comparison["comparedFiles"]} != expected_names
            or not all(row["bytesIdentical"] is True for row in comparison["comparedFiles"])):
        raise RuntimeError("Wait for root's closed five-file original bounded-output comparison")
    comparison_script = Path(comparison["executedScriptBefore"]["path"])
    script_actual = h.record(comparison_script)
    if (script_actual["bytes"], script_actual["sha256"]) != (
            comparison["executedScriptBefore"]["bytes"], comparison["executedScriptBefore"]["sha256"]):
        raise RuntimeError("Original comparison script differs from its before-execution record")
    # Bind retained hashes without repeating the existing comparison operation.
    comparison_bindings = []
    for row in comparison["comparedFiles"]:
        for side in ("original", "repaired"):
            actual = h.record(Path(row[side]["path"]))
            if (actual["bytes"], actual["sha256"]) != (row[side]["bytes"], row[side]["sha256"]):
                raise RuntimeError("Retained compared artifact changed")
            comparison_bindings.append(actual)
    collected = {}
    current_cache = {}
    for name, (expected_count, after_name, counters) in GATES.items():
        run = RAW / name
        result = h.read_json(run / "result.json")
        command = h.read_json(RAW / (name + "-command.json"))
        native_exit = h.read_json(RAW / (name + "-exit.json"))
        if result["passed"] is not True or native_exit["exitCode"] != 0 or not native_exit.get("endedUtc"):
            raise RuntimeError("Native repair gate is not closed/PASS: " + name)
        if any(result.get(key) != value for key, value in counters.items()):
            raise RuntimeError("Original repair gate counters differ: " + name)
        group_count = {"stable-regression-001": 15, "capture-controls-001": 8, "fine-repair-controls-001": 4}.get(name)
        if group_count is not None:
            planned = result.get("plannedGroups", result.get("selectedGroups", result["passedGroups"]))
            if len(result["passedGroups"]) != group_count or result["passedGroups"] != planned or result.get("failedGroups", []):
                raise RuntimeError("Original selected repair groups differ: " + name)
        if name == "stable-math-001" and (len(result["cases"]) != 33 or result["failures"]):
            raise RuntimeError("Original fixed stable arithmetic cases differ")
        if name == "fine-repair-controls-001":
            observed = result["observations"]
            if not (observed["fineParticleCount"] == 3520 and observed["savedParticleRows"] == 10560
                    and observed["savedVtkStates"] == 3 and observed["savedApexActiveRows"] == 0
                    and observed["apexActivationRequired"] is False):
                raise RuntimeError("Original bounded fine observation scope differs")
        rows = h.read_json(run / "source/source-manifest.json")["files"]
        source_index = {row["path"]: row for row in rows}
        if len(rows) != expected_count or len(source_index) != expected_count:
            raise RuntimeError("Original gate source count differs: " + name)
        sources, current = [], []
        for row in rows:
            path = (run / row["path"]).resolve()
            if not path.is_relative_to((run / "source").resolve()):
                raise RuntimeError("Gate source escaped original snapshot")
            actual = h.record(path)
            if (actual["bytes"], actual["sha256"]) != (row["bytes"], row["sha256"]):
                raise RuntimeError("Original executed source bytes changed: " + str(path))
            sources.append(actual)
            original = Path(row["originalPath"]).resolve()
            key = str(original)
            if key not in current_cache:
                current_cache[key] = h.record(original) if original.is_file() else None
            live = current_cache[key]
            current.append({"frozenPath": row["path"], "originalPath": key, "current": live,
                "currentMatchesOriginalExecutedBytes": live is not None and (live["bytes"], live["sha256"]) == (row["bytes"], row["sha256"])})
        expected_hashes = {path: row["sha256"] for path, row in source_index.items()}
        for proof_name in ("source-proof-before.json", "source-proof-after.json"):
            proof = h.read_json(run / proof_name)
            if len(proof["files"]) != expected_count or {row["path"]: row["sha256"] for row in proof["files"]} != expected_hashes:
                raise RuntimeError("Original gate before/after proof differs: " + name)
        backend = result["nativeBackend"]
        for provenance_name in ("source-provenance-before.json", after_name):
            provenance = h.read_json(run / provenance_name)
            if not (provenance["sourceSnapshotExactLoadedBytes"] and provenance["copiedByteEqualityBeforeLoad"]
                    and provenance["nativeBackend"] == backend
                    and backend["sha256"] == source_index["source/libs/kirchoff.dll"]["sha256"]
                    and Path(backend["modulePath"]).resolve() == (run / "source/libs/kirchoff.dll").resolve()
                    and backend["verifiedBy"] == "GetModuleHandleW/GetModuleFileNameW"):
                raise RuntimeError("Original gate runtime/DLL proof differs: " + name)
        members = {path: file for path, file in h.tree_files(run).items() if ".native-cache" not in Path(path).parts}
        if {path for path in members if path.startswith("source/") and path != "source/source-manifest.json"} != set(source_index):
            raise RuntimeError("Native gate archive source membership differs")
        members.update({"adjacent/" + p.name: p for p in sorted(RAW.glob(name + "*")) if p.is_file()})
        if name == "fine-repair-controls-001":
            members["existing-comparison-script/" + comparison_script.name] = comparison_script
        collected[name] = {"run": run, "result": result, "command": command, "nativeExit": native_exit,
            "sourceIndex": source_index, "sources": sources, "current": current, "members": members,
            "provenanceAfterFile": after_name, "counters": counters}

    PACKET.mkdir(parents=True)
    (PACKET / "archives").mkdir()
    (PACKET / ".gitattributes").write_bytes(b"* -text\n*.zip binary\n")
    h.copy(Path(__file__), PACKET / "executed-pack-script.py")
    h.copy(HELPER, PACKET / "executed-copy-hash-zip-helpers.py")
    h.copy(FREEZE, PACKET / "collector-source-before.json")
    h.write_json(PACKET / "packaging-invocation.json", {"argv": sys.argv, "createdUtc": datetime.now(timezone.utc).isoformat(),
        "scope": "Read/copy/hash/ZIP/CRC/decoded-byte collection only; no tests, solver, audit, render, replay or process query"})
    archives, summaries = [], []
    for name, gate in collected.items():
        archive = h.archive("archives/" + name + "-complete-native-source-runtime", gate["members"])
        archives.append(archive)
        decoded = {row["path"]: row for row in archive["members"]}
        for path, expected in gate["sourceIndex"].items():
            if (decoded[path]["bytes"], decoded[path]["sha256"]) != (expected["bytes"], expected["sha256"]):
                raise RuntimeError("Decoded executed gate source differs")
        target = PACKET / "gates" / name
        for path in sorted(gate["run"].glob("*.json")):
            h.copy(path, target / path.name)
        for suffix, target_name in (("-command.json", "command.json"), ("-exit.json", "exit.json"), ("-native.log", "native.log")):
            h.copy(RAW / (name + suffix), target / target_name)
        h.copy(gate["run"] / "source/source-manifest.json", target / "source-manifest-index.json")
        h.copy(gate["run"] / "source/case.lisp", target / "executed-test.lisp")
        h.write_json(target / "recorded-source-byte-bindings.json", {"originalSources": gate["sources"], "allMatched": True,
            "originalBeforeAfterProofsMatchOriginalPreloadManifest": True,
            "runtimeBackendAsOriginallyRecorded": gate["result"]["nativeBackend"],
            "provenanceAfterOriginalFilename": gate["provenanceAfterFile"],
            "scope": "Original executed bytes and stored runtime/DLL mapping only; no remapping after exit"})
        h.write_json(target / "current-source-bindings.json", {"rows": gate["current"],
            "scope": "Current original-path hashes at collection time; earlier gates may predate intentional capture edits. Original runtime identity is always its frozen source manifest, never current HEAD."})
        summaries.append({"name": name, "nativeExit": gate["nativeExit"]["exitCode"],
            "nativeEndedUtc": gate["nativeExit"]["endedUtc"], "nativeSourceCommit": gate["command"]["sourceCommit"],
            "nativeSourceFiles": len(gate["sourceIndex"]), "selectedGroupCount": len(gate["result"].get("passedGroups", [])),
            "fixedSyntheticCaseCount": len(gate["result"].get("cases", [])), "counters": gate["counters"],
            "provenanceAfterOriginalFilename": gate["provenanceAfterFile"], "directArtifacts": "gates/" + name,
            "archive": archive["archive"], "archiveMembers": archive["decodedMembers"],
            "scopeAsReceived": gate["result"]["scope"]})
    h.copy(comparison_script, PACKET / "gates/fine-repair-controls-001/original-output-byte-comparison-executed.py")
    h.write_json(PACKET / "existing-comparison-byte-bindings.json", {"record": h.record(comparison_path),
        "executedScriptBeforeAsReceived": comparison["executedScriptBefore"], "retainedComparedArtifacts": comparison_bindings,
        "allMatched": True, "scope": "Bind original comparison records, script and retained output hashes; comparison not repeated"})
    h.write_json(PACKET / "archive-member-verification.json", {"archives": archives,
        "actualNativeSourceMembers": sum(len(gate["sourceIndex"]) for gate in collected.values()),
        "totalDecodedMembers": sum(archive["decodedMembers"] for archive in archives), "allCrcAndDecodedPayloadChecksPassed": True})
    h.write_json(PACKET / "summary.json", {"schema": "cl-mpm.mc-composite-apex.repair-gates.evidence.v1",
        "createdUtc": datetime.now(timezone.utc).isoformat(), "status": "FOUR_RELEVANT_GATES_PASS",
        "gates": summaries, "boundedOutputComparisonAsReceived": comparison,
        "fullRepairedFineSolverRun": "NOT_RUN", "actualOriginalFineFailureReplayCalls": 0,
        "landslideVerified": False, "scientificallyValidated": False,
        "operations": "Collect original four native gates and root's existing bounded comparison; no test/native/projector/MPM/replay/audit/render/PID operation repeated"})
    (PACKET / "README.md").write_text(
        "# Relevant optional composite-apex repair gates\n\n"
        "Four original native gates exit0:33fixed synthetic stable-arithmetic projector calls;15optional regression groups with38new pure/6strict comparator/10native calls;8NEW capture groups with6helper-only failures,7optional calls,2native calls,9replay attempts/2replay projector calls,1strict schema rejection/1synthetic strict delegate; and4fine-grid groups with2actual USF updates/7040accepted material calls/3520MPs/3VTKs/10560particle rows. The first three gates perform zero MPM updates. Every gate performs zero actual missing fine-run failure replay.\n\n"
        "Root's FIRST existing bounded comparison reports both CSVs and all3VTKs byte-identical to the original fine gate. Its exact executed script and before-execution hash remain. These bounded states contain zero active apex rows; they do not prove that the later failed fine trajectory will complete. No full repaired fine solver run, convergence, verified landslide or scientific validation is claimed.\n\n"
        "Each original native gate has one complete source ZIP and direct result/test/command/exit/log/source manifest/before-after proof/runtime records. Honest original provenance filenames are preserved: stable-regression and capture use source-provenance-after.json; stable-math and fine-repair use source-provenance.json. Gate source commits remain their original command attribution. Current-path source bindings are separate from original executed-source identity. Original protocols/input fixtures remain in each corresponding native ZIP; no old evidence ZIP is duplicated.\n\n"
        "Collector and reusable helper were copied and hashed BEFORE this collector execution. All archived members are CRC-tested, decoded and byte-compared; all1158source/input payloads bind to original preload and before/after hashes and each original stored mapped DLL record. Private caches are excluded. Collection makes no native/test/projector/MPM/replay/audit/render/process-query call; it does not repeat the root comparison. * -text preserves exact artifacts for independent staged-blob verification.\n",
        encoding="utf-8", newline="\n")
    artifacts = [h.record(path, PACKET) for path in sorted(PACKET.rglob("*")) if path.is_file()]
    h.write_json(PACKET / "artifact-index.json", {"schema": "cl-mpm.evidence.artifact-index.v1", "artifacts": artifacts,
        "note": "Index excludes itself. Four native source ZIPs, one per actual gate; original bytes preserved."})
    for row in artifacts:
        if h.record(PACKET / row["path"], PACKET) != row:
            raise RuntimeError("Indexed repair gate artifact changed")
    print(json.dumps({"packet": str(PACKET), "indexedArtifacts": len(artifacts), "nativeSources": 1158,
        "decodedZipMembers": sum(archive["decodedMembers"] for archive in archives), "gates": summaries}, indent=2))


if __name__ == "__main__":
    main()
