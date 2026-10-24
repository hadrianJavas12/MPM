"""Package completed scoped MC fix controls. No tests, replay or analysis run."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import zipfile


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "output/unnotched-gravity-2026-10-25"
PACKET = ROOT / "docs/evidence/unnotched-gravity-2026-10-25/complementarity-fix-controls"
ATTEMPTS = {"mc-regression-001": 283, "complementarity-controls-001": 284,
            "native-output-fixed-001": 285}
PROJECTION = "source/materials/models/plastic/mohr-coulomb-evolution/projection.lisp"
PROJECTOR_SHA = "e26b736914a8fa2cc3f4eb7f6619c1331e787f72d365d5bb7c0a5b3f4d8ceda1"


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def record(path, root=None):
    payload = Path(path).read_bytes()
    return {"path": Path(path).relative_to(root).as_posix() if root else str(path),
            "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                    encoding="utf-8", newline="\n")


def copy(source, destination):
    if destination.exists():
        raise RuntimeError(f"Refuse overwrite: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    if source.read_bytes() != destination.read_bytes():
        raise RuntimeError(f"Copy mismatch: {source}")


def archive_attempt(name, expected_count):
    attempt, target = RAW / name, PACKET / name
    manifest = read_json(attempt / "source/source-manifest.json")
    expected = {row["path"]: row for row in manifest["files"]}
    if len(expected) != expected_count or len(manifest["files"]) != expected_count:
        raise RuntimeError(f"Wrong/duplicate source members: {name}")
    for relative, row in expected.items():
        source = (attempt / relative).resolve()
        if not source.is_relative_to((attempt / "source").resolve()):
            raise RuntimeError("Source member escaped immutable source directory")
        actual = record(source)
        if (actual["sha256"], actual["bytes"]) != (row["sha256"], row["bytes"]):
            raise RuntimeError(f"Executed frozen source mismatch: {name}/{relative}")
    if expected[PROJECTION]["sha256"] != PROJECTOR_SHA:
        raise RuntimeError(f"Executed projection differs: {name}")
    proofs = {}
    for phase in ("before", "after"):
        path = attempt / f"source-proof-{phase}.json"
        if path.exists():
            proof = read_json(path)
            if {row["path"]: row["sha256"] for row in proof["files"]} != {
                    relative: row["sha256"] for relative, row in expected.items()}:
                raise RuntimeError(f"Original source proof mismatch: {name}/{phase}")
            proofs[phase] = {"status": "PASS", "members": len(expected), "file": record(path)}
        else:
            proofs[phase] = {"status": "NAMED_FILE_NOT_RETAINED",
                             "scope": "Original regression wrapper uses native provenance plus result copied-test/hash verification. No missing standalone file is invented."}
    runtime = {}
    for filename in ("source-provenance-before.json", "source-provenance.json"):
        path = attempt / filename
        provenance = read_json(path)
        if not (provenance["sourceSnapshotExactLoadedBytes"] and provenance["copiedByteEqualityBeforeLoad"]):
            raise RuntimeError(f"Native source runtime proof false: {name}/{filename}")
        if set(provenance["copiedFiles"]) != set(expected):
            raise RuntimeError(f"Native runtime source set differs: {name}/{filename}")
        backend = provenance["nativeBackend"]
        if (backend["sha256"] != expected["source/libs/kirchoff.dll"]["sha256"]
                or backend["verifiedBy"] != "GetModuleHandleW/GetModuleFileNameW"):
            raise RuntimeError(f"Actual mapped DLL proof differs: {name}/{filename}")
        runtime[filename] = {"sourceSnapshotExactLoadedBytes": True,
                             "copiedByteEqualityBeforeLoad": True, "backend": backend,
                             "file": record(path)}
    members = {relative: attempt / relative for relative in expected}
    members["source/source-manifest.json"] = attempt / "source/source-manifest.json"
    for source in sorted(attempt.rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(attempt)
        if "source" in relative.parts or "__pycache__" in relative.parts or source.suffix == ".pyc":
            continue
        members[relative.as_posix()] = source
    for suffix in (".log", "-exit.json"):
        members["adjacent/native" + suffix] = RAW / (name + suffix)
    target.mkdir(parents=True)
    archive = target / "executed-source-output-and-runtime.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zipped:
        for relative, source in sorted(members.items()):
            zipped.write(source, relative)
    decoded = []
    with zipfile.ZipFile(archive) as zipped:
        if zipped.testzip() is not None or sorted(zipped.namelist()) != sorted(members):
            raise RuntimeError(f"ZIP CRC/member failure: {name}")
        for relative, source in sorted(members.items()):
            payload = zipped.read(relative)
            if payload != source.read_bytes():
                raise RuntimeError(f"Decoded source/raw bytes changed: {relative}")
            decoded.append({"path": relative, "bytes": len(payload),
                            "sha256": hashlib.sha256(payload).hexdigest()})
    for source in sorted(attempt.glob("*")):
        if source.is_file():
            copy(source, target / source.name)
    copy(attempt / "source/source-manifest.json", target / "source/source-manifest.json")
    for suffix in (".log", "-exit.json"):
        copy(RAW / (name + suffix), target / ("native" + suffix))
    return {"attempt": name, "sourceFiles": len(expected), "decodedMembers": len(decoded),
            "archive": record(archive, PACKET), "crcPass": True, "decodedBytesMatchOriginals": True,
            "projectionSha256": expected[PROJECTION]["sha256"], "originalSourceProofs": proofs,
            "nativeRuntimeProof": runtime, "members": decoded}, expected


def main():
    if PACKET.exists() or not PACKET.resolve().is_relative_to(ROOT.resolve()):
        raise RuntimeError("Packet destination must be fresh and inside workspace")
    regression = read_json(RAW / "mc-regression-001/result.json")
    focused = read_json(RAW / "complementarity-controls-001/result.json")
    native = read_json(RAW / "native-output-fixed-001/result.json")
    comparison = read_json(RAW / "native-output-fixed-001/comparison-to-pre-fix.json")
    if not regression["passed"] or regression["passedCount"] != 34 or not regression["allSourceHashesVerifiedAfter"]:
        raise RuntimeError("Existing MC regression is not retained PASS34")
    if (not focused["passed"] or len(focused["passedGroups"]) != 8 or focused["explicitNewFixedPointCalls"] != 61
            or focused["oldBaselineReplayCalls"] != 0 or focused["physicalUpdatesExecuted"] != 0):
        raise RuntimeError("Focused fixed-code controls scope changed")
    if (not native["passed"] or native["passedCount"] != 4 or native["physicalUpdatesExecuted"] != 2
            or native["materialCallsAccepted"] != 1760):
        raise RuntimeError("Narrow native output is not expected PASS4/2updates/1760calls")
    if comparison["status"] != "PASS" or len(comparison["comparedFiles"]) != 5:
        raise RuntimeError("Root's retained output comparison is not PASS5")
    current = record(ROOT / PROJECTION.removeprefix("source/"))
    if current["sha256"] != PROJECTOR_SHA:
        raise RuntimeError("Current projector differs from all executed fixed-code snapshots")
    PACKET.mkdir(parents=True)
    (PACKET / ".gitattributes").write_bytes(b"* -text\n*.zip binary\n")
    copy(Path(__file__), PACKET / "executed-pack-script.py")
    archives, sources = [], {}
    for name, count in ATTEMPTS.items():
        verified, source = archive_attempt(name, count)
        archives.append(verified)
        sources[name] = source
    old_test = sources["mc-regression-001"]["source/case.lisp"]
    if not (old_test["sha256"] == regression["originalTestSha256"] == regression["copiedTestSha256"]):
        raise RuntimeError("Original old34 test bytes differ from executed source case")
    for relative in ("source/case.lisp", "source/control-bootstrap.lisp"):
        copy(RAW / "mc-regression-001" / relative, PACKET / "mc-regression-001" / relative)
    baseline_packet = ROOT / "docs/evidence/unnotched-gravity-2026-10-24/native-controls"
    for source in sorted((baseline_packet / "native-controls-002-independent-review").glob("*")):
        if source.is_file():
            copy(source, PACKET / "reference-pre-fix-independent-review" / source.name)
    for filename in ("review-gravity-slope.py", "plot_m5_cliff_comparison.py"):
        source = baseline_packet / "analysis-and-process-support/scripts" / filename
        copy(source, PACKET / "reference-pre-fix-independent-review/analysis-support" / filename)
    copy(baseline_packet / "analysis-provenance-limits.json",
         PACKET / "reference-pre-fix-independent-review/inherited-analysis-provenance-limits.json")
    write_json(PACKET / "archive-member-verification.json", {"archives": archives,
               "totalExecutedSourceEntries": sum(row["sourceFiles"] for row in archives),
               "totalDecodedMembers": sum(row["decodedMembers"] for row in archives),
               "allCrcAndDecodedPayloadChecksPassed": True})
    write_json(PACKET / "summary.json", {
        "schema": "cl-mpm.mc-complementarity-fix-controls.evidence.v1",
        "createdUtc": datetime.now(timezone.utc).isoformat(), "status": "FOCUSED_FIX_GATES_PASS",
        "existingMcPointSuite": {"passed": 34, "originalNumericalTestBytesUnchanged": True,
                                "actualExecutedTest": old_test, "bootstrapRetained": "mc-regression-001/source/control-bootstrap.lisp"},
        "newFixedCodeControls": focused,
        "narrowNativeOutput": native,
        "originalPreFixOutputComparison": comparison,
        "projection": {"currentWorkingFile": current, "allThreeExecutedHashesIdentical": True,
                       "sha256": PROJECTOR_SHA},
        "oldBaselineActualCapsuleReplayCallsInThisPacket": 0,
        "fullPostFixSlopeRunsInThisPacket": 0,
        "landslideVerified": False, "scientificallyValidated": False,
        "scope": "Tightened stress-dimensional negative-multiplier acceptance. Existing shared admissibility and Wang behavior unchanged. No relaxation of stress/history/dedup tolerances or strength/psi/rate changes.",
        "analysisFailureRetained": "Initial comparison wildcard included mesh.vtk and stopped at assertion before producing a result; corrected particle-only comparison reran saved-byte comparison only, zero native repeats.",
        "referenceReviewScope": "Retained pre-fix independent review only. New two-update files are byte-identical; no new independent reader run is claimed.",
        "packagingOperations": "Read/copy/hash/ZIP/CRC/decode verification only; no native tests, replay, renderer, solver or saved-data analysis executed"})
    (PACKET / "README.md").write_text(
        "# Scoped MC complementarity fix: native controls\n\n"
        "The fixed projection adds a conservative Kirchhoff-stress/yield-plane bound for negative flow multipliers. "
        "Stress/history/dedup tolerances, physical inputs and the shared admissible-candidate predicate remain unchanged; "
        "the separate Wang point/apex acceptance paths are not newly filtered. This is an acceptance tightening, "
        "not a clamp, root preference or claim of global uniqueness.\n\n"
        "Three completed Windows-native gates are retained: the original unchanged34-point suite, eight focused groups "
        "with61 NEW fixed-code pure calls and one native constitutive call, and four narrow output groups recording "
        "two genuine MPM updates/1760 accepted material calls/three saved states. The61 calls are not repetitions of the "
        "old failing-code capsule replay, which belongs to the earlier negative-evidence packet. No full post-fix slope "
        "or verified landslide is included here.\n\n"
        "The three archives contain283/284/285 immutable executed source files respectively, with source manifests, "
        "available before/after hash proofs, source-provenance, mapped DLL identity, logs, exits and outputs. "
        "Every archive member is CRC-tested, decoded and compared byte for byte to originals. All three projection "
        "hashes match the current fixed file. The old34 case and actual control bootstrap are also directly accessible. "
        "That regression wrapper has no separately named source-proof-before/after files: its copied-byte/runtime "
        "provenance and original allSourceHashesVerifiedAfter result are preserved, not replaced with invented files.\n\n"
        "The new three particle VTK states and two CSV files are byte-identical to the previously independently "
        "audited pre-fix two-update output. Root's exact comparison script/result are retained, together with the initial "
        "wildcard-selection script and assertion failure. Selecting mesh.vtk with the three particle states caused that "
        "analysis harness failure before any result; correcting selection repeated no native work. "
        "The pre-fix review, analysis support and inherited provenance limitations are reference evidence, not a newly "
        "executed saved-data review.\n\n"
        "Completion of these small gates proves neither full-ramp stability nor coherent slope failure, calibrated "
        "runout or journal agreement. Packaging itself performs only file operations and archive verification.\n",
        encoding="utf-8", newline="\n")
    artifacts = [record(path, PACKET) for path in sorted(PACKET.rglob("*")) if path.is_file()]
    write_json(PACKET / "artifact-index.json", {"schema": "cl-mpm.evidence.artifact-index.v1", "artifacts": artifacts,
               "note": "Index excludes itself; * -text preserves raw bytes. Force-add intended ignored media/VTK and verify staged Git blobs before committing."})
    for expected in artifacts:
        if record(PACKET / expected["path"], PACKET) != expected:
            raise RuntimeError(f"Final indexed artifact changed: {expected['path']}")
    print(json.dumps({"packet": str(PACKET), "indexedArtifacts": len(artifacts),
                      "executedSourceEntries": sum(row["sourceFiles"] for row in archives),
                      "decodedZipMembers": sum(row["decodedMembers"] for row in archives),
                      "status": "FOCUSED_FIX_GATES_PASS"}, indent=2))


if __name__ == "__main__":
    main()
