"""Collect completed scenario gates and their retained failures; no reruns."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "output/mc-composite-apex-2026-10-26"
PACKET = ROOT / "docs/evidence/mc-composite-apex-2026-10-26/scenario-integration-controls"
HELPER = ROOT / ".tmp/pack-gravity-completed-002.py"
NAMES = [f"scenario-controls-{i:03d}" for i in (1, 2, 3)]
RUNNERS = ["run-native-gate.ps1", "run-native-saved-gate.ps1", "run-native-saved-gate-003.ps1"]


def main():
    if PACKET.exists():
        raise RuntimeError("Preserve prior packet; refuse overwrite")
    spec = importlib.util.spec_from_file_location("_copy_hash_zip_helpers", HELPER)
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)  # Definitions only; no historical main executed.
    h.PACKET = PACKET
    native, native_trees, source_indexes, checked_sources = {}, {}, {}, {}
    for name, runner in zip(NAMES, RUNNERS):
        run = RAW / name
        result = h.read_json(run / "result.json")
        outer_exit = h.read_json(RAW / (name + ".exit.json"))
        command = h.read_json(RAW / (name + ".command.json"))
        if h.record(ROOT / ".tmp" / runner)["sha256"] != command["runnerSha256"].lower():
            raise RuntimeError("Actual invocation helper differs from recorded executed bytes")
        rows = h.read_json(run / "source/source-manifest.json")["files"]
        index = {row["path"]: row for row in rows}
        if len(index) != len(rows):
            raise RuntimeError("Duplicate native source member")
        checks = []
        for relative, row in index.items():
            path = (run / relative).resolve()
            if not path.is_relative_to((run / "source").resolve()):
                raise RuntimeError("Source escapes native snapshot")
            actual = h.record(path)
            if (actual["bytes"], actual["sha256"]) != (row["bytes"], row["sha256"]):
                raise RuntimeError("Original native source changed")
            checks.append({"path": relative, "bytes": actual["bytes"], "sha256": actual["sha256"]})
        for phase in ("before", "after"):
            proof = h.read_json(run / f"source-proof-{phase}.json")["files"]
            if len(proof) != len(index) or {row["path"]: row["sha256"] for row in proof} != {key: row["sha256"] for key, row in index.items()}:
                raise RuntimeError("Native before/after source hashes disagree")
        for filename in ("source-provenance-before.json", "source-provenance.json"):
            proof = h.read_json(run / filename)
            backend = proof["nativeBackend"]
            dll = run / "source/libs/kirchoff.dll"
            if not (proof["sourceSnapshotExactLoadedBytes"] and proof["copiedByteEqualityBeforeLoad"]
                    and set(proof["copiedFiles"]) == set(index)
                    and Path(backend["modulePath"]).resolve() == dll.resolve()
                    and backend["verifiedBy"] == "GetModuleHandleW/GetModuleFileNameW"
                    and backend["sha256"] == h.record(dll)["sha256"]):
                raise RuntimeError("Native actual loaded-source/mapped-DLL proof disagrees")
        native[name] = {"launcherExit": outer_exit, "command": command, "result": result,
                        "sourceCount": len(rows), "sourceBeforeAfterAndCurrentMatched": True}
        source_indexes[name], checked_sources[name] = index, checks
        # Review and its outer command/log/exit belong only in analysis bundle.
        native_trees[name] = {key: path for key, path in h.tree_files(run).items()
                              if ".native-cache" not in Path(key).parts
                              and not Path(key).parts[0].startswith("variant-review-")}
        native_trees[name].update({"adjacent/" + path.name: path for path in sorted(RAW.glob(name + ".*")) if path.is_file()})
    r1, r2, r3 = [native[name]["result"] for name in NAMES]
    if not (native[NAMES[0]]["launcherExit"]["exitCode"] == 1 and not r1["passed"]
            and r1["passedGroups"] == ["strict-default", "optional-input", "reject-hidden-inputs", "short-output"]
            and r1["failure"][0] == "saved-output" and r1["physicalUpdatesExecuted"] == 2
            and r1["materialCallsAttempted"] == r1["materialCallsAccepted"] == 1760):
        raise RuntimeError("First reader failure/complete short-run distinction changed")
    if not (native[NAMES[1]]["launcherExit"]["exitCode"] == 1 and not r2["passed"]
            and r2["selectedGroups"] == ["saved-output"] and r2["physicalUpdatesExecuted"] == 0
            and r2["materialCallsAttempted"] == r2["materialCallsAccepted"] == 0
            and Path(r2["observations"]["observationsDirectory"]).resolve() == (ROOT / "read-only").resolve()):
        raise RuntimeError("Second zero-update command-tokenization failure changed")
    observations = RAW / NAMES[0] / "observations"
    if not (native[NAMES[2]]["launcherExit"]["exitCode"] == 0 and r3["passed"]
            and r3["selectedGroups"] == r3["passedGroups"] == ["saved-output", "read-only"]
            and r3["physicalUpdatesExecuted"] == 0 and r3["materialCallsAttempted"] == r3["materialCallsAccepted"] == 0
            and Path(r3["observations"]["observationsDirectory"]).resolve() == observations.resolve()):
        raise RuntimeError("Third saved-only reader/read-only scope differs")
    if any(row["result"]["standaloneConstitutiveCallsAttempted"] or row["result"]["standaloneConstitutiveCallsAccepted"] for row in native.values()):
        raise RuntimeError("Unexpected standalone constitutive invocation")
    tiny = h.read_json(observations / "manifest.json")
    if not (tiny["complete"] is True and tiny["updates"] == 2 and tiny["savedFrames"] == 3 and tiny["particleCount"] == 880):
        raise RuntimeError("Original short solver output is not complete")

    python_trees, synthetic = {}, {}
    for name, expected, wrapper in (("analysis-controls-001", 11, "run-frozen-apex-review-tests.py"),
                                     ("binding-controls-001", 3, "run-frozen-apex-binding-tests.py")):
        directory = RAW / name
        result = h.read_json(directory / "result.json")
        records = h.read_json(directory / "source-before.json")
        if not (result["exitCode"] == 0 and result["copiedSourcesUnchanged"] and result["currentSourcesMatch"]
                and result["sourceCount"] == len(records) == 5 and result["nativeCalls"] == 0):
            raise RuntimeError("Original synthetic invocation did not complete its narrow scope")
        if f"Ran {expected} tests" not in (directory / "stderr.log").read_text() or "\nOK\n" not in (directory / "stderr.log").read_text():
            raise RuntimeError("Actual synthetic test count/terminal log differs")
        for row in records:
            actual = h.record(directory / "source" / row["path"])
            if (actual["bytes"], actual["sha256"]) != (row["bytes"], row["sha256"]):
                raise RuntimeError("A historical synthetic source copy changed")
        synthetic[name] = {"testCount": expected, "result": result, "copiedSourcesVerified": 5,
                            "scope": "Each invocation retains its own historical copied version; not assumed identical to later reviewer"}
        python_trees.update({name + "/" + key: path for key, path in h.tree_files(directory).items()})
        python_trees[name + "/received-orchestration.py"] = ROOT / ".tmp" / wrapper
    review_dir = RAW / NAMES[0] / "variant-review-001"
    review = h.read_json(review_dir / "review.json")
    outer_review_exit = h.read_json(RAW / NAMES[0] / "variant-review-001.exit.json")
    if not (outer_review_exit["exitCode"] == h.read_json(review_dir / "child-exit.json")["exitCode"] == 0
            and review["integrityStatus"] == "PASS" and review["nativeComplete"] and review["boundedControlOnly"]
            and review["analysisSourceAfterMatch"] and review["sourceVerification"]["status"] == "PASS"
            and review["sourceVerification"]["frozenSourcesVerified"] == native[NAMES[0]]["sourceCount"]
            and review["landslideVerified"] is False and review["scientificallyValidated"] is False):
        raise RuntimeError("Actual independent bounded variant review differs")
    records = h.read_json(review_dir / "analysis-source-before.json")
    for row in records:
        if hashlib.sha256(Path(row["path"]).read_bytes()).hexdigest() != row["sha256"]:
            raise RuntimeError("Actual executed analysis source changed")
    raw_checks = []
    for row in review["baseReview"]["inputHashes"] + review["media"]:
        actual = h.record(Path(row["path"]))
        if actual["sha256"] != row["sha256"] or ("bytes" in row and actual["bytes"] != row["bytes"]):
            raise RuntimeError("Original reviewed state/media bytes changed")
        raw_checks.append({"path": row["path"], "bytes": actual["bytes"], "sha256": actual["sha256"]})
    python_trees.update({"actual-variant-review-001/" + key: path for key, path in h.tree_files(review_dir).items()})
    for path in sorted((RAW / NAMES[0]).glob("variant-review-001.*")):
        if path.is_file():
            python_trees["actual-variant-review-001/adjacent/" + path.name] = path
    # Preserve unchanged root-verifier convention: at most one native source
    # manifest per archive, accompanied by every one of its original payloads.
    if any(key.endswith("source/source-manifest.json") for key in python_trees):
        raise RuntimeError("Analysis bundle must not duplicate a native source manifest")

    PACKET.mkdir(parents=True)
    (PACKET / ".gitattributes").write_bytes(b"* -text\n*.zip binary\n")
    h.copy(Path(__file__), PACKET / "executed-pack-script.py")
    h.copy(HELPER, PACKET / "executed-copy-hash-zip-helpers.py")
    h.write_json(PACKET / "packaging-invocation.json", {"argv": sys.argv, "createdUtc": datetime.now(timezone.utc).isoformat(),
        "scope": "FIRST collector invocation only; no numerical/test/audit/render invocation"})
    archives = []
    for name, runner in zip(NAMES, RUNNERS):
        tree = native_trees[name]
        if sum(key.endswith("source/source-manifest.json") for key in tree) != 1:
            raise RuntimeError("Native archive must have exactly one complete source manifest")
        archives.append(h.archive(name + "-full-source-and-native-evidence", tree))
        h.copy(ROOT / ".tmp" / runner, PACKET / "execution-support" / runner)
        for filename in ("result.json", "source-proof-before.json", "source-proof-after.json"):
            h.copy(RAW / name / filename, PACKET / name / filename)
        for path in sorted(RAW.glob(name + ".*")):
            if path.is_file():
                h.copy(path, PACKET / "adjacent" / path.name)
    archives.append(h.archive("synthetic-and-actual-frozen-variant-review", python_trees))
    for name, path in python_trees.items():
        if "analysis-source" not in Path(name).parts and "source" not in Path(name).parts:
            h.copy(path, PACKET / "analysis" / name)
    h.write_json(PACKET / "native-source-verification.json", {"filesByAttempt": checked_sources,
        "countsByAttempt": {name: len(rows) for name, rows in checked_sources.items()},
        "allBeforeAfterAndRetainedCopiedHashesMatched": True,
        "originalReviewedStateAndMediaBytesUnchanged": raw_checks,
        "scope": "Existing immutable records and current retained file hash/length checks only; no earlier source version reconstructed from current workspace"})
    h.write_json(PACKET / "archive-member-verification.json", {"archives": archives,
        "sourceFilesByAttempt": {name: row["sourceCount"] for name, row in native.items()},
        "totalDecodedMembers": sum(row["decodedMembers"] for row in archives), "allCrcAndDecodedPayloadChecksPassed": True})
    h.write_json(PACKET / "summary.json", {"schema": "cl-mpm.gravity-composite-apex.scenario-controls.evidence.v1",
        "createdUtc": datetime.now(timezone.utc).isoformat(), "nativeAttempts": native,
        "originalShortSolverComplete": True, "totalGenuineMpmUpdatesAcrossAttempts": 2,
        "shortMaterialCallsAttempted": 1760, "shortMaterialCallsAccepted": 1760,
        "zeroUpdateReaderAttempts": [NAMES[1], NAMES[2]], "finalReaderGroups": r3["passedGroups"],
        "syntheticControls": synthetic, "actualIndependentReviewExit": outer_review_exit,
        "actualIndependentReviewIntegrity": review["integrityStatus"], "actualAnalysisSourceCopies": len(records),
        "actualReviewedSavedStates": review["baseReview"]["savedFrames"],
        "readerFailure001": "Harness requested nonexistent2D VTK zz/yz/xz fields; underlying2USF/3-state runner completed",
        "argumentFailure002": "Unquoted comma was tokenized by WindowsCMD; read-only became observations arg; zero MPM/material calls",
        "repair003": "Single-token saved alias and absolute original observations; saved-output/read-only pass with zero new MPM/material calls",
        "landslideVerified": False, "scientificallyValidated": False,
        "scope": "Focused optional gravity integration, exact input/default compatibility, genuine short output and independent saved-reader verification; not full slope, forced MPM apex activation, paper reproduction or physical slide validation",
        "operations": "Read/copy/hash/ZIP/CRC/all-member decoded-byte comparison only; no numerical/test/analysis/render repeated"})
    (PACKET / "README.md").write_text(
        "# Optional composite-apex gravity scenario integration gates\n\n"
        "Only attempt001 executes2genuine USF steps on880particles,1760 accepted material calls and3saved states. Its underlying runner complete=true; the test launcher exits1 because its saved reader incorrectly requested nonexistent2D VTK zz/yz/xz fields. This is a test-oracle failure, not a solver failure.\n\n"
        "Attempt002 executes zero MPM/material calls and fails from WindowsCMD splitting an unquoted comma selector, so read-only became the observations argument. Attempt003 uses single-token saved plus the absolute ORIGINAL observations path, passes saved-output/read-only and executes zero new MPM/material calls. All earlier sources, failures, commands and logs remain retained.\n\n"
        "The two pure Python invocations pass11and3synthetic controls with five copied sources each. Each invocation retains its own historical source version. The FIRST frozen actual variant reviewer independently passes original001observations and source/DLL/binding/currentJ/metadata integrity, with a real scale1 PNG inspected by root. Its complete flag describes only the tiny underlying runner, not the failed001test launcher. Four actual analysis-source copies, outer/child exits and logs are retained.\n\n"
        "Three separate native ZIPs each contain exactly one original source manifest and its full indexed payloads. The separate analysis ZIP contains no native source manifest. All ZIP members are CRC-tested, decoded and byte-compared; private caches are excluded. Originals remain untouched. This collection repeats no solver, replay, test, audit or rendering. * -text preserves exact bytes.\n\n"
        "This closes focused integration/reader controls, with no guaranteed MPM apex activation, full-slope run, paper reproduction, landslide or scientific validation claim. Root must independently verify staged Git blobs before commit.\n",
        encoding="utf-8", newline="\n")
    artifacts = [h.record(path, PACKET) for path in sorted(PACKET.rglob("*")) if path.is_file()]
    h.write_json(PACKET / "artifact-index.json", {"schema": "cl-mpm.evidence.artifact-index.v1", "artifacts": artifacts,
        "note": "Index excludes itself; raw bytes protected by * -text. <=1 native source manifest per ZIP."})
    for row in artifacts:
        if h.record(PACKET / row["path"], PACKET) != row:
            raise RuntimeError("Final indexed artifact changed")
    print(json.dumps({"packet": str(PACKET), "indexedArtifacts": len(artifacts),
        "decodedZipMembers": sum(row["decodedMembers"] for row in archives),
        "nativeSourceCounts": {name: row["sourceCount"] for name, row in native.items()},
        "archives": [{"name": row["archive"]["path"], "members": row["decodedMembers"]} for row in archives],
        "totalGenuineMpmUpdates": 2, "landslideVerified": False}, indent=2))


if __name__ == "__main__":
    main()
