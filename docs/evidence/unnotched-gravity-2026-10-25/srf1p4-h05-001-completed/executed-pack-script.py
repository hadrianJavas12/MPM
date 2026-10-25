"""Archive an already terminal h0.5 attempt and saved analysis; execute neither.

Run only after the supervisor/worker and saved-data analysis have terminated.
Default mode is deliberately strict. Failed/incomplete records use distinct
packet names and never receive a completed label. Originals are never modified.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "output/unnotched-gravity-2026-10-25"
NAME = "srf1p4-h05-001"
RUN = RAW / NAME
LAUNCH = ROOT / f"docs/evidence/unnotched-gravity-2026-10-25/{NAME}-launch"
HELPER = ROOT / ".tmp/pack-gravity-completed-002.py"


def load_helpers():
    # Import definitions only: the existing helper's guarded main is not run.
    spec = importlib.util.spec_from_file_location("_copy_hash_zip_helpers", HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.RUN = RUN
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("completed", "failed", "incomplete"), default="completed")
    parser.add_argument("--review-dir", type=Path, default=RUN / "refinement-review-001")
    parser.add_argument("--observer-controls-dir", type=Path,
                        help="Optional existing pure-synthetic proof, not a test invocation")
    parser.add_argument("--terminal-reconciliation", type=Path,
                        help="Explicit retained terminal evidence if a non-success worker exit is unavailable")
    args = parser.parse_args()
    h = load_helpers()
    packet = ROOT / f"docs/evidence/unnotched-gravity-2026-10-25/{NAME}-{args.mode}"
    h.PACKET = packet
    if packet.exists() or not packet.resolve().is_relative_to(ROOT.resolve()):
        raise RuntimeError("Use a fresh packet inside the workspace")
    review_dir = args.review_dir.resolve()
    if not review_dir.is_relative_to(RUN.resolve()):
        raise RuntimeError("Saved review must belong to this native attempt")
    manifest = h.read_json(RUN / "manifest.json")
    status = h.read_json(RAW / f"{NAME}-status.json")
    if status["status"] in ("STARTING", "NATIVE_RUNNING", "POSTPROCESSING"):
        raise RuntimeError("Wait for terminal supervisor state; no active packaging")
    worker_path = RAW / f"{NAME}-detached/worker-exit.json"
    worker = h.read_json(worker_path) if worker_path.is_file() else None
    if worker is None and (args.mode == "completed" or not args.terminal_reconciliation):
        raise RuntimeError("Require existing worker exit or explicit non-success reconciliation")
    if args.terminal_reconciliation and not args.terminal_reconciliation.is_file():
        raise RuntimeError("Terminal reconciliation file is missing")
    exit_path = review_dir / "refinement-review-exit.json"
    review_exit = h.read_json(exit_path) if exit_path.is_file() else None
    fine_path = review_dir / "fine-native-review.json"
    common_path = review_dir / "common-physical-review.json"
    fine = h.read_json(fine_path) if fine_path.is_file() else None
    common = h.read_json(common_path) if common_path.is_file() else None
    media_path = review_dir / "fine-media.json"
    media = h.read_json(media_path) if media_path.is_file() else None
    native_complete = (status.get("nativeExitCode") == 0 and status.get("nativeComplete") is True
                       and manifest.get("complete") is True and manifest.get("status") == "complete")

    sources = h.immutable_sources()  # All282 original manifest members, including DLL.
    provenance = h.read_json(RUN / "source-provenance.json")
    backend = provenance["nativeBackend"]
    if not (provenance["sourceSnapshotExactLoadedBytes"] and provenance["copiedByteEqualityBeforeLoad"]
            and backend["verifiedBy"] == "GetModuleHandleW/GetModuleFileNameW"
            and backend["sha256"] == h.record(RUN / "source/libs/kirchoff.dll")["sha256"]):
        raise RuntimeError("Frozen sources and existing actual mapped-DLL proof disagree")

    # Check existing saved proofs; this collector performs no result calculation.
    recorded_proof_checks = []
    def check_record(row, path=None):
        source = path or Path(row["path"])
        actual = h.record(source)
        matched = all(actual[key] == row[key] for key in ("bytes", "sha256"))
        recorded_proof_checks.append({"path": str(source), "matchesRecordedBytes": matched})
        if not matched:
            raise RuntimeError(f"Recorded analysis/protocol bytes changed: {source}")

    review_dirs = sorted(path for path in RUN.glob("refinement-review-*") if path.is_dir())
    if review_dir.is_dir() and review_dir not in review_dirs:
        review_dirs.append(review_dir)
    for directory in review_dirs:
        pre = directory / "support-pre-execution.json"
        if pre.is_file():
            for row in h.read_json(pre)["copies"]:
                frozen = directory / "analysis-support" / Path(row["path"]).name
                check_record(row, frozen)
        if not (directory / "refinement-review-exit.json").is_file() and not args.terminal_reconciliation:
            raise RuntimeError(f"Saved-analysis attempt lacks terminal exit: {directory}")

    video = None
    if media:
        for row in media["files"]:
            check_record(row, review_dir / Path(row["path"]).name)
            if row["path"].lower().endswith(".mp4"):
                video = row
    if common:
        for row in common["comparisonSources"] + common["outputs"]:
            check_record(row)
        check_record(common["coarsePriorAudit"])
        check_record(common["analysisScript"])
        for row in common["contracts"].values():
            check_record(row)
    if fine:
        for row in fine["inputHashes"]:
            check_record(row)
    if args.mode == "completed":
        if not (native_complete and worker and worker["exitCode"] == 0
                and manifest["timeS"] == 6.0 and manifest["savedFrames"] == 61
                and manifest["particleCount"] == 3520 and manifest["updates"] > 0
                and len(list((RUN / "vtk").glob("particles_*.vtk"))) == 61):
            raise RuntimeError("Completed label requires actual native0/complete6s/61states/3520MPs")
        if not (review_exit and review_exit["exitCode"] == 0 and fine and common
                and fine["integrityStatus"] == "PASS" and fine["nativeComplete"]
                and fine["savedFrames"] == 61 and fine["lastSavedTimeS"] == 6.0
                and fine["auditRole"] == "FINE_NATIVE_INTEGRITY_AND_SEPARATE_H_SCALED_DIAGNOSTICS"
                and fine["crossMeshComparisonIsSeparate"] is True
                and common["nativeFineIntegrity"] == "PASS" and common["nativeFineComplete"]
                and common["interpolation"] is False and common["particleIdsTransferableAcrossMeshes"] is False
                and common["inputChanges"] == [{"key": "meshSize", "coarse": 1.0, "fine": 0.5}]
                and common["landslideVerified"] is False and common["scientificallyValidated"] is False):
            raise RuntimeError("Completed label requires separate terminal fine integrity and common-metre review")
        pre = h.read_json(review_dir / "support-pre-execution.json")
        expected_support = {"review-gravity-refinement.py", "review-gravity-slope.py",
                            "plot_m5_cliff_comparison.py", "fine-audit-contract.json",
                            "refinement-contract.json", "original-study-contract.json"}
        if {Path(row["path"]).name for row in pre["copies"]} != expected_support or len(pre["copies"]) != 6:
            raise RuntimeError("Require all six exact pre-execution analysis sources/contracts")
        source_proof = h.read_json(review_dir / "fine-terminal-source-verification.json")
        if not source_proof["allManifestHashesAndLengthsMatched"] or len(source_proof["files"]) != 282:
            raise RuntimeError("Saved terminal source verification is missing or incomplete")
        for row in source_proof["files"]:
            check_record(row, RUN / row["path"])
        if not (media and "error" not in media and video and video["fullDecodeExit"] == 0
                and video["actualSavedStates"] == 61 and video["playbackFramesPerSecond"] == 4
                and video["deformationMagnification"] == 1 and video["interpolation"] is False):
            raise RuntimeError("Completed packet requires recorded actual-state scale1 decoded video proof")
    elif args.mode == "failed":
        if not ((status.get("nativeExitCode") not in (None, 0))
                or (review_exit and review_exit["exitCode"] != 0)
                or (worker and worker["exitCode"] != 0)):
            raise RuntimeError("Failed label requires an actual recorded nonzero exit")

    packet.mkdir(parents=True)
    (packet / ".gitattributes").write_bytes(b"* -text\n*.zip binary\n")
    h.copy(Path(__file__), packet / "executed-pack-script.py")
    h.copy(HELPER, packet / "executed-copy-hash-zip-helpers.py")
    # Source cache is deliberately excluded; every other original source file
    # (including ASDF action/load-event proof) is retained, even if not indexed.
    source_extras = {"source/" + name: path for name, path in h.tree_files(RUN / "source").items()
                     if ".native-cache" not in Path(name).parts}
    native_members = {**sources, **source_extras}
    analysis_roots = {directory.name for directory in review_dirs}
    native_members.update({name: path for name, path in h.tree_files(RUN).items()
                           if Path(name).parts[0] != "source" and Path(name).parts[0] not in analysis_roots})
    runtime = {"adjacent/" + p.name: p for p in sorted(RAW.glob(f"{NAME}*")) if p.is_file()}
    runtime.update({"detached/" + key: path for key, path in h.tree_files(RAW / f"{NAME}-detached").items()})
    if args.terminal_reconciliation:
        runtime["terminal-reconciliation/" + args.terminal_reconciliation.name] = args.terminal_reconciliation
    native_members.update(runtime)
    archives = [h.archive("native-source-raw-and-runtime", native_members)]
    analysis_members = {directory.name + "/" + name: path for directory in review_dirs
                        for name, path in h.tree_files(directory).items()}
    if analysis_members:
        archives.append(h.archive("saved-analysis-all-attempts-and-media", analysis_members))
    if not LAUNCH.is_dir():
        raise RuntimeError("Original launch evidence packet is required, including initial helper failure")
    launch_members = h.tree_files(LAUNCH)
    launch_source_manifest = h.read_json(LAUNCH / "source/source-manifest.json")
    launch_sources = {row["path"]: row for row in launch_source_manifest["files"]}
    if set(launch_sources) != set(sources):
        raise RuntimeError("Launch and original native snapshot source member sets differ")
    augmentation = []
    for name, path in sources.items():
        expected = launch_sources[name]
        actual = h.record(path)
        if (actual["bytes"], actual["sha256"]) != (expected["bytes"], expected["sha256"]):
            raise RuntimeError("Original native source differs from launch manifest")
        if name in launch_members and launch_members[name].read_bytes() != path.read_bytes():
            raise RuntimeError("Original launch member conflicts with original native snapshot")
        augmentation.append({"archiveMember": name, "originalNativePath": str(path),
                             "alreadyInOriginalLaunchPacket": name in launch_members,
                             "bytes": actual["bytes"], "sha256": actual["sha256"]})
        launch_members.setdefault(name, path)
    archives.append(h.archive("original-launch-evidence-plus-original-native-source", launch_members))
    h.write_json(packet / "launch-archive-source-augmentation.json", {
        "scope": "Original launch packet unchanged; archive additionally includes every original frozen native source indexed by its launch manifest. These are original executed bytes, not reconstructed/current production sources.",
        "originalLaunchPacket": str(LAUNCH), "manifestSourceMembers": len(sources),
        "members": augmentation, "allAddedSourceHashesAndLengthsMatchLaunchManifest": True})
    if args.observer_controls_dir:
        if not args.observer_controls_dir.is_dir():
            raise RuntimeError("Explicit synthetic observer-proof directory is missing")
        archives.append(h.archive("existing-observer-controls", h.tree_files(args.observer_controls_dir)))
    for name in ("manifest.json", "source-provenance.json", "source/source-manifest.json"):
        h.copy(RUN / name, packet / "native" / name)
    for name, path in runtime.items():
        h.copy(path, packet / "native" / name)
    for name, path in analysis_members.items():
        if "actual-frames" not in Path(name).parts:
            h.copy(path, packet / "saved-analysis" / name)
    prior_attempt = RAW / "archive-pack-attempt-001"
    if prior_attempt.is_dir():
        prior_files = {"packaging-failure.json": prior_attempt / "packaging-failure.json"}
        for name in ("executed-pack-script.py", "executed-copy-hash-zip-helpers.py",
                     "summary.json", "archive-member-verification.json"):
            prior_files[name] = prior_attempt / "packet" / name
        prior_files["original-artifact-index.json"] = prior_attempt / "packet/artifact-index.json"
        for name, path in prior_files.items():
            h.copy(path, packet / "prior-packaging-attempt-001" / name)
        h.write_json(packet / "prior-packaging-attempt-001/preserved-archives.json", {
            "scope": "First packet remains unchanged under output; invalid metadata-only launch ZIP is NOT embedded in the corrected packet. Parent-reported verifier failure and original packer are retained separately.",
            "archives": [h.record(path) for path in sorted((prior_attempt / "packet").glob("*.zip"))]})
    h.write_json(packet / "recorded-proof-byte-checks.json", {"checks": recorded_proof_checks,
                 "allMatched": True, "scope": "Retained record hash comparison only; no saved-data audit repeated"})
    h.write_json(packet / "archive-member-verification.json", {"archives": archives,
                 "actualNativeSourceMembers": len(sources),
                 "totalDecodedMembers": sum(row["decodedMembers"] for row in archives),
                 "allCrcAndDecodedPayloadChecksPassed": True})
    h.write_json(packet / "summary.json", {"schema": "cl-mpm.unnotched-gravity.refinement-terminal-evidence.v1",
        "createdUtc": datetime.now(timezone.utc).isoformat(), "packetMode": args.mode,
        "packagingHead": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                         capture_output=True, check=True, text=True).stdout.strip(),
        "nativeSourceCommit": status["sourceCommit"], "nativeExit": status.get("nativeExitCode"),
        "nativeComplete": native_complete, "nativeManifestComplete": manifest.get("complete"),
        "physicalTimeS": manifest.get("timeS"), "lastSavedTimeS": manifest.get("lastSavedTimeS"),
        "savedFrames": manifest.get("savedFrames"), "particleCount": manifest.get("particleCount"),
        "acceptedUpdates": manifest.get("updates"), "actualNativeSourceFiles": len(sources),
        "savedReviewExit": review_exit, "fineNativeIntegrity": fine and fine.get("integrityStatus"),
        "nativeHScaledDiagnostics": fine and fine.get("motionWindows"),
        "commonPhysicalTrials": common and common.get("trials"),
        "commonPhysicalObserver": common and common.get("observer"),
        "media": media, "landslideVerified": False, "scientificallyValidated": False,
        "observerControls": "Existing explicit proof archived" if args.observer_controls_dir else "NOT_INCLUDED; no synthetic test claim",
        "scope": "Native fine h-scaled diagnostics and common fixed-metre cross-mesh observer are separate. Coupled space/time refinement, no certified convergence or automatic physical-mechanism validation.",
        "runtimeScope": "Original worker/supervisor exits, modern logs, stored live proof and initial helper failure retained. No new process query; user-session restart/logoff/sleep immunity unproved.",
        "operations": "Read/copy/hash/ZIP/CRC/all-member decoded-byte verification only; no solver/material/replay/test/render/review/comparison invoked"})
    (packet / "README.md").write_text(
        "# h0.5 unnotched SRF1.40 terminal evidence\n\n"
        f"Packet classification: **{args.mode}**. Native completion and saved-analysis integrity are recorded separately in summary.json; neither establishes a verified landslide or scientific validation. "
        "The original282 manifest-indexed source/input/DLL members and extra ASDF load/action proof, original raw CSV/VTK/manifest, adjacent modern logs/status/exits, detached worker records and original launch packet are retained. "
        "The launch ZIP is explicitly augmented with all282 original frozen sources, each verified against the original launch manifest, so its metadata manifest is accompanied by the complete indexed snapshot. The original launch directory remains unchanged; the separate augmentation record maps every archived source to its original path and bytes. "
        "The launch packet preserves the initial premature proof-helper failure and timestamped successful live chain. Packaging makes no process query.\n\n"
        "All saved-analysis attempts, exact pre-execution support/contracts, stage failures, exits, media and actual frame PNGs are retained in the analysis ZIP. "
        "Fine native h-scaled diagnostics remain distinct from the common fixed-metre observer. Cross-mesh IDs are not interchangeable; coarse data is compared against its prior audit without rerunning it. "
        "Mesh refinement also changes stable timestep; results do not certify isolated mesh or timestep convergence, calibrated runout or a physical mechanism.\n\n"
        "Every ZIP is CRC-tested and every decoded member is byte-compared to its original. Private native/Python caches are excluded. Originals remain untouched. "
        "Collection runs only read/copy/hash/archive verification, with no native, test, replay, review, comparison, render or decode invocation. "
        "The artifact index excludes itself; * -text preserves bytes. Explicitly stage ignored indexed PNG/MP4/VTK and verify staged blobs before commit.\n",
        encoding="utf-8", newline="\n")
    artifacts = [h.record(path, packet) for path in sorted(packet.rglob("*")) if path.is_file()]
    h.write_json(packet / "artifact-index.json", {"schema": "cl-mpm.evidence.artifact-index.v1", "artifacts": artifacts,
                 "note": "Index excludes itself; raw bytes protected by * -text; root must verify staged blobs"})
    for row in artifacts:
        if h.record(packet / row["path"], packet) != row:
            raise RuntimeError("Final indexed bytes changed")
    print(json.dumps({"packet": str(packet), "mode": args.mode, "indexedArtifacts": len(artifacts),
                      "actualNativeSourceFiles": len(sources),
                      "decodedZipMembers": sum(row["decodedMembers"] for row in archives),
                      "nativeComplete": native_complete, "landslideVerified": False}, indent=2))


if __name__ == "__main__":
    main()
