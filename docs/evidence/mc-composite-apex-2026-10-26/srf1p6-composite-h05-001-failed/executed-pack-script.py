"""Collect the existing failed h0.5 run and terminal saved review; execute none.

Run only after root has closed its ONE saved review/media and spatial review.
One native ZIP retains all source payloads; the closed launch ZIP is referenced.
"""
from datetime import datetime, timezone
import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "output/mc-composite-apex-2026-10-26"
NAME = "srf1p6-composite-h05-001"
RUN = RAW / NAME
STAGE = RAW / (NAME + "-launch-preparation")
LAUNCH = ROOT / "docs/evidence/unnotched-gravity-2026-10-26" / (NAME + "-launch")
PACKET = ROOT / "docs/evidence/mc-composite-apex-2026-10-26" / (NAME + "-failed")
HELPER = ROOT / ".tmp/pack-gravity-completed-002.py"
SOURCE_COMMIT = "a07eb8f8d8276a03a211266362518c323983ea13"
ERROR = "MC evolution integration failed: Composite apex compliance, flow, yield or work identity failed NIL"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-dir", type=Path, required=True)
    parser.add_argument("--review-exit", type=Path,
                        help="Existing outer exit JSON; default is RUN/<review-dir-name>.exit.json")
    parser.add_argument("--root-review", type=Path, default=RUN / "root-spatial-review.md")
    parser.add_argument("--comparison-dir", type=Path,
                        help="Optional existing saved-CSV comparison, retained as received")
    args = parser.parse_args()
    if PACKET.exists():
        raise RuntimeError("Preserve previous packet; no overwrite")
    spec = importlib.util.spec_from_file_location("_copy_hash_zip_helpers", HELPER)
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)  # Definitions only; guarded historical main does not run.
    h.PACKET = PACKET
    review_dir = args.review_dir.resolve()
    outer_path = (args.review_exit or RUN / (review_dir.name + ".exit.json")).resolve()
    root_review = args.root_review.resolve()
    if not review_dir.is_relative_to(RUN.resolve()) or not outer_path.is_relative_to(RUN.resolve()):
        raise RuntimeError("Review and authoritative exit must be retained within this native run")
    if not root_review.is_relative_to(RUN.resolve()) or not root_review.is_file():
        raise RuntimeError("Wait for root's retained terminal spatial-review note")
    manifest = h.read_json(RUN / "manifest.json")
    status = h.read_json(RAW / (NAME + "-status.json"))
    worker = h.read_json(RAW / (NAME + "-detached/worker-exit.json"))
    if not (status["status"] == "FAILED_NATIVE" and status["sourceCommit"] == SOURCE_COMMIT
            and status["nativeExitCode"] == worker["exitCode"] == 1
            and status["nativeComplete"] is False and manifest["complete"] is False
            and manifest["status"] == "failed" and manifest["timeS"] == 5.2
            and manifest["lastSavedTimeS"] == 5.2 and manifest["savedFrames"] == 53
            and manifest["particleCount"] == 3520 and manifest["updates"] == 13590
            and manifest["attemptTimeS"] == 5.27147981362577 and manifest["error"] == ERROR
            and status.get("endedUtc") and worker.get("finishedUtc")):
        raise RuntimeError("Original terminal failed-native scope differs")
    review = h.read_json(review_dir / "review.json")
    child_exit = h.read_json(review_dir / "child-exit.json")
    outer_exit = h.read_json(outer_path)
    if (not isinstance(child_exit.get("exitCode"), int)
            or outer_exit.get("exitCode") != child_exit["exitCode"]):
        raise RuntimeError("Wait for matching authoritative terminal review exits")
    if review.get("nativeComplete") is True or review.get("landslideVerified") is not False:
        raise RuntimeError("Partial failed run must not be reported complete or scientifically verified")
    if review.get("scientificallyValidated") is not False:
        raise RuntimeError("Scientific validation claim exceeds this evidence")

    checked_records = []
    def match_record(row, path=None):
        actual = h.record(path or Path(row["path"]))
        if actual["sha256"] != row["sha256"] or ("bytes" in row and actual["bytes"] != row["bytes"]):
            raise RuntimeError("Retained recorded bytes changed: " + actual["path"])
        checked_records.append(actual)
        return actual

    rows = h.read_json(RUN / "source/source-manifest.json")["files"]
    source_index = {row["path"]: row for row in rows}
    if len(rows) != 287 or len(source_index) != 287:
        raise RuntimeError("Expected exactly 287 original manifest-indexed sources")
    for row in rows:
        path = (RUN / row["path"]).resolve()
        if not path.is_relative_to((RUN / "source").resolve()):
            raise RuntimeError("Source path escapes this native snapshot")
        match_record(row, path)
    launch_rows = h.read_json(LAUNCH / "metadata/native-source-manifest-index.json")["files"]
    if {row["path"]: (row["bytes"], row["sha256"]) for row in launch_rows} != {
            name: (row["bytes"], row["sha256"]) for name, row in source_index.items()}:
        raise RuntimeError("Original launch and terminal source manifests differ")
    provenance = h.read_json(RUN / "source-provenance.json")
    dll = source_index["source/libs/kirchoff.dll"]
    backend = provenance["nativeBackend"]
    if not (provenance["sourceSnapshotExactLoadedBytes"] and provenance["copiedByteEqualityBeforeLoad"]
            and backend["sha256"] == dll["sha256"]
            and Path(backend["modulePath"]).resolve() == (RUN / dll["path"]).resolve()
            and backend["verifiedBy"] == "GetModuleHandleW/GetModuleFileNameW"):
        raise RuntimeError("Stored original runtime DLL/source-byte proof differs")
    prepared = h.read_json(STAGE / "prelaunch-snapshot.json")
    for row in prepared["frozenFiles"]:
        path = (STAGE / row["path"]).resolve()
        if not path.is_relative_to(STAGE.resolve()):
            raise RuntimeError("Prepared artifact path escapes original stage")
        match_record(row, path)
    for row in h.read_json(review_dir / "analysis-source-before.json"):
        match_record(row)
    for row in review.get("baseReview", {}).get("inputHashes", []) + review.get("media", []):
        match_record(row)

    # Preserve every native payload except private caches and separately retained analyses.
    analysis_roots = {p.name for p in RUN.glob("variant-review-*") if p.is_dir()}
    comparison_dir = args.comparison_dir.resolve() if args.comparison_dir else None
    if comparison_dir:
        if not comparison_dir.is_relative_to((ROOT / "output").resolve()) or not comparison_dir.is_dir():
            raise RuntimeError("Optional comparison must be existing workspace output")
        if comparison_dir.parent == RUN.resolve():
            analysis_roots.add(comparison_dir.name)
    native_members = {name: path for name, path in h.tree_files(RUN).items()
        if ".native-cache" not in Path(name).parts and Path(name).parts[0] not in analysis_roots
        and not Path(name).parts[0].startswith("variant-review-")}
    actual_source_names = {name for name in native_members
                           if name.startswith("source/") and name != "source/source-manifest.json"}
    if actual_source_names != set(source_index):
        raise RuntimeError("Complete native ZIP source membership differs from original manifest")
    runtime = {"adjacent/" + p.name: p for p in sorted(RAW.glob(NAME + "*")) if p.is_file()}
    runtime.update({"detached/" + name: path
                    for name, path in h.tree_files(RAW / (NAME + "-detached")).items()})
    native_members.update(runtime)
    analysis_members = {p.name + "/" + name: path for p in RUN.glob("variant-review-*") if p.is_dir()
                        for name, path in h.tree_files(p).items()}
    analysis_members.update({"caller/" + p.name: p for p in sorted(RUN.glob("variant-review-*.*")) if p.is_file()})
    if comparison_dir:
        analysis_members.update({"saved-comparison/" + name: path
                                for name, path in h.tree_files(comparison_dir).items()})
    launch_members = {"prelaunch-original/" + name: path for name, path in h.tree_files(STAGE).items()}
    omitted_archives = []
    for name, path in h.tree_files(LAUNCH).items():
        if path.suffix.lower() == ".zip":
            omitted_archives.append({**h.record(path), "reason": "Closed launch source ZIP referenced; current full native source archived once"})
        else:
            launch_members["closed-launch-metadata/" + name] = path
    for tree in (analysis_members, launch_members):
        if any(name.endswith("source/source-manifest.json") or path.suffix.lower() == ".zip"
               for name, path in tree.items()):
            raise RuntimeError("Analysis/prelaunch metadata must not embed native source archives")
    failure_candidates = [name for name in native_members
        if not name.startswith(("source/", "adjacent/", "detached/"))
        and any(token in Path(name).name.lower() for token in ("capsule", "failure", "error"))]

    PACKET.mkdir(parents=True)
    (PACKET / ".gitattributes").write_bytes(b"* -text\n*.zip binary\n")
    h.copy(Path(__file__), PACKET / "executed-pack-script.py")
    h.copy(HELPER, PACKET / "executed-copy-hash-zip-helpers.py")
    h.write_json(PACKET / "packaging-invocation.json", {"argv": sys.argv,
        "createdUtc": datetime.now(timezone.utc).isoformat(),
        "scope": "Copy/hash/ZIP/CRC/decoded-byte collection only; no native, test, replay, audit, render or process query"})
    archives = [h.archive("complete-native-source-raw-runtime-and-failure", native_members),
                h.archive("terminal-saved-variant-review", analysis_members),
                h.archive("original-prelaunch-and-closed-launch-metadata", launch_members)]
    decoded = {row["path"]: row for row in archives[0]["members"]}
    for name, expected in source_index.items():
        if (decoded[name]["bytes"], decoded[name]["sha256"]) != (expected["bytes"], expected["sha256"]):
            raise RuntimeError("Archived source differs from original pre-load manifest")
    for name in ("manifest.json", "source-provenance.json"):
        h.copy(RUN / name, PACKET / "native" / name)
    h.copy(RUN / "source/source-manifest.json", PACKET / "metadata/native-source-manifest-index.json")
    h.copy(root_review, PACKET / "native" / root_review.name)
    for name, path in runtime.items():
        h.copy(path, PACKET / "native" / name)
    for name, path in analysis_members.items():
        if "actual-frames" not in Path(name).parts:
            h.copy(path, PACKET / "saved-analysis" / name)
    h.write_json(PACKET / "recorded-byte-bindings.json", {"records": checked_records, "allMatched": True,
        "originalRuntimeBackendAsRecorded": backend,
        "scope": "Original stored pre-load source/runtime records bound to retained bytes; no after-exit module mapping or saved-state reanalysis"})
    h.write_json(PACKET / "closed-launch-packet-reference.json", {
        "originalIndex": h.record(LAUNCH / "artifact-index.json"), "omittedOriginalSourceArchives": omitted_archives,
        "scope": "Selected original launch metadata retained; full original source ZIP remains in its closed packet, referenced without duplicate payload"})
    h.write_json(PACKET / "archive-member-verification.json", {"archives": archives,
        "actualNativeSourceMembers": len(rows), "totalDecodedMembers": sum(row["decodedMembers"] for row in archives),
        "allCrcAndDecodedPayloadChecksPassed": True})
    summary = {"schema": "cl-mpm.gravity-composite-apex.failed.evidence.v1",
        "createdUtc": datetime.now(timezone.utc).isoformat(), "nativeSourceCommit": SOURCE_COMMIT,
        "nativeExit": 1, "workerExit": 1, "nativeComplete": False,
        "nativeEndedUtc": status["endedUtc"], "workerFinishedUtc": worker["finishedUtc"],
        "lastSavedTimeS": manifest["lastSavedTimeS"], "manifestTimeS": manifest["timeS"],
        "attemptTimeS": manifest["attemptTimeS"], "savedFrames": manifest["savedFrames"],
        "particleCount": manifest["particleCount"], "manifestUpdates": manifest["updates"],
        "nativeError": manifest["error"], "nativeSourceFiles": len(rows),
        "savedReviewExit": outer_exit, "savedReviewIntegrityAsReceived": review.get("integrityStatus"),
        "savedReviewNativeCompleteAsReceived": review.get("nativeComplete"),
        "savedReviewErrorAsReceived": review.get("error"), "savedMediaAsReceived": review.get("media", []),
        "nativeFailureNamedArtifactCandidates": failure_candidates,
        "failureSearchScope": "This run's retained native output filenames only, excluding source, analysis and adjacent/detached metadata; no old trees searched",
        "failureReplay": "NOT_RUN; manifest records an error/attempt clock, not a serialized failed constitutive input; no capsule or failed-particle state invented",
        "updateScope": "Manifest counter includes unsaved evolution after lastSavedTimeS; it is not 13590 saved-state transitions or evidence that the failed global step committed",
        "physicalResultScope": "Partial53-state saved review and root spatial note only; failure at5.27147981362577s prevents complete0-6s fine comparison or convergence claim",
        "landslideVerified": False, "scientificallyValidated": False,
        "operations": "Read/copy/hash/ZIP/CRC/decoded-byte comparison only; no native/gate/launch/audit/render/replay/comparison or obsolete PID query"}
    h.write_json(PACKET / "summary.json", summary)
    (PACKET / "README.md").write_text(
        "# Failed h0.5 optional composite-apex SRF1.6 attempt\n\n"
        "Native and worker exit1 on26October2026 at13:06:10WIB. Manifest is failed/complete=false:53saved states through5.2s,3520MPs,13590updates including unsaved evolution, attemptTimeS5.27147981362577. Exact native error: " + ERROR + ". The attempt clock is not a saved failed-particle capsule or proof of a committed failed global step.\n\n"
        "Original287pre-load source payloads, mapped-DLL provenance, raw VTK/CSV, manifest, modern adjacent/detached logs and original launch references are retained. Stored runtime mapping is preserved as recorded; no process is queried after exit. ONE source ZIP carries every native payload exactly once. The closed launch source ZIP is referenced by hash.\n\n"
        "The terminal saved variant review, its original exit/failures, prepared analysis/protocol bytes, all saved-frame PNGs and existing media are retained as received. Root's spatial interpretation is included. Collection does not rerun review, rendering, decoding, comparison, tests, material calls or native integration. Partial motion cannot establish completion, full-window refinement/convergence, verified landslide or scientific validation.\n\n"
        "All ZIP members are CRC-tested, decoded and byte-compared; source payloads bind to the original pre-load manifest and stored DLL record. Private native/Python caches are excluded. Original output and private data remain untouched. * -text preserves artifact bytes; independently verify any staged Git blobs.\n",
        encoding="utf-8", newline="\n")
    artifacts = [h.record(path, PACKET) for path in sorted(PACKET.rglob("*")) if path.is_file()]
    h.write_json(PACKET / "artifact-index.json", {"schema": "cl-mpm.evidence.artifact-index.v1", "artifacts": artifacts,
        "note": "Index excludes itself. Single full native-source ZIP; original launch source archive referenced. Explicitly stage ignored indexed media."})
    for row in artifacts:
        if h.record(PACKET / row["path"], PACKET) != row:
            raise RuntimeError("Indexed artifact changed")
    print(json.dumps({"packet": str(PACKET), "indexedArtifacts": len(artifacts),
        "decodedZipMembers": sum(row["decodedMembers"] for row in archives), "nativeSources": len(rows),
        "archives": [{"name": row["archive"]["path"], "members": row["decodedMembers"]} for row in archives],
        "nativeComplete": False, "landslideVerified": False}, indent=2))


if __name__ == "__main__":
    main()
