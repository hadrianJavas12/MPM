"""Collect the completed repaired h0.5 attempt and existing terminal analyses.

Adapted from pack-failed-gravity-composite-h05.py; import only the guarded
copy/hash/ZIP helper definitions. Run after root closes the one variant review,
its spatial note and the full saved-CSV pair. No analysis or solver is invoked.
"""
from datetime import datetime, timezone
import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "output/mc-composite-apex-2026-10-26"
NAME = "srf1p6-composite-h05-002"
RUN = RAW / NAME
STAGE = RAW / (NAME + "-launch-preparation")
LAUNCH = ROOT / "docs/evidence/unnotched-gravity-2026-10-26" / (NAME + "-launch")
PACKET = ROOT / "docs/evidence/mc-composite-apex-2026-10-26" / (NAME + "-completed")
HELPER = ROOT / ".tmp/pack-gravity-completed-002.py"
SOURCE_COMMIT = "139005c28ff579fe7cbce410f8e07917ec6cf17c"
SOURCE_COUNT = 288  # Actual manifest/tree count for this attempt, not the old287.


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-dir", type=Path, required=True)
    parser.add_argument("--review-exit", type=Path, required=True,
                        help="Root's existing authoritative outer review exit JSON")
    parser.add_argument("--root-review", type=Path, default=RUN / "root-spatial-review.md")
    parser.add_argument("--comparison-dir", type=Path, required=True)
    args = parser.parse_args()
    require(not PACKET.exists() and PACKET.resolve().is_relative_to(ROOT.resolve()),
            "Use a fresh completion packet inside the workspace; preserve previous attempts")
    spec = importlib.util.spec_from_file_location("_copy_hash_zip_helpers", HELPER)
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)  # Definitions only; guarded historical main stays idle.
    h.PACKET = PACKET
    review_dir, outer_path = args.review_dir.resolve(), args.review_exit.resolve()
    root_review, comparison_dir = args.root_review.resolve(), args.comparison_dir.resolve()
    for path in (review_dir, outer_path, root_review):
        require(path.is_relative_to(RAW.resolve()) and path.exists(), "Missing retained run analysis: " + str(path))
    require(review_dir.is_relative_to(RUN.resolve()) and root_review.is_relative_to(RUN.resolve())
            and root_review.is_file(), "Wait for this run's saved review and root spatial note")
    require(comparison_dir.is_relative_to((ROOT / "output").resolve()) and comparison_dir.is_dir(),
            "Wait for an existing full saved-CSV comparison in workspace output")

    manifest = h.read_json(RUN / "manifest.json")
    status = h.read_json(RAW / (NAME + "-status.json"))
    worker = h.read_json(RAW / (NAME + "-detached/worker-exit.json"))
    require(status["status"] == "NATIVE_COMPLETE_REVIEW_PENDING" and status["sourceCommit"] == SOURCE_COMMIT
            and status["nativeExitCode"] == worker["exitCode"] == 0
            and status["nativeComplete"] is True and manifest["complete"] is True
            and manifest["status"] == "complete" and manifest["timeS"] == manifest["lastSavedTimeS"] == 6
            and manifest["savedFrames"] == 61 and manifest["particleCount"] == 3520
            and manifest["updates"] == 15470 and status.get("endedUtc") and worker.get("finishedUtc"),
            "Original terminal completed-native scope differs")
    review = h.read_json(review_dir / "review.json")
    child_exit, outer_exit = h.read_json(review_dir / "child-exit.json"), h.read_json(outer_path)
    require(child_exit.get("exitCode") == outer_exit.get("exitCode") == 0
            and review.get("integrityStatus") == "PASS" and review.get("nativeComplete") is True
            and review.get("boundedControlOnly") is False and review.get("analysisSourceAfterMatch") is True
            and review.get("sourceVerification", {}).get("status") == "PASS"
            and review.get("variantReview", {}).get("status") == "PASS"
            and Path(review["nativeEvidenceRoot"]).resolve() == RUN.resolve()
            and not any(key in review for key in ("error", "sourceAfterError", "mediaError")),
            "Wait for the authoritative complete unbounded variant review")
    require(review.get("landslideVerified") is False and review.get("scientificallyValidated") is False,
            "Scientific or verified-landslide claim exceeds this evidence")
    video = next((row for row in review.get("media", []) if row["path"].lower().endswith(".mp4")), None)
    require(video and video.get("fullDecodeExit") == 0 and video.get("actualSavedStates") == 61
            and video.get("playbackFramesPerSecond") == 4 and video.get("deformationMagnification") == 1
            and video.get("interpolation") is False, "Wait for existing full actual-state scale1 media")

    checked_records = []
    def match_record(row, path=None):
        actual = h.record(path or Path(row["path"]))
        require(actual["sha256"] == row["sha256"] and ("bytes" not in row or actual["bytes"] == row["bytes"]),
                "Retained recorded bytes changed: " + actual["path"])
        checked_records.append(actual)
        return actual

    rows = h.read_json(RUN / "source/source-manifest.json")["files"]
    source_index = {row["path"]: row for row in rows}
    require(len(rows) == len(source_index) == SOURCE_COUNT, "Actual native source count differs")
    for row in rows:
        path = (RUN / row["path"]).resolve()
        require(path.is_relative_to((RUN / "source").resolve()), "Source path escapes native snapshot")
        match_record(row, path)
    launch_rows = h.read_json(LAUNCH / "metadata/native-source-manifest-index.json")["files"]
    require({row["path"]: (row["bytes"], row["sha256"]) for row in launch_rows} == {
            name: (row["bytes"], row["sha256"]) for name, row in source_index.items()},
            "Original launch and terminal source manifests differ")
    provenance = h.read_json(RUN / "source-provenance.json")
    backend, dll = provenance["nativeBackend"], source_index["source/libs/kirchoff.dll"]
    require(provenance["sourceSnapshotExactLoadedBytes"] and provenance["copiedByteEqualityBeforeLoad"]
            and set(provenance["copiedFiles"]) == set(source_index)
            and backend["sha256"] == dll["sha256"] and backend["nativeMcEntryPresent"] is True
            and Path(backend["modulePath"]).resolve() == (RUN / dll["path"]).resolve()
            and backend["verifiedBy"] == "GetModuleHandleW/GetModuleFileNameW",
            "Stored original runtime DLL/source-byte proof differs")
    diagnostic_path = (RUN / "source/materials/models/plastic/mc-composite-apex/diagnostics.lisp").resolve()
    diagnostic_loads = [row for row in provenance["verifiedAsdfActions"]
        if row.get("event") == "performing" and row.get("operation") == "load-op"
        and row.get("source") and Path(row["source"]).resolve() == diagnostic_path]
    require(diagnostic_loads and all(row.get("firstParty") is True and row.get("loadInputs")
            and all(item.get("sha256") for item in row["loadInputs"]) for row in diagnostic_loads),
            "Original actual optional diagnostics load proof is absent")
    prepared = h.read_json(STAGE / "prelaunch-snapshot.json")
    require(prepared["sourceCommit"] == SOURCE_COMMIT and len(prepared["frozenFiles"]) == 25,
            "Original prelaunch preparation attribution/count differs")
    for row in prepared["frozenFiles"]:
        path = (STAGE / row["path"]).resolve()
        require(path.is_relative_to(STAGE.resolve()), "Prepared path escapes original stage")
        match_record(row, path)
    for row in h.read_json(review_dir / "analysis-source-before.json"):
        match_record(row)
    for row in review["baseReview"]["inputHashes"] + review.get("media", []):
        match_record(row)

    comparison = h.read_json(comparison_dir / "common-physical-review.json")
    comparison_exit = h.read_json(comparison_dir / "comparison-exit.json")
    support_before = h.read_json(comparison_dir / "support-pre-execution.json")
    support_after = h.read_json(comparison_dir / "support-after-execution.json")
    require(comparison.get("schema") == "cl-mpm.composite-refinement.csv-comparison.v1"
            and comparison.get("status") == "PASS_CSV_COMPARISON"
            and comparison_exit.get("exitCode") == 0 and support_after.get("unchanged") is True
            and comparison_exit.get("nativeCalls") == comparison_exit.get("vtkAudits") == comparison_exit.get("renders") == 0
            and comparison.get("landslideVerified") is False and comparison.get("scientificallyValidated") is False
            and comparison.get("interpolation") is False and not (comparison_dir / "stage-failure.json").exists(),
            "Wait for the complete successful full saved-CSV comparison; partial evidence is insufficient")
    for row in support_before["copies"] + support_after["copies"]:
        match_record(row)
    fine_prior = comparison["priorAuditBindings"]["fine_h05"]["frozenPriorReview"]
    require(match_record(fine_prior)["sha256"] == h.record(review_dir / "review.json")["sha256"],
            "Full comparison is bound to a different fine review")
    for binding in comparison["priorAuditBindings"].values():
        for row in [binding["frozenPriorReview"], binding["priorAuditContract"], binding["boundBaseReview"], *binding["inputs"]]:
            match_record(row)
    for row in [comparison["contract"], *comparison["outputs"]]:
        match_record(row)

    analysis_roots = {p.name for p in RUN.glob("variant-review-*") if p.is_dir()}
    if comparison_dir.parent == RUN.resolve():
        analysis_roots.add(comparison_dir.name)
    native_members = {name: path for name, path in h.tree_files(RUN).items()
        if ".native-cache" not in Path(name).parts and Path(name).parts[0] not in analysis_roots
        and not Path(name).parts[0].startswith("variant-review-") and path.resolve() != root_review}
    actual_sources = {name for name in native_members if name.startswith("source/") and name != "source/source-manifest.json"}
    require(actual_sources == set(source_index), "Full native ZIP source membership differs from original manifest")
    runtime, analysis_callers = {}, {}
    for path in sorted(RAW.glob(NAME + "*")):
        if path.is_file():
            target = analysis_callers if any(token in path.name for token in ("variant-review", "comparison")) else runtime
            target["adjacent/" + path.name] = path
    runtime.update({"detached/" + name: path for name, path in h.tree_files(RAW / (NAME + "-detached")).items()})
    native_members.update(runtime)
    analysis_members = {p.name + "/" + name: path for p in RUN.glob("variant-review-*") if p.is_dir()
                        for name, path in h.tree_files(p).items()}
    analysis_members.update({"caller/" + p.name: p for p in sorted(RUN.glob("variant-review-*.*")) if p.is_file()})
    analysis_members.update({"caller/" + name: path for name, path in analysis_callers.items()})
    if outer_path not in analysis_members.values():
        analysis_members["caller/" + outer_path.name] = outer_path
    analysis_members["root/" + root_review.name] = root_review
    analysis_members.update({"full-saved-csv-comparison/" + name: path for name, path in h.tree_files(comparison_dir).items()})
    analysis_members.update({"original-prelaunch/" + name: path for name, path in h.tree_files(STAGE).items()})
    require(not any(path.suffix.lower() == ".zip" or name.endswith("source/source-manifest.json")
                    for name, path in analysis_members.items()), "Analysis archive must not embed native source archives")
    launch_reference = {"originalArtifactIndex": h.record(LAUNCH / "artifact-index.json"),
        "originalLaunchSummary": h.record(LAUNCH / "summary.json"),
        "originalSourceArchive": h.record(LAUNCH / "complete-native-source-at-launch.zip"),
        "scope": "Closed launch evidence stays at its original path; references avoid duplicating its native-source ZIP"}

    PACKET.mkdir(parents=True)
    (PACKET / ".gitattributes").write_bytes(b"* -text\n*.zip binary\n")
    h.copy(Path(__file__), PACKET / "executed-pack-script.py")
    h.copy(HELPER, PACKET / "executed-copy-hash-zip-helpers.py")
    h.write_json(PACKET / "packaging-invocation.json", {"argv": sys.argv, "createdUtc": datetime.now(timezone.utc).isoformat(),
        "scope": "Read/copy/hash/ZIP/CRC/decoded-byte collection only; no native, test, replay, audit, render, decode or process query"})
    archives = [h.archive("complete-native-source-raw-and-runtime", native_members),
                h.archive("terminal-saved-analyses-and-original-prelaunch", analysis_members)]
    decoded = {row["path"]: row for row in archives[0]["members"]}
    for name, expected in source_index.items():
        require((decoded[name]["bytes"], decoded[name]["sha256"]) == (expected["bytes"], expected["sha256"]),
                "Archived native source differs from original pre-load manifest")
    for name in ("manifest.json", "source-provenance.json"):
        h.copy(RUN / name, PACKET / "native" / name)
    h.copy(RUN / "source/source-manifest.json", PACKET / "metadata/native-source-manifest-index.json")
    for name, path in runtime.items():
        h.copy(path, PACKET / "native" / name)
    for name, path in analysis_members.items():
        if "actual-frames" not in Path(name).parts and not name.startswith("original-prelaunch/"):
            h.copy(path, PACKET / "saved-analysis" / name)
    h.write_json(PACKET / "recorded-byte-bindings.json", {"records": checked_records, "allMatched": True,
        "originalRuntimeBackendAsRecorded": backend, "actualDiagnosticsLoadEventsAsRecorded": diagnostic_loads,
        "scope": "Existing source/runtime/analysis records bound to retained bytes; no after-exit mapping or saved-state calculation"})
    h.write_json(PACKET / "closed-launch-packet-reference.json", launch_reference)
    h.write_json(PACKET / "archive-member-verification.json", {"archives": archives,
        "actualNativeSourceMembers": len(rows), "totalDecodedMembers": sum(row["decodedMembers"] for row in archives),
        "allCrcAndDecodedPayloadChecksPassed": True})
    summary = {"schema": "cl-mpm.gravity-composite-apex.completed.evidence.v1",
        "createdUtc": datetime.now(timezone.utc).isoformat(), "nativeSourceCommit": SOURCE_COMMIT,
        "nativeExit": 0, "workerExit": 0, "nativeComplete": True,
        "nativeEndedUtc": status["endedUtc"], "workerFinishedUtc": worker["finishedUtc"],
        "physicalTimeS": manifest["timeS"], "savedFrames": manifest["savedFrames"],
        "particleCount": manifest["particleCount"], "acceptedUpdates": manifest["updates"], "nativeSourceFiles": len(rows),
        "savedReviewExit": outer_exit, "savedReviewIntegrityAsReceived": review["integrityStatus"],
        "savedReviewMotionWindowsAsReceived": review["baseReview"].get("motionWindows"),
        "savedReviewMediaAsReceived": review["media"], "fullCsvComparisonStatusAsReceived": comparison["status"],
        "fullCsvMotionWindowsAsReceived": {role: value["motion"]["windows"] for role, value in comparison["trials"].items()},
        "fullCsvRunoutCandidateAsReceived": {role: value["separateRunoutCandidate"] for role, value in comparison["trials"].items()},
        "rootSpatialReview": h.record(root_review), "registeredStopRuleAsReceived": comparison["stopRule"],
        "freshRepairAttemptAsRecorded": prepared["freshRepairAttempt"],
        "trajectoryLimit": "No byte/trajectory identity with failed001 is claimed; its missing failed trial remains unavailable",
        "landslideVerified": False, "scientificallyValidated": False,
        "runtimeScope": "Stored original DLL, launch/live creation-clock chain and worker exits retained; no post-exit PID query or logoff/sleep/reboot guarantee",
        "physicalResultScope": "Completed native integration plus existing saved audits/common-metre comparison and root spatial note; resolution/rounding sensitivity is not convergence or scientific validation",
        "operations": "Read/copy/hash/ZIP/CRC/decoded-byte collection only; no native/gate/launch/audit/render/replay/comparison repetition"}
    h.write_json(PACKET / "summary.json", summary)
    (PACKET / "README.md").write_text(
        "# Completed repaired h0.5 optional composite-apex SRF1.6 attempt002\n\n"
        "Native/worker exit0 on26October2026 at16:09:22WIB:6physical seconds,61saved states,3520MPs and15470accepted updates. Native source139005c28ff579fe7cbce410f8e07917ec6cf17c remains the launch attribution. The original supervisor status remains NATIVE_COMPLETE_REVIEW_PENDING; subsequent analyses are separate operations.\n\n"
        "ONE full native archive retains all288actual pre-load sources including the copied DLL, source/runtime provenance, raw VTK/CSV and modern adjacent/detached logs. Original prepared25records and the actual optional diagnostics load are byte-bound. The already-closed launch source ZIP is referenced by path/hash instead of copied.\n\n"
        "The separate analysis archive retains the existing complete variant review, all actual-frame PNGs/media, caller logs/exits, root spatial note, full saved-CSV comparison and original prelaunch bytes. This collector invokes no saved-data review, rendering, video decoding, comparison, test, replay, material call, native integration or process query. Reports are retained as received.\n\n"
        "Native completion and integrity PASS do not establish verified landslide, converged resolution behavior, calibrated runout or scientific validation. Root's spatial note and the registered common physical-metre observers determine the reported motion scope. No failed001 trajectory identity or missing actual failure cause is claimed. The finite stop rule forbids automatic SRF/grid/duration/strength/psi/tolerance escalation.\n\n"
        "Both ZIPs are CRC-tested, decoded and byte-compared against original members. Every native source binds to the original pre-load manifest and recorded mapped DLL. Private native/Python caches are excluded. Original outputs/private data remain untouched; * -text preserves evidence bytes. Independently verify staged Git blobs.\n",
        encoding="utf-8", newline="\n")
    artifacts = [h.record(path, PACKET) for path in sorted(PACKET.rglob("*")) if path.is_file()]
    h.write_json(PACKET / "artifact-index.json", {"schema": "cl-mpm.evidence.artifact-index.v1", "artifacts": artifacts,
        "note": "Index excludes itself; one full native-source ZIP, closed launch source ZIP referenced. Explicitly stage ignored indexed media."})
    for row in artifacts:
        require(h.record(PACKET / row["path"], PACKET) == row, "Indexed artifact changed")
    print(json.dumps({"packet": str(PACKET), "indexedArtifacts": len(artifacts),
        "decodedZipMembers": sum(row["decodedMembers"] for row in archives), "nativeSources": len(rows),
        "archives": [{"name": row["archive"]["path"], "members": row["decodedMembers"]} for row in archives],
        "nativeComplete": True, "landslideVerified": False, "scientificallyValidated": False}, indent=2))


if __name__ == "__main__":
    main()
