"""Collect existing completed native/variant/prefix evidence; run none of it.

Requires root's terminal review/prefix approval. One source ZIP for the current
native run; the closed launch packet's source ZIP is referenced, not duplicated.
"""
from datetime import datetime, timezone
import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "output/mc-composite-apex-2026-10-26"
NAME = "srf1p6-composite-001"
RUN = RAW / NAME
STAGE = RAW / (NAME + "-launch-preparation")
LAUNCH = ROOT / "docs/evidence/unnotched-gravity-2026-10-26" / (NAME + "-launch")
PACKET = ROOT / "docs/evidence/mc-composite-apex-2026-10-26" / (NAME + "-completed")
HELPER = ROOT / ".tmp/pack-gravity-completed-002.py"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-dir", type=Path, required=True)
    parser.add_argument("--prefix-dir", type=Path, required=True)
    parser.add_argument("--prefix-result", type=Path, required=True)
    parser.add_argument("--prefix-exit", type=Path,
                        help="Optional existing authoritative exit if stored separately")
    args = parser.parse_args()
    if PACKET.exists():
        raise RuntimeError("Preserve previous packet; no overwrite")
    spec = importlib.util.spec_from_file_location("_copy_hash_zip_helpers", HELPER)
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)  # Definitions only; guarded historical main does not run.
    h.PACKET = PACKET
    review_dir, prefix_dir = args.review_dir.resolve(), args.prefix_dir.resolve()
    if not review_dir.is_relative_to(RUN.resolve()) or not prefix_dir.is_relative_to((ROOT / "output").resolve()):
        raise RuntimeError("Existing review/prefix directories must be workspace output artifacts")
    manifest, status = h.read_json(RUN / "manifest.json"), h.read_json(RAW / (NAME + "-status.json"))
    worker = h.read_json(RAW / (NAME + "-detached/worker-exit.json"))
    terminal_path = RUN / "terminal-native-source-runtime-verification.json"
    terminal = h.read_json(terminal_path)
    if not (status["status"] == "NATIVE_COMPLETE_REVIEW_PENDING" and status["nativeExitCode"] == worker["exitCode"] == 0
            and status["nativeComplete"] and manifest["complete"] is True and manifest["timeS"] == 6
            and manifest["savedFrames"] == 61 and manifest["particleCount"] == 880 and manifest["updates"] == 7740
            and terminal["status"] == "PASS" and terminal["allTerminalHashesMatchOriginalPreloadManifest"]):
        raise RuntimeError("Original completed native scope/closed terminal proof differs")
    source_rows = h.read_json(RUN / "source/source-manifest.json")["files"]
    source_index = {row["path"]: row for row in source_rows}
    if len(source_index) != len(source_rows) or len(source_rows) != terminal["sourceCount"]:
        raise RuntimeError("Original native source membership differs from closed terminal proof")
    if {row["path"]: (row["bytes"], row["sha256"]) for row in terminal["files"]} != {
            key: (row["bytes"], row["sha256"]) for key, row in source_index.items()}:
        raise RuntimeError("Original source manifest differs from closed terminal source list")
    review = h.read_json(review_dir / "review.json")
    child_exit = h.read_json(review_dir / "child-exit.json")
    review_outer = h.read_json(RUN / (review_dir.name + ".exit.json"))
    if not (child_exit["exitCode"] == review_outer["exitCode"] == 0 and review["integrityStatus"] == "PASS"
            and review["nativeComplete"] and not review["boundedControlOnly"] and review["analysisSourceAfterMatch"]
            and review["sourceVerification"]["status"] == "PASS"
            and review["sourceVerification"]["frozenSourcesVerified"] == len(source_rows)
            and review["landslideVerified"] is False and review["scientificallyValidated"] is False):
        raise RuntimeError("Full actual independent variant review is not terminal/pass in declared scope")
    checked_records = []
    def match_record(row, path=None):
        path = path or Path(row["path"])
        actual = h.record(path)
        if actual["sha256"] != row["sha256"] or ("bytes" in row and actual["bytes"] != row["bytes"]):
            raise RuntimeError("Retained executed/reviewed artifact changed: " + str(path))
        checked_records.append(actual)
    for row in h.read_json(review_dir / "analysis-source-before.json"):
        match_record(row)
    for row in review["baseReview"]["inputHashes"] + review["media"]:
        match_record(row)
    video = next((row for row in review["media"] if row["path"].lower().endswith(".mp4")), None)
    if not (video and video["actualSavedStates"] == 61 and video["fullDecodeExit"] == 0
            and video["playbackFramesPerSecond"] == 4 and video["deformationMagnification"] == 1
            and video["interpolation"] is False):
        raise RuntimeError("Existing actual61-state scale1/full-decode media proof is incomplete")
    prefix = h.read_json(args.prefix_result)
    prefix_exit = h.read_json(args.prefix_exit) if args.prefix_exit else None
    if prefix_exit is not None and prefix_exit.get("exitCode") is None:
        raise RuntimeError("Prefix exit proof is not terminal")
    first_exit_path = RUN / "variant-review-001.exit.json"
    first_exit = h.read_json(first_exit_path)
    if first_exit["exitCode"] != 2 or (RUN / "variant-review-001").exists():
        raise RuntimeError("Preserved first caller failure no longer has its known before-Python scope")
    if not STAGE.is_dir() or not LAUNCH.is_dir():
        raise RuntimeError("Original prepared and closed launch records are missing")

    # Native ZIP carries the current run's complete source exactly once.
    analysis_roots = {p.name for p in RUN.glob("variant-review-*") if p.is_dir()}
    if prefix_dir.parent == RUN.resolve():
        analysis_roots.add(prefix_dir.name)
    native_members = {name: path for name, path in h.tree_files(RUN).items()
        if ".native-cache" not in Path(name).parts and Path(name).parts[0] not in analysis_roots
        and not Path(name).parts[0].startswith("variant-review-")}
    runtime = {"adjacent/" + p.name: p for p in sorted(RAW.glob(NAME + "*")) if p.is_file()}
    runtime.update({"detached/" + name: path for name, path in h.tree_files(RAW / (NAME + "-detached")).items()})
    native_members.update(runtime)
    if "root-spatial-review.md" not in native_members:
        raise RuntimeError("Root's completed spatial-review note must be retained")
    if sum(name.endswith("source/source-manifest.json") for name in native_members) != 1:
        raise RuntimeError("Exactly one native source manifest required in the full native archive")
    analysis_members = {p.name + "/" + name: path for p in RUN.glob("variant-review-*") if p.is_dir()
                        for name, path in h.tree_files(p).items()}
    analysis_members.update({"caller/" + p.name: p for p in sorted(RUN.glob("variant-review-*.*")) if p.is_file()})
    prefix_members = {"prefix/" + name: path for name, path in h.tree_files(prefix_dir).items()}
    if not args.prefix_result.resolve().is_relative_to(prefix_dir):
        prefix_members["prefix-adjacent/" + args.prefix_result.name] = args.prefix_result
    if args.prefix_exit and not args.prefix_exit.resolve().is_relative_to(prefix_dir):
        prefix_members["prefix-adjacent/" + args.prefix_exit.name] = args.prefix_exit
    launch_members = {"prelaunch-original/" + name: path for name, path in h.tree_files(STAGE).items()}
    omitted_source_archives = []
    for name, path in h.tree_files(LAUNCH).items():
        if path.suffix.lower() == ".zip":
            omitted_source_archives.append({**h.record(path), "reason": "Closed launch source archive referenced by hash; source payload not duplicated in completion packet"})
        else:
            launch_members["closed-launch-metadata/" + name] = path
    for tree in (analysis_members, prefix_members, launch_members):
        if any(name.endswith("source/source-manifest.json") for name in tree):
            raise RuntimeError("Metadata/analysis/prefix archives must not duplicate native source manifests")
    PACKET.mkdir(parents=True)
    (PACKET / ".gitattributes").write_bytes(b"* -text\n*.zip binary\n")
    h.copy(Path(__file__), PACKET / "executed-pack-script.py")
    h.copy(HELPER, PACKET / "executed-copy-hash-zip-helpers.py")
    h.write_json(PACKET / "packaging-invocation.json", {"argv": sys.argv, "createdUtc": datetime.now(timezone.utc).isoformat(),
        "scope": "Copy/hash/archive collection only; no solver/test/replay/audit/render or process query"})
    archives = [h.archive("complete-native-source-raw-runtime-and-terminal-proof", native_members),
                h.archive("actual-frozen-variant-review-and-negative-caller", analysis_members),
                h.archive("existing-prefix-comparison", prefix_members),
                h.archive("original-prelaunch-and-closed-launch-metadata", launch_members)]
    # Verify the archive's actual source payloads against the CLOSED terminal
    # source proof; this is collection binding, not a repeat verifier invocation.
    decoded = {row["path"]: row for row in archives[0]["members"]}
    for name, expected in source_index.items():
        actual = decoded.get(name)
        if not actual or (actual["bytes"], actual["sha256"]) != (expected["bytes"], expected["sha256"]):
            raise RuntimeError("Archived source differs from original terminal proof")
    for name in ("manifest.json", "source-provenance.json", "terminal-native-source-runtime-verification.json"):
        h.copy(RUN / name, PACKET / "native" / name)
    for name, path in runtime.items():
        h.copy(path, PACKET / "native" / name)
    h.copy(RUN / "source/source-manifest.json", PACKET / "metadata/native-source-manifest-index.json")
    for name, path in {**analysis_members, **prefix_members}.items():
        if "actual-frames" not in Path(name).parts:
            h.copy(path, PACKET / "saved-analysis-and-prefix" / name)
    h.write_json(PACKET / "closed-launch-packet-reference.json", {
        "originalIndex": h.record(LAUNCH / "artifact-index.json"), "omittedOriginalSourceArchives": omitted_source_archives,
        "scope": "Closed launch packet is referenced, not claimed wholly copied. Selected launch metadata and its original index remain in metadata ZIP; full current native snapshot exists once in this packet. Prior closed gate/launch checks are not rerun."})
    h.write_json(PACKET / "recorded-review-byte-bindings.json", {"records": checked_records,
        "allMatched": True, "scope": "Existing hashes and original payloads matched; no state analysis/media decoding repeated"})
    h.write_json(PACKET / "archive-member-verification.json", {"archives": archives,
        "actualNativeSourceMembers": len(source_rows), "totalDecodedMembers": sum(row["decodedMembers"] for row in archives),
        "allCrcAndDecodedPayloadChecksPassed": True})
    h.write_json(PACKET / "summary.json", {"schema": "cl-mpm.gravity-composite-apex.completed.evidence.v1",
        "createdUtc": datetime.now(timezone.utc).isoformat(), "nativeSourceCommit": status["sourceCommit"],
        "nativeExit": 0, "workerExit": 0, "nativeComplete": True, "physicalTimeS": 6,
        "savedFrames": 61, "particleCount": 880, "acceptedUpdates": 7740, "nativeSourceFiles": len(source_rows),
        "terminalSourceProof": h.record(terminal_path), "actualReviewExit": review_outer,
        "firstCallerExit": first_exit, "firstCallerFailureScope": "PowerShell array concatenation formed an invalid Python script path before Python opened the intended script; no first analysis directory",
        "savedIntegrity": review["integrityStatus"], "boundedControlOnly": False,
        "rootSpatialReviewIncluded": True,
        "postRunDiagnosisIncluded": "post-run-diagnosis-001.md" in native_members,
        "media": video, "prefixResultAsReceived": prefix, "prefixExitAsReceived": prefix_exit,
        "physicalResultScope": "Use existing root physical/spatial review; native completion and reader integrity are not motion/runout/scientific validation",
        "landslideVerified": False, "scientificallyValidated": False,
        "operations": "Read/copy/hash/ZIP/CRC/all-member decoded-byte comparison only; native/gate/launch/audit/render/comparison and PID queries not repeated"})
    (PACKET / "README.md").write_text(
        "# Full optional composite-apex SRF1.6 run: completed native evidence\n\n"
        "Original native and worker exit0;6physical seconds,61actual saved states,880particles and7740updates. Original source287/runtime/case/configuration, raw CSV/VTK, modern logs/status/launch, detached exit and separate closed terminal proof are retained. Native runtime provenance was written before the solver; the separate terminal file proof checks original pre-load hashes afterward without inventing an after-runtime mapping.\n\n"
        "The FIRST review caller fails before Python opens its intended script from malformed PowerShell argument concatenation; its command/log/exit2 remain. The next full frozen variant review succeeds on actual saved states and four copied analysis sources, with an actual61-state4fps/15.25s scale1 video, no interpolation, recorded full-decode0. The collector does not review, render or decode it again. Prefix result and any negative findings are preserved as received without changing tolerances or imposing a pass.\n\n"
        "One ZIP contains the current complete native source manifest and every original payload. Closed launch source ZIP is referenced by hash, avoiding duplicate native source payload; selected original prelaunch/launch metadata and historical index are explicitly metadata references. All archive members are CRC-tested, decoded and byte-compared; source payload hashes bind to the closed terminal proof. Originals remain untouched and private caches are excluded.\n\n"
        "This is an explicitly changed volumetric apex-flow material, not unchanged strict MC, a fracture model, paper reproduction, verified landslide or scientific validation. Root owns physical/spatial interpretation and further scientific gates. * -text preserves exact artifact bytes; verify staged blobs independently.\n",
        encoding="utf-8", newline="\n")
    artifacts = [h.record(path, PACKET) for path in sorted(PACKET.rglob("*")) if path.is_file()]
    h.write_json(PACKET / "artifact-index.json", {"schema": "cl-mpm.evidence.artifact-index.v1", "artifacts": artifacts,
        "note": "Index excludes itself. One complete native-source ZIP; closed launch source payload referenced only. Explicitly stage ignored indexed media."})
    for row in artifacts:
        if h.record(PACKET / row["path"], PACKET) != row:
            raise RuntimeError("Indexed artifact changed")
    print(json.dumps({"packet": str(PACKET), "indexedArtifacts": len(artifacts),
        "decodedZipMembers": sum(row["decodedMembers"] for row in archives), "nativeSources": len(source_rows),
        "archives": [{"name": row["archive"]["path"], "members": row["decodedMembers"]} for row in archives],
        "nativeComplete": True, "landslideVerified": False}, indent=2))


if __name__ == "__main__":
    main()
