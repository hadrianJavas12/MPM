"""Read/copy/hash/ZIP the two actual framework attempts; no numerical calls."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "output/mc-composite-apex-2026-10-26"
PACKET = ROOT / "docs/evidence/mc-composite-apex-2026-10-26/framework-output-controls"
HELPER = ROOT / ".tmp/pack-gravity-completed-002.py"
RUNNER = ROOT / ".tmp/run-native-gate.ps1"
spec = importlib.util.spec_from_file_location("apex_framework_copy_helpers", HELPER)
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)
common.PACKET = PACKET
load, record, copy, write = common.read_json, common.record, common.copy, common.write_json


def checked_attempt(name, expected_exit):
    run = RAW / name
    result, exit_record = load(run / "result.json"), load(RAW / (name + ".exit.json"))
    if exit_record["exitCode"] != expected_exit:
        raise RuntimeError("Unexpected actual native exit")
    rows = load(run / "source/source-manifest.json")["files"]
    sources = {row["path"]: row for row in rows}
    if len(rows) != 289 or len(sources) != 289:
        raise RuntimeError("Expected289 distinct exact native/source/input members")
    for relative, expected in sources.items():
        source = (run / relative).resolve()
        if not source.is_relative_to((run / "source").resolve()):
            raise RuntimeError("Frozen source escapes source tree")
        actual = record(source)
        if (actual["sha256"], actual["bytes"]) != (expected["sha256"], expected["bytes"]):
            raise RuntimeError("Current immutable source differs from pre-load manifest")
    wanted = {name: row["sha256"] for name, row in sources.items()}
    for phase in ("before", "after"):
        proof = load(run / f"source-proof-{phase}.json")["files"]
        if len(proof) != len(rows) or {row["path"]: row["sha256"] for row in proof} != wanted:
            raise RuntimeError("Source before/after proof mismatch")
    provenance = load(run / "source-provenance.json")
    before = load(run / "source-provenance-before.json")
    expected_dll = (run / "source/libs/kirchoff.dll").resolve()
    for proof in (before, provenance):
        backend = proof["nativeBackend"]
        if not (proof["sourceSnapshotExactLoadedBytes"] and proof["copiedByteEqualityBeforeLoad"]
                and Path(backend["modulePath"]).resolve() == expected_dll
                and backend["sha256"] == sources["source/libs/kirchoff.dll"]["sha256"]
                and backend["verifiedBy"] == "GetModuleHandleW/GetModuleFileNameW"
                and backend["nativeMcEntryPresent"]):
            raise RuntimeError("Mapped DLL/loading proof mismatch")
    if result["nativeBackend"] != provenance["nativeBackend"]:
        raise RuntimeError("Result/runtime mapped DLL records differ")
    return run, result, sources, provenance, exit_record


def main():
    if PACKET.exists() or not PACKET.resolve().is_relative_to(ROOT.resolve()):
        raise RuntimeError("Evidence packet must be fresh inside workspace")
    first = checked_attempt("framework-output-001", 1)
    second = checked_attempt("framework-output-002", 0)
    a, b = first[1], second[1]
    if (a["passed"] or a["passedGroups"] != ["optional-framework-loading-and-unique-diagnostics"]
            or a["physicalUpdatesExecuted"] != 0 or a["materialCallsAttempted"] != 0
            or a["pointNativeCallsAttempted"] != 1 or a["pointNativeCallsAccepted"] != 1
            or a["failure"] != ["point-apex-diagnostic-storage-and-postcommit-q",
                                 "Unsupported bootstrap JSON value 2.721539030917347e-4"]):
        raise RuntimeError("First actual harness failure must remain explicit")
    remaining = ["point-apex-diagnostic-storage-and-postcommit-q",
                 "two-genuine-usf-updates-with-readonly-exports",
                 "independent-vtk-csv-finite-F-J-mass-IDs-and-q"]
    if (not b["passed"] or b["passedGroups"] != remaining or b["mode"] != "remaining"
            or b["skippedGroups"] != a["passedGroups"] or b["physicalUpdatesExecuted"] != 2
            or b["materialCallsAttempted"] != 64 or b["materialCallsAccepted"] != 64
            or b["pointNativeCallsAttempted"] != 1 or b["pointNativeCallsAccepted"] != 1):
        raise RuntimeError("Expected exact selective closure, not an old-group repeat")
    s1, s2 = first[2], second[2]
    if s1.keys() != s2.keys():
        raise RuntimeError("Frozen source sets differ beyond the harness correction")
    differences = [name for name in sorted(s1) if
                   (s1[name]["sha256"], s1[name]["bytes"]) != (s2[name]["sha256"], s2[name]["bytes"])]
    if differences != ["source/case.lisp"]:
        raise RuntimeError("Expected harness-only source change; numerical sources must match")
    workspace_rows = []
    for relative, row in s2.items():
        actual = record(Path(row["originalPath"]))
        if (actual["sha256"], actual["bytes"]) != (row["sha256"], row["bytes"]):
            raise RuntimeError("Current original source differs from selective executed snapshot")
        workspace_rows.append({"frozenPath": relative, "originalCurrent": actual,
                               "matchesAttempt002": True,
                               "matchesAttempt001": row["sha256"] == s1[relative]["sha256"]})
    command = load(RAW / "framework-output-002.command.json")
    if command["runnerSha256"].lower() != record(RUNNER)["sha256"]:
        raise RuntimeError("Actual command helper changed")
    PACKET.mkdir(parents=True)
    (PACKET / ".gitattributes").write_bytes(b"* -text\n*.zip binary\n")
    copy(Path(__file__), PACKET / "executed-pack-script.py")
    copy(HELPER, PACKET / "executed-pack-copy-helpers.py")
    copy(RUNNER, PACKET / "actual-attempt002-command-helper.ps1")
    archives, summaries = [], []
    for attempt in (first, second):
        run, result, sources, provenance, exit_record = attempt
        label = run.name
        members = {relative: run / relative for relative in sources}
        members["source/source-manifest.json"] = run / "source/source-manifest.json"
        direct = {name: path for name, path in common.tree_files(run).items() if not name.startswith("source/")}
        for name, path in direct.items():
            members[name] = path
        for suffix in (".command.json", ".exit.json", ".log"):
            path = RAW / (label + suffix)
            members["adjacent/" + path.name] = direct["adjacent/" + path.name] = path
        archive = common.archive(label + "-complete-source-and-output", members)
        archives.append(archive)
        for name, path in direct.items():
            copy(path, PACKET / label / name)
        for relative in ("source/source-manifest.json", "source/case.lisp",
                         "source/inputs/PERFECT_MC_APEX_PLAN.md", "source/inputs/PERFECT_MC_APEX_REVIEW.md"):
            copy(run / relative, PACKET / label / relative)
        write(PACKET / label / "archive-member-verification.json", archive)
        summaries.append({"attempt": label, "nativeExit": exit_record["exitCode"],
                          "result": result, "frozenSources": len(sources),
                          "allFrozenCurrentBytesBeforeAfterMatch": True,
                          "actualMappedDll": provenance["nativeBackend"],
                          "archive": archive["archive"], "decodedMembers": archive["decodedMembers"]})
    write(PACKET / "source-comparison-and-original-current-proof.json", {
        "comparedSourceFilesPerAttempt": len(s2), "onlyChangedFrozenPath": differences,
        "unchangedProductionAndDesignFiles": len(s2) - len(differences),
        "harnessAttempt001Sha256": s1["source/case.lisp"]["sha256"],
        "harnessAttempt002Sha256": s2["source/case.lisp"]["sha256"],
        "allOriginalCurrentBytesMatchSelectiveAttempt002": True,
        "scope": "All original/current first-party/input bytes match002;001 differs solely by deliberately corrected harness. Original001 snapshot remains unchanged.",
        "files": workspace_rows})
    write(PACKET / "summary.json", {"schema": "cl-mpm.mc-composite-apex.framework-output.evidence.v1",
        "createdUtc": datetime.now(timezone.utc).isoformat(), "attempts": summaries,
        "combinedDistinctGroupsPassed": 4, "firstFailureRetained": True,
        "totalActualMpmUpdatesAcrossAttempts": 2, "totalMpmConstitutiveAccepted": 64,
        "separateNativeApexAcceptedAcrossAttempts": 2,
        "successfulFixture": {"particles": 32, "savedVtkStates": 3, "perParticleCsvRows": 96,
                              "aggregateCsvRows": 3, "oldPassedFirstGroupRepeated": False},
        "tinyMpmApexActivationRequired": False, "fullSlopeExecutedByThisPacket": False,
        "landslideVerified": False, "scientificallyValidated": False,
        "operations": "Read/copy/hash/ZIP/CRC/decoded-byte verification only. No test, material, MPM, replay, rendering or analysis rerun."})
    (PACKET / "README.md").write_text(
        "# Optional composite-apex framework output controls\n\n"
        "Attempt001 exits1 after its optional-framework/unique-diagnostics group passes. Its one native apex call is accepted; float JSON serialization in the harness then fails. It executes zero MPM updates. The original failure, compile warning, exact source and runtime proofs remain intact.\n\n"
        "Attempt002 uses the corrected test only: runtime floats use Yason, a CSV helper arity is corrected, and explicit remaining mode skips the previously passed first group while retaining necessary output setup. All three remaining groups pass, native exit0. It executes exactly two real USF updates on32MPs with64accepted material calls, retains three particle VTKs,96per-particle CSV rows and3production aggregate diagnostic rows. Its separate native apex fixture proves last q/active survives commit with consistent plastic volume/work. Ordinary tiny compressive MPM is not required or claimed to activate apex.\n\n"
        "Each archive contains exactly one complete289-file source/input/DLL manifest plus that attempt's actual source bytes, logs, command, exit, proof and raw output. All current frozen bytes and before/after hashes agree; mapped DLL identity is verified. The only source difference between attempts is source/case.lisp;288production/design files are identical. Current original files match002;001's old harness is deliberately retained.\n\n"
        "Archive CRC and every decoded member match the originals byte for byte. Original raw files remain in output/. Byte-preserving attributes and the artifact index support staged-blob verification. Packaging repeats no numerical work and establishes no full slope, landslide or scientific validation.\n",
        encoding="utf-8", newline="\n")
    files = [record(path, PACKET) for path in sorted(PACKET.rglob("*")) if path.is_file()]
    write(PACKET / "artifact-index.json", {"schema": "cl-mpm.evidence.artifact-index.v1", "artifacts": files,
         "note": "Index excludes itself. Every ZIP has one source-manifest; preserve indexed ignored VTKs with * -text."})
    for row in files:
        if record(PACKET / row["path"], PACKET) != row:
            raise RuntimeError("Indexed artifact changed")
    print(json.dumps({"packet": str(PACKET), "indexedArtifacts": len(files),
                      "sourceFilesEach": len(s2), "archiveMembers": [row["decodedMembers"] for row in archives],
                      "allCrcAndDecodedBytesVerified": True, "onlyChangedSource": differences}))


if __name__ == "__main__":
    main()
