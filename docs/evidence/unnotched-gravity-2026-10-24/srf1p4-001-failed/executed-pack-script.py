"""Package existing first unnotched gravity failure and baseline replay evidence.

Read/copy/hash/ZIP operations only. Never execute native code or redo analysis.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "output/unnotched-gravity-2026-10-24"
PACKET = ROOT / "docs/evidence/unnotched-gravity-2026-10-24/srf1p4-001-failed"
FAILURE = "srf1p4-001"
REPLAYS = ("failure-replay-001", "failure-replay-002")
CAPSULE_SHA = "d0fa089970adf81178ca486f00423d53e0dffa98ba963823e822037e6e5f15bb"


def record(path: Path, root: Path | None = None) -> dict:
    payload = path.read_bytes()
    return {"path": path.relative_to(root).as_posix() if root else str(path),
            "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                    encoding="utf-8", newline="\n")


def copy(source: Path, destination: Path) -> None:
    if destination.exists():
        raise RuntimeError(f"Refuse overwrite: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    if destination.read_bytes() != source.read_bytes():
        raise RuntimeError(f"Copy mismatch: {source}")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def verify_frozen(attempt: Path, expected_count: int) -> dict:
    manifest = read_json(attempt / "source/source-manifest.json")
    files = {entry["path"]: entry for entry in manifest["files"]}
    if len(files) != expected_count or len(manifest["files"]) != expected_count:
        raise RuntimeError(f"Unexpected or duplicate source member count: {attempt}")
    for relative, expected in files.items():
        source = (attempt / relative).resolve()
        if not source.is_relative_to((attempt / "source").resolve()):
            raise RuntimeError(f"Source member escaped frozen source directory: {relative}")
        actual = record(source)
        if (actual["sha256"], actual["bytes"]) != (expected["sha256"], expected["bytes"]):
            raise RuntimeError(f"Frozen executed source hash/length mismatch: {source}")
    proofs = {}
    for phase in ("before", "after"):
        path = attempt / f"source-proof-{phase}.json"
        if not path.exists():
            proofs[phase] = {"status": "NOT_RETAINED", "reason": "No original proof file exists; not fabricated retrospectively"}
            continue
        proof = read_json(path)
        observed = {entry["path"]: entry["sha256"] for entry in proof["files"]}
        if observed != {relative: entry["sha256"] for relative, entry in files.items()}:
            raise RuntimeError(f"Original {phase} proof differs from frozen manifest: {attempt}")
        proofs[phase] = {"status": "PASS", "members": len(observed), "file": record(path)}
    return {"files": files, "proofs": proofs}


def archive(attempt: Path, target: Path, frozen: dict, extras: dict[str, Path]) -> dict:
    members = {relative: attempt / relative for relative in frozen["files"]}
    members["source/source-manifest.json"] = attempt / "source/source-manifest.json"
    for source in sorted(attempt.rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(attempt)
        # Only manifest-indexed source files are archived. Private native/Python
        # caches are not executed source or scientific output evidence.
        if "source" in relative.parts or "__pycache__" in relative.parts or source.suffix == ".pyc":
            continue
        members[relative.as_posix()] = source
    for relative, source in extras.items():
        if relative in members:
            raise RuntimeError(f"Duplicate archive member: {relative}")
        members[relative] = source
    if any(name.startswith("/") or ".." in Path(name).parts for name in members):
        raise RuntimeError("Unsafe archive member path")
    destination = target / "executed-source-raw-and-runtime.zip"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zipped:
        for relative, source in sorted(members.items()):
            zipped.write(source, relative)
    decoded = []
    with zipfile.ZipFile(destination) as zipped:
        if zipped.testzip() is not None or sorted(zipped.namelist()) != sorted(members):
            raise RuntimeError(f"Archive CRC/member failure: {destination}")
        for relative, source in sorted(members.items()):
            payload = zipped.read(relative)
            if payload != source.read_bytes():
                raise RuntimeError(f"Decoded member mismatch: {relative}")
            decoded.append({"path": relative, "bytes": len(payload),
                            "sha256": hashlib.sha256(payload).hexdigest()})
    return {"archive": record(destination, PACKET), "sourceFiles": len(frozen["files"]),
            "decodedMembers": len(decoded), "crcPass": True, "decodedBytesMatchOriginals": True,
            "originalSourceProofs": frozen["proofs"], "members": decoded}


def main() -> None:
    if PACKET.exists() or not PACKET.resolve().is_relative_to(ROOT.resolve()):
        raise RuntimeError("Packet must be a fresh directory inside workspace")
    failed = RAW / FAILURE
    manifest = read_json(failed / "manifest.json")
    review = read_json(failed / "review-001/review.json")
    replay = read_json(RAW / "failure-replay-002/replay-result.json")
    harness = read_json(RAW / "failure-replay-001/harness-failure.json")
    if manifest["complete"] or manifest["status"] != "failed" or manifest["savedFrames"] != 10:
        raise RuntimeError("Unexpected failed run scope")
    if record(failed / "mc-integration-failure.json")["sha256"] != CAPSULE_SHA:
        raise RuntimeError("Actual failure capsule changed")
    if (review["nativeComplete"] or review["integrityStatus"] != "PASS"
            or review["landslideDetected"] or review["savedFrames"] != 10):
        raise RuntimeError("Saved review scope is not expected retained negative evidence")
    if not replay["passed"] or replay["actualPrincipalReplayCalls"] != 1 or replay["physicalUpdates"] != 0:
        raise RuntimeError("Actual original replay count/scope changed")
    if harness["actualPrincipalReplayCalls"] != 0 or harness["physicalUpdates"] != 0:
        raise RuntimeError("Harness001 unexpectedly executed native material/MPM work")
    PACKET.mkdir(parents=True)
    (PACKET / ".gitattributes").write_bytes(b"* -text\n*.zip binary\n")
    copy(Path(__file__), PACKET / "executed-pack-script.py")
    frozen = {FAILURE: verify_frozen(failed, 282),
              **{name: verify_frozen(RAW / name, 283) for name in REPLAYS}}
    adjacent = {f"adjacent/{FAILURE}{ending}": RAW / f"{FAILURE}{ending}"
                for ending in ("-launch.json", "-status.json", ".stdout.log", ".stderr.log")}
    detached = RAW / f"{FAILURE}-detached"
    for source in sorted(detached.rglob("*")):
        if source.is_file():
            adjacent["detached/" + source.relative_to(detached).as_posix()] = source
    verification = [archive(failed, PACKET / FAILURE, frozen[FAILURE], adjacent)]
    for name in REPLAYS:
        verification.append(archive(RAW / name, PACKET / name, frozen[name],
                                    {"adjacent/native.log": RAW / f"{name}.log"}))
    # Provide directly inspectable summaries, media and exact analysis sources;
    # full native CSV/VTK plus actual-frame PNG sequence remain inside the ZIP.
    for source in sorted((failed / "review-001").rglob("*")):
        if (source.is_file() and "actual-frames" not in source.relative_to(failed / "review-001").parts
                and "__pycache__" not in source.parts and source.suffix != ".pyc"):
            copy(source, PACKET / FAILURE / "saved-review" / source.relative_to(failed / "review-001"))
    for name in ("manifest.json", "mc-integration-failure.json", "source-provenance.json", "source/source-manifest.json"):
        copy(failed / name, PACKET / FAILURE / name)
    for relative, source in adjacent.items():
        copy(source, PACKET / FAILURE / relative)
    for name in REPLAYS:
        for source in sorted((RAW / name).glob("*")):
            if source.is_file():
                copy(source, PACKET / name / source.name)
        copy(RAW / f"{name}.log", PACKET / name / "native.log")
        copy(RAW / name / "source/source-manifest.json", PACKET / name / "source/source-manifest.json")
    incomplete = ROOT / "docs/evidence/unnotched-gravity-2026-10-24/srf1p4-001-launch"
    incomplete_members = []
    for source in sorted(incomplete.rglob("*")):
        if source.is_file():
            destination = PACKET / "incomplete-launch-capture" / source.relative_to(incomplete)
            copy(source, destination)
            incomplete_members.append(record(destination, PACKET))
    copy(ROOT / "research/notes/unnotched-landslide-2026-10-24/perfect-mc-complementarity-diagnosis.md",
         PACKET / "analysis-not-native/perfect-mc-complementarity-diagnosis.md")
    module_names = ["law", "projection", "state", "material", "diagnostics", "package"]
    module_comparison = []
    for module in module_names:
        relative = f"source/materials/models/plastic/mohr-coulomb-evolution/{module}.lisp"
        hashes = {name: frozen[name]["files"][relative]["sha256"] for name in frozen}
        if len(set(hashes.values())) != 1:
            raise RuntimeError(f"Baseline replay MC module differs from actual failed source: {module}")
        module_comparison.append({"path": relative, "sha256ByExecutedAttempt": hashes, "allIdentical": True})
    write_json(PACKET / "archive-member-verification.json", {"archives": verification,
               "totalExecutedSourceEntriesAcrossThreeArchives": sum(row["sourceFiles"] for row in verification),
               "totalDecodedMembers": sum(row["decodedMembers"] for row in verification),
               "allCrcAndDecodedPayloadChecksPassed": True})
    write_json(PACKET / "provenance-and-source-scope.json", {
        "executedBaselineMcModules": module_comparison,
        "currentWorkingTreeCompared": False,
        "reason": "Current projection is being repaired independently after baseline replay. Archives use immutable executed snapshots only; no current-source equality is claimed.",
        "analysisSupport": review["analysisScript"], "importedReader": review["vtkReaderSource"],
        "fullFailedRunReviewExecutedExactlyOnce": True,
        "incompleteLaunchCapture": {"status": "INCOMPLETE_CAPTURE", "files": incomplete_members,
             "missingLiveProof": "Capture started after native exit1 and correctly rejected missing live PID. Original partial status/launch copies and README are retained; not fabricated as live verification."},
        "replay001AfterProof": "NOT_RETAINED: top-level package-lock failure occurred before actual replay; only original before proofs exist.",
        "runtimeScope": "Native source-provenance records actual loaded frozen bytes and mapped DLL. WMI worker remains in user session; sleep/logoff/reboot immunity is not proved.",
        "wholeMpmRollbackFromCapsule": "NOT_EXECUTED: pure capsule lacks full particle/simulation checkpoint"})
    summary = {
        "schema": "cl-mpm.unnotched-gravity.first-failure.evidence.v1", "createdUtc": datetime.now(timezone.utc).isoformat(),
        "packagingHead": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, check=True, text=True).stdout.strip(),
        "status": "FAILED_NATIVE_WITH_SAVED_INTEGRITY_PASS_AND_EXPECTED_REPLAY_REJECTION",
        "nativeExit": 1, "savedStates": 10, "particleCount": manifest["particleCount"], "savedParticleRows": 8800,
        "lastSavedTimeS": manifest["lastSavedTimeS"], "attemptedFailureTimeS": manifest["attemptTimeS"],
        "acceptedOrAttemptedUpdateCounterAtFailure": manifest["updates"],
        "savedIntegrity": review["integrityStatus"], "coherentMotionDetected": review["coherentMotionDetected"],
        "landslideVerified": False, "scientificallyValidated": False,
        "motionWindowScope": {key: value["status"] for key, value in review["motionWindows"].items()},
        "media": review["media"],
        "replay001": harness, "replay002": {"expectedRejection": replay["expectedRejection"],
            "actualPrincipalReplayCalls": replay["actualPrincipalReplayCalls"], "physicalUpdates": replay["physicalUpdates"],
            "productionFunctionsRestored": replay["productionFunctionsRestored"]},
        "capsuleSha256": CAPSULE_SHA,
        "interpretation": "Native ambiguity arises from accepted face and near-edge candidate; negative edge multiplier has stress effect above unchanged stress tolerance. Pure diagnostic/closed-form analysis is separate from pending repair, not evidence of successful full run.",
        "packagingOperations": "Copy/hash/ZIP/CRC/read verification only; no solver/replay/material/render/saved-data review repetitions"}
    write_json(PACKET / "summary.json", summary)
    (PACKET / "README.md").write_text(
        "# First unnotched gravity/SSR failure and original replay\n\n"
        "The SRF1.40 trial failed native exit1 during the gravity ramp. Ten actual saved states cover0–0.9s, "
        "880 captured particle IDs and8800 CSV rows. The failed attempted time is approximately0.980934788s; "
        "the1265 update counter includes later unsaved work. Saved0.9s must not be called the exact failure time. "
        "No full-duration slope, gravity hold, coherent landslide or scientific validation was achieved.\n\n"
        "The saved-data review ran once and passed finite/mass/ID/F/J/MC-law/yield/CSV–VTK checks. "
        "Displacements remain millimetric; no toe-crossing mass appears. Its1s persistence and post2s windows "
        "are NOT_EVALUATED, rather than failed physics tests. Scale1 PNG and INCOMPLETE video contain actual states; "
        "the video has10 frames at4fps, full decode exit0, without interpolation or amplified motion. "
        "Executed analysis script/imported reader bytes are retained under saved-review/analysis-support.\n\n"
        "Each ZIP retains its own immutable executed source set:282 failed-run sources,283 replay001 sources, "
        "and283 replay002 sources, with manifests, available runtime proofs, raw outputs, logs and diagnostics. "
        "All ZIP members are CRC-tested, decoded and compared byte for byte against originals. Six MC modules "
        "match across the executed attempts. Current working projection is under separate repair and is not "
        "claimed identical. Original raw outputs and frozen directories remain in output/.\n\n"
        "Replay001 is a retained package-lock harness failure with zero actual calls. Replay002 performs exactly "
        "one original production principal return, zero MPM updates, reproduces the expected ambiguity rejection, "
        "and restores observation wrappers. Full-MPM rollback is NOT_EXECUTED from this capsule. Original before/after "
        "source and mapped DLL proof are preserved where they exist.\n\n"
        "The historical launch capture is INCOMPLETE_CAPTURE: it began after native exit, correctly rejected the "
        "missing live PID, and retained only two status/launch JSONs. Its original README and files remain unchanged "
        "both here and in their original packet. No missing live-process proof is reconstructed.\n\n"
        "The analytical active-set note is read-only algebra, distinct from native replay. No numerical fix or "
        "successful continuation is included in this negative-evidence packet. Packaging itself executes no solver, "
        "replay, material calls, rendering or saved-data review.\n",
        encoding="utf-8", newline="\n")
    files = [record(path, PACKET) for path in sorted(PACKET.rglob("*")) if path.is_file()]
    write_json(PACKET / "artifact-index.json", {"schema": "cl-mpm.evidence.artifact-index.v1", "artifacts": files,
               "note": "Index excludes itself; * -text preserves indexed raw bytes. Intended ignored media must be force-added and staged Git blobs hash-verified before commit."})
    for row in files:
        actual = record(PACKET / row["path"], PACKET)
        if actual != row:
            raise RuntimeError(f"Final artifact changed: {row['path']}")
    print(json.dumps({"packet": str(PACKET), "indexedArtifacts": len(files),
                      "executedSourceEntries": sum(row["sourceFiles"] for row in verification),
                      "decodedZipMembers": sum(row["decodedMembers"] for row in verification),
                      "status": summary["status"]}, indent=2))


if __name__ == "__main__":
    main()
