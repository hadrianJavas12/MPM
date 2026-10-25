"""Package terminal baseline native/review/paired files; no numerical execution."""
from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "output/unnotched-gravity-2026-10-25"
RUN = RAW / "srf1-001"
REVIEW = RUN / "review-001"
PACKET = ROOT / "docs/evidence/unnotched-gravity-2026-10-25/srf1-001-completed"
PRIOR = ROOT / "docs/evidence/unnotched-gravity-2026-10-25/srf1p4-002-completed"
HELPER = ROOT / ".tmp/pack-gravity-completed-002.py"

# Import only read/copy/hash/ZIP utilities. The helper's main() is not invoked.
spec = importlib.util.spec_from_file_location("gravity_packet_copy_helpers", HELPER)
common = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(common)
common.PACKET = PACKET
common.RUN = RUN
record = common.record
read_json = common.read_json
write_json = common.write_json
copy = common.copy
tree_files = common.tree_files


def main() -> None:
    if len(sys.argv) != 3:
        raise RuntimeError("Provide completed PAIRED_DIRECTORY and its summary JSON filename")
    paired_dir = (ROOT / sys.argv[1]).resolve()
    paired_name = sys.argv[2]
    if not paired_dir.is_relative_to(RAW.resolve()) or Path(paired_name).name != paired_name:
        raise RuntimeError("Paired evidence must remain inside intended output directory")
    pair = read_json(paired_dir / paired_name)
    pair_exit = read_json(paired_dir / "comparison-exit.json")
    pair_pre = read_json(paired_dir / "comparison-pre-execution.json")
    pair_script = record(paired_dir / "compare-srf-pair.py")
    if pair_exit["exitCode"] != 0 or pair_script["sha256"] != pair_pre["scriptSha256"]:
        raise RuntimeError("Wait for terminal paired comparison and unchanged pre-execution script")
    if (pair_script["bytes"], pair_script["sha256"]) != (pair["comparisonScript"]["bytes"], pair["comparisonScript"]["sha256"]):
        raise RuntimeError("Exact paired comparison source differs from result provenance")
    if PACKET.exists() or not PACKET.resolve().is_relative_to(ROOT.resolve()):
        raise RuntimeError("Baseline evidence packet must be fresh inside workspace")
    manifest = read_json(RUN / "manifest.json")
    status = read_json(RAW / "srf1-001-status.json")
    review = read_json(REVIEW / "review.json")
    review_exit = read_json(REVIEW / "review-exit.json")
    source_members = common.immutable_sources()
    if (not manifest["complete"] or manifest["timeS"] != 6.0 or manifest["savedFrames"] != 61
            or manifest["particleCount"] != 880 or manifest["updates"] != 7740
            or manifest["config"]["strengthReductionFactor"] != 1.0
            or status["nativeExitCode"] != 0 or not status["nativeComplete"]):
        raise RuntimeError("Native baseline does not have expected complete scope")
    if review_exit["exitCode"] != 0 or not review["nativeComplete"] or review["savedFrames"] != 61:
        raise RuntimeError("Wait for terminal baseline saved-data review")
    provenance = read_json(RUN / "source-provenance.json")
    dll = record(RUN / "source/libs/kirchoff.dll")
    if (not provenance["sourceSnapshotExactLoadedBytes"] or not provenance["copiedByteEqualityBeforeLoad"]
            or provenance["nativeBackend"]["sha256"] != dll["sha256"]):
        raise RuntimeError("Exact loaded-byte/native DLL provenance mismatch")
    pre_execution = read_json(REVIEW / "analysis-pre-execution.json")
    for row in pre_execution["sourceCopies"]:
        p = REVIEW / "analysis-support" / Path(row["path"]).name
        actual = record(p)
        if (actual["bytes"], actual["sha256"]) != (row["bytes"], row["sha256"]):
            raise RuntimeError("Baseline review source differs from pre-execution capture")
    media = next((m for m in review["media"] if m["path"].endswith(".mp4")), None)
    if (not media or media["fullDecodeExit"] != 0 or media["actualSavedStates"] != 61
            or media["playbackFramesPerSecond"] != 4 or media["deformationMagnification"] != 1
            or media["interpolation"]):
        raise RuntimeError("Baseline actual-state media evidence scope mismatch")
    for item in review["media"]:
        actual = record(REVIEW / Path(item["path"]).name)
        if (actual["bytes"], actual["sha256"]) != (item["bytes"], item["sha256"]):
            raise RuntimeError("Baseline media bytes differ from saved review")
    prior_index = read_json(PRIOR / "artifact-index.json")
    for row in prior_index["artifacts"]:
        actual = record(PRIOR / row["path"], PRIOR)
        if actual != row:
            raise RuntimeError("Referenced prior reduced-run evidence artifact changed")

    PACKET.mkdir(parents=True)
    (PACKET / ".gitattributes").write_bytes(b"* -text\n*.zip binary\n")
    copy(Path(__file__), PACKET / "executed-pack-script.py")
    copy(HELPER, PACKET / "executed-pack-copy-helpers.py")
    members = dict(source_members)
    for name in ["source/source-manifest.json", "source-provenance.json", "manifest.json", "history.csv", "particles.csv"]:
        members[name] = RUN / name
    members.update({"vtk/" + p.name: p for p in sorted((RUN / "vtk").glob("*.vtk"))})
    if len(list((RUN / "vtk").glob("particles_*.vtk"))) != 61:
        raise RuntimeError("Baseline particle VTK state count differs")
    runtime = {"adjacent/" + p.name: p for p in sorted(RAW.glob("srf1-001*")) if p.is_file()}
    runtime.update({"detached/" + name: p for name, p in tree_files(RAW / "srf1-001-detached").items()})
    runtime["prelaunch/baseline-input-comparison.json"] = RAW / "baseline-input-comparison.json"
    members.update(runtime)
    archives = [common.archive("baseline-native-source-raw-and-runtime", members)]
    review_members = {"review/" + k: v for k, v in tree_files(REVIEW).items()}
    pair_members = {"paired/" + k: v for k, v in tree_files(paired_dir).items()}
    archives.append(common.archive("baseline-saved-review-and-paired", {**review_members, **pair_members}))
    for name in ["manifest.json", "source-provenance.json", "source/source-manifest.json"]:
        copy(RUN / name, PACKET / "native" / name)
    for name, source in runtime.items():
        copy(source, PACKET / "native" / name)
    for name, source in tree_files(REVIEW).items():
        if "actual-frames" not in Path(name).parts:
            copy(source, PACKET / "saved-review" / name)
    for name, source in tree_files(paired_dir).items():
        copy(source, PACKET / "paired-review" / name)
    prior_reference = {"scope": "Referenced reduced-run packet retained separately; no archive duplication",
                       "packet": str(PRIOR.relative_to(ROOT)),
                       "artifactIndex": record(PRIOR / "artifact-index.json", ROOT),
                       "indexedArtifactsVerified": len(prior_index["artifacts"]),
                       "archives": [r for r in prior_index["artifacts"] if r["path"].endswith(".zip")],
                       "summary": record(PRIOR / "summary.json", ROOT)}
    write_json(PACKET / "reduced-run-evidence-reference.json", prior_reference)
    write_json(PACKET / "archive-member-verification.json", {"archives": archives,
               "actualBaselineSourceFiles": len(source_members),
               "totalDecodedMembers": sum(r["decodedMembers"] for r in archives),
               "allCrcAndDecodedPayloadChecksPassed": True})
    summary = {"schema": "cl-mpm.unnotched-gravity.baseline-and-pair.evidence.v1",
               "createdUtc": datetime.now(timezone.utc).isoformat(),
               "packagingHead": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                                capture_output=True, check=True, text=True).stdout.strip(),
               "nativeSourceCommit": status["sourceCommit"], "nativeExit": status["nativeExitCode"],
               "nativeComplete": manifest["complete"], "savedFrames": manifest["savedFrames"],
               "physicalTimeS": manifest["timeS"], "particleCount": manifest["particleCount"],
               "acceptedUpdates": manifest["updates"], "actualSourceFiles": len(source_members),
               "savedIntegrity": review["integrityStatus"],
               "coherentMotionDetected": review["coherentMotionDetected"],
               "landslideDetected": review["landslideDetected"], "runoutGateDetected": review["runoutGateDetected"],
               "landslideVerified": False, "scientificallyValidated": False,
               "motionWindows": {k: v["status"] for k, v in review["motionWindows"].items()},
               "media": media, "pairedReview": pair,
               "pairedAnalysisPreExecutionRecord": pair_pre,
               "reducedRunEvidence": prior_reference,
               "baselineAnalysisPreExecutionRecord": pre_execution,
               "runtimeScope": "Original modern supervisor/detached logs and live proof retained; user-session WMI does not guarantee logoff/sleep/reboot survival",
               "operations": "Read/copy/hash/ZIP/CRC/decoded-byte verification only; no native/replay/material/test/render/review/paired-analysis repeated"}
    write_json(PACKET / "summary.json", summary)
    (PACKET / "README.md").write_text(
        "# Completed unnotched SRF1 baseline and paired review\n\n"
        "Baseline srf1-001 native source8d8b544 completes exit0 at25October04:33:41WIB:6physical seconds,61actual states,880fixed particle IDs and7740accepted updates. "
        "The original supervisor status remains NATIVE_COMPLETE_REVIEW_PENDING; subsequent independent saved review is retained separately. "
        "All282actual immutable native sources, raw CSV/VTK, loaded-byte provenance, mapped DLL and original status/modern logs/detached worker exit/start/live proofs are preserved.\n\n"
        "The one baseline saved-data audit/render completes exit0; integrity is " + str(review["integrityStatus"]) + ". "
        "Baseline coherent-motion/landslide/runout observations are " + str(review["coherentMotionDetected"]) + "/" + str(review["landslideDetected"]) + "/" + str(review["runoutGateDetected"]) + ". "
        "Complete video contains61actual states at4fps,15.25s playback, scale1, no interpolation or amplification, full decode exit0. "
        "Exact review script/imported reader/contract were copied and hashed before execution; all61frame PNGs remain in the review ZIP.\n\n"
        "The one separately executed paired review and its exact scripts/results/plots are retained without rerunning it. "
        "Its time/ID/input alignment status is " + str(pair["comparisonStatus"]) + "; physical result is " + str(pair["physicalResult"]) + ". "
        "The prior SRF1.40 completion packet remains separate and is referenced by its artifact-index/summary/archive hashes rather than duplicating its archives. "
        "Neither native completion nor a paired numerical comparison is a verified landslide, scientific validation or calibrated field runout. "
        "Predeclared detection windows, fixed-grid floor, coarse mesh and adapted geometry limits remain intact.\n\n"
        "Both new ZIPs were CRC-tested, decoded and compared byte for byte against original members. "
        "Only manifest-indexed source files are included; private FASL/Python caches are excluded. "
        "All original baseline/reduced/review/paired directories remain in output/. Packaging executes read/copy/hash/ZIP verification only, with no native or analysis repetition.\n",
        encoding="utf-8", newline="\n")
    files = [record(p, PACKET) for p in sorted(PACKET.rglob("*")) if p.is_file()]
    write_json(PACKET / "artifact-index.json", {"schema": "cl-mpm.evidence.artifact-index.v1", "artifacts": files,
               "note": "Index excludes itself. * -text preserves raw bytes. Indexed ignored PNG/MP4 need explicit staging and staged-blob verification."})
    for row in files:
        if record(PACKET / row["path"], PACKET) != row:
            raise RuntimeError("Indexed artifact changed")
    print(json.dumps({"packet": str(PACKET), "indexedArtifacts": len(files),
                      "actualBaselineSourceFiles": len(source_members),
                      "decodedZipMembers": sum(r["decodedMembers"] for r in archives),
                      "referencedReducedArtifacts": len(prior_index["artifacts"]),
                      "landslideVerified": False}, indent=2))


if __name__ == "__main__":
    main()
