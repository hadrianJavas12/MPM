"""Archive completed default controls only; repeat no native/test/comparison."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "output/mc-composite-apex-2026-10-25"
PACKET = RAW / "default-compatibility-evidence-001"
HELPER = ROOT / ".tmp/pack-gravity-completed-002.py"


def main():
    if PACKET.exists():
        raise RuntimeError("Preserve prior packet")
    spec = importlib.util.spec_from_file_location("_copy_hash_zip_helpers", HELPER)
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)
    h.PACKET = PACKET
    names = ("default-strict34-001", "default-output-001")
    results, sources, members = {}, {}, {}
    for name in names:
        run = RAW / name
        exit_record = h.read_json(RAW / (name + "-exit.json"))
        verification = h.read_json(run / "post-run-source-runtime-verification.json")
        if exit_record["exitCode"] != 0 or verification["status"] != "PASS":
            raise RuntimeError("Do not relabel a failed default gate as successful")
        for row in h.read_json(run / "source/source-manifest.json")["files"]:
            actual = h.record(run / row["path"])
            if (actual["bytes"], actual["sha256"]) != (row["bytes"], row["sha256"]):
                raise RuntimeError("Frozen source changed before collection")
        results[name] = verification["nativeResult"]
        sources[name] = verification["sourceCount"]
        members.update({name + "/" + key: value for key, value in h.tree_files(run).items()
                        if ".native-cache" not in Path(key).parts})
        members.update({"adjacent/" + path.name: path for path in sorted(RAW.glob(name + "*")) if path.is_file()})
    comparison = h.read_json(RAW / "default-output-001/comparison-to-default-strict-baseline.json")
    if comparison["status"] != "PASS" or len(comparison["comparedFiles"]) != 5:
        raise RuntimeError("Default compatibility requires all five exact byte matches")
    PACKET.mkdir()
    (PACKET / ".gitattributes").write_bytes(b"* -text\n*.zip binary\n")
    h.copy(Path(__file__), PACKET / "executed-pack-script.py")
    h.copy(HELPER, PACKET / "executed-copy-hash-zip-helpers.py")
    support = ("plan-mc-default-compatibility.json", "run-mc-default-compatibility.ps1",
               "run-frozen-mc-regression.lisp", "verify-mc-default-compatibility.py", "compare-mc-default-hook-output.py")
    for name in support:
        h.copy(ROOT / ".tmp" / name, PACKET / "execution-support" / name)
    archive = h.archive("exact-default-source-native-output-runtime-and-comparison", members)
    for name in names:
        run = RAW / name
        for file in ("result.json", "post-run-source-runtime-verification.json"):
            h.copy(run / file, PACKET / name / file)
        for path in sorted(RAW.glob(name + "*")):
            if path.is_file():
                h.copy(path, PACKET / "adjacent" / path.name)
    h.copy(RAW / "default-output-001/comparison-to-default-strict-baseline.json", PACKET / "exact-byte-comparison.json")
    h.write_json(PACKET / "archive-member-verification.json", {"archives": [archive],
        "sourceFilesByControl": sources, "totalDecodedMembers": archive["decodedMembers"],
        "allCrcAndDecodedPayloadChecksPassed": True})
    h.write_json(PACKET / "summary.json", {"createdUtc": datetime.now(timezone.utc).isoformat(),
        "sourceCheckpoint": "ac767e10e2856195aab4c51fade2d11c6cf70c61", "status": "PASS",
        "existingStrictGroupsPassed": results[names[0]]["passedCount"],
        "boundedGroupsPassed": results[names[1]]["passedCount"],
        "genuineMpmUpdates": results[names[1]]["physicalUpdatesExecuted"],
        "boundedMaterialCallsAttempted": results[names[1]]["materialCallsAttempted"],
        "boundedMaterialCallsAccepted": results[names[1]]["materialCallsAccepted"],
        "frozenSourceCounts": sources, "exactOutputFilesMatched": 5,
        "defaultOptionalCompositeLoaded": False, "strictProjectorUnchanged": True,
        "landslideVerified": False, "scientificallyValidated": False,
        "scope": "Default dispatch compatibility only. Existing34 tests plus existing four output groups with2USF updates. New optional model/output and full slope not invoked by this gate.",
        "packagingOperations": "Read/copy/hash/ZIP/CRC/all-member decoded-byte comparison only; no numerical or saved-analysis execution repeated"})
    (PACKET / "README.md").write_text(
        "# Default strict material dispatch compatibility\n\n"
        "Existing unchanged34 point/native/framework/transaction controls and existing four bounded output groups pass once each on sourceac767e1. The bounded fixture executes2genuine USF updates and1760 accepted material calls; all3VTKs and2CSVs match the retained strict pre-hook baseline byte for byte.\n\n"
        "Both native runtimes freeze exact sources/inputs/DLL before loading; before/after proof and current copied/original hashes are retained. The strict projector hash is unchanged and optional composite model/diagnostic components do not occur in loaded ASDF action records. Copying those optional source files into the snapshot is not loading the model.\n\n"
        "Actual commands are recorded before each invocation with logs/exits retained. The old34 bootstrap's native manifest and recorded snapshot checks provide its pre-load hash proof; explicit per-file before/after JSON is also retained where emitted by the bounded fixture. No independent external pre-run reads are invented.\n\n"
        "This is default compatibility evidence, not optional composite material validation, full-slope instability, landslide or scientific validation. Original outputs remain untouched. Private caches are excluded; every archive member is CRC-tested, decoded and byte-compared. No numerical/test/replay/render execution is repeated during packaging.\n",
        encoding="utf-8", newline="\n")
    files = [h.record(path, PACKET) for path in sorted(PACKET.rglob("*")) if path.is_file()]
    h.write_json(PACKET / "artifact-index.json", {"schema": "cl-mpm.evidence.artifact-index.v1", "artifacts": files,
        "note": "Index excludes itself. Packet stays under output for root review; * -text preserves exact bytes if moved/staged."})
    for row in files:
        if h.record(PACKET / row["path"], PACKET) != row:
            raise RuntimeError("Indexed byte mismatch")
    print(json.dumps({"packet": str(PACKET), "indexedArtifacts": len(files),
        "decodedZipMembers": archive["decodedMembers"], "frozenSources": sources, "status": "PASS"}))


if __name__ == "__main__":
    main()
