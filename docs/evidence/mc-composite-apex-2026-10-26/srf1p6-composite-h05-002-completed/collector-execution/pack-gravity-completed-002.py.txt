"""Copy/hash/ZIP terminal native outputs and existing review, without execution."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "output/unnotched-gravity-2026-10-25"
NAME = "srf1p4-002"
RUN = RAW / NAME
REVIEW = RUN / "review-001"
PREFIX = RUN / "prefix-comparison-001"
PACKET = ROOT / "docs/evidence/unnotched-gravity-2026-10-25/srf1p4-002-completed"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def record(path: Path, root: Path | None = None) -> dict:
    payload = path.read_bytes()
    return {"path": path.relative_to(root).as_posix() if root else str(path),
            "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}


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
        raise RuntimeError(f"Copy byte mismatch: {source}")


def immutable_sources() -> dict[str, Path]:
    manifest = read_json(RUN / "source/source-manifest.json")
    rows = manifest["files"]
    if len(rows) != 282 or len({r["path"] for r in rows}) != 282:
        raise RuntimeError("Expected 282 distinct actual native source members")
    sources = {}
    for row in rows:
        p = RUN / row["path"]
        if not p.resolve().is_relative_to((RUN / "source").resolve()):
            raise RuntimeError("Frozen source escaped native source directory")
        actual = record(p)
        if (actual["bytes"], actual["sha256"]) != (row["bytes"], row["sha256"]):
            raise RuntimeError(f"Frozen source hash mismatch: {p}")
        sources[row["path"]] = p
    return sources


def archive(label: str, members: dict[str, Path]) -> dict:
    destination = PACKET / f"{label}.zip"
    if any(name.startswith("/") or ".." in Path(name).parts for name in members):
        raise RuntimeError("Unsafe archive member path")
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name, source in sorted(members.items()):
            z.write(source, name)
    decoded = []
    with zipfile.ZipFile(destination) as z:
        if z.testzip() is not None or sorted(z.namelist()) != sorted(members):
            raise RuntimeError("Archive CRC/member failure")
        for name, source in sorted(members.items()):
            payload = z.read(name)
            if payload != source.read_bytes():
                raise RuntimeError(f"Decoded archive member mismatch: {name}")
            decoded.append({"path": name, "bytes": len(payload),
                            "sha256": hashlib.sha256(payload).hexdigest()})
    return {"archive": record(destination, PACKET), "decodedMembers": len(decoded),
            "crcPass": True, "allDecodedBytesMatchOriginals": True, "members": decoded}


def tree_files(directory: Path) -> dict[str, Path]:
    return {p.relative_to(directory).as_posix(): p for p in sorted(directory.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}


def main() -> None:
    if PACKET.exists() or not PACKET.resolve().is_relative_to(ROOT.resolve()):
        raise RuntimeError("Completion packet must be fresh inside workspace")
    manifest = read_json(RUN / "manifest.json")
    status = read_json(RAW / f"{NAME}-status.json")
    review = read_json(REVIEW / "review.json")
    review_exit = read_json(REVIEW / "review-exit.json")
    prefix_result_path = PREFIX / "result.json"
    if not prefix_result_path.is_file():
        raise RuntimeError("Wait for authoritative prefix comparison result before collection")
    prefix = read_json(prefix_result_path)
    if prefix["newProjectorOrSolverCalls"] != 0:
        raise RuntimeError("Prefix comparison scope unexpectedly includes numerical execution")
    prefix_script = record(PREFIX / "executed-comparison.py")
    if (prefix_script["bytes"], prefix_script["sha256"]) != (prefix["executedScript"]["bytes"], prefix["executedScript"]["sha256"]):
        raise RuntimeError("Exact prefix comparison script differs from recorded execution")
    if (not manifest["complete"] or manifest["status"] != "complete"
            or manifest["timeS"] != 6.0 or manifest["savedFrames"] != 61
            or manifest["particleCount"] != 880 or manifest["updates"] != 7740):
        raise RuntimeError("Native scope differs from expected completed attempt")
    if status["nativeExitCode"] != 0 or not status["nativeComplete"]:
        raise RuntimeError("No native success in actual supervisor status")
    if review_exit["exitCode"] != 0 or not review["nativeComplete"] or review["savedFrames"] != 61:
        raise RuntimeError("Wait for completed authoritative review")
    source_members = immutable_sources()
    provenance = read_json(RUN / "source-provenance.json")
    if not provenance["sourceSnapshotExactLoadedBytes"] or not provenance["copiedByteEqualityBeforeLoad"]:
        raise RuntimeError("Runtime provenance does not confirm actual frozen loaded bytes")
    dll = record(RUN / "source/libs/kirchoff.dll")
    if provenance["nativeBackend"]["sha256"] != dll["sha256"]:
        raise RuntimeError("Mapped DLL proof differs from frozen library")
    pre_execution = read_json(REVIEW / "analysis-pre-execution.json")
    for row in pre_execution["sourceCopies"]:
        p = REVIEW / "analysis-support" / Path(row["path"]).name
        actual = record(p)
        if (actual["bytes"], actual["sha256"]) != (row["bytes"], row["sha256"]):
            raise RuntimeError("Analysis-support bytes changed after pre-execution capture")
    native_vtk = sorted((RUN / "vtk").glob("particles_*.vtk"))
    if len(native_vtk) != 61:
        raise RuntimeError("Actual native particle VTK count differs")
    media = next((m for m in review["media"] if m["path"].endswith(".mp4")), None)
    if (not media or media["fullDecodeExit"] != 0 or media["actualSavedStates"] != 61
            or media["playbackFramesPerSecond"] != 4 or media["deformationMagnification"] != 1
            or media["interpolation"]):
        raise RuntimeError("Saved media scope differs from actual-state scale1 evidence")
    for item in review["media"]:
        actual = record(REVIEW / Path(item["path"]).name)
        if (actual["bytes"], actual["sha256"]) != (item["bytes"], item["sha256"]):
            raise RuntimeError("Actual media bytes differ from authoritative review")

    PACKET.mkdir(parents=True)
    (PACKET / ".gitattributes").write_bytes(b"* -text\n*.zip binary\n")
    copy(Path(__file__), PACKET / "executed-pack-script.py")
    members = dict(source_members)
    for name in ["source/source-manifest.json", "source-provenance.json", "manifest.json", "history.csv", "particles.csv"]:
        members[name] = RUN / name
    members.update({"vtk/" + p.name: p for p in sorted((RUN / "vtk").glob("*.vtk"))})
    runtime = {"adjacent/" + p.name: p for p in sorted(RAW.glob(f"{NAME}*")) if p.is_file()}
    runtime.update({"detached/" + name: p for name, p in tree_files(RAW / f"{NAME}-detached").items()})
    members.update(runtime)
    native_archive = archive("native-source-raw-and-runtime", members)
    review_members = {"review/" + k: v for k, v in tree_files(REVIEW).items()}
    prefix_members = {"prefix/" + k: v for k, v in tree_files(PREFIX).items()}
    verification = [native_archive, archive("saved-review-and-prefix", {**review_members, **prefix_members})]
    # Direct summaries/media/exact analysis support are indexed as ordinary
    # artifacts; all61 actual frame PNGs remain in the verified review ZIP.
    for name in ["manifest.json", "source-provenance.json", "source/source-manifest.json"]:
        copy(RUN / name, PACKET / "native" / name)
    for name, source in runtime.items():
        copy(source, PACKET / "native" / name)
    for name, source in tree_files(REVIEW).items():
        if "actual-frames" not in Path(name).parts:
            copy(source, PACKET / "saved-review" / name)
    for name, source in tree_files(PREFIX).items():
        copy(source, PACKET / "prefix-comparison" / name)
    write_json(PACKET / "archive-member-verification.json", {"archives": verification,
               "actualNativeSourceMembers": len(source_members),
               "totalDecodedMembers": sum(r["decodedMembers"] for r in verification),
               "allCrcAndDecodedPayloadChecksPassed": True})
    summary = {"schema": "cl-mpm.unnotched-gravity.completed.evidence.v1",
               "createdUtc": datetime.now(timezone.utc).isoformat(),
               "packagingHead": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                                capture_output=True, check=True, text=True).stdout.strip(),
               "nativeSourceCommit": status["sourceCommit"], "nativeExit": status["nativeExitCode"],
               "nativeComplete": manifest["complete"], "savedFrames": manifest["savedFrames"],
               "physicalTimeS": manifest["timeS"], "particleCount": manifest["particleCount"],
               "acceptedUpdates": manifest["updates"], "actualSourceFiles": len(source_members),
               "savedIntegrity": review["integrityStatus"],
               "coherentMotionDetected": review["coherentMotionDetected"],
               "landslideDetected": review["landslideDetected"],
               "runoutGateDetected": review["runoutGateDetected"],
               "landslideVerified": False, "scientificallyValidated": False,
               "motionWindows": {k: v["status"] for k, v in review["motionWindows"].items()},
               "prefixComparison": prefix,
               "media": media,
               "actualAnalysisSupportCapturedBeforeExecution": pre_execution,
               "runtimeScope": "Original modern supervisor/detached logs and existing live proof retained; WMI remains in user session, no logoff/sleep/reboot guarantee",
               "operations": "Read/copy/hash/ZIP/CRC/decoded-byte verification only; no solver/material/replay/test/render/review/comparison repeated"}
    write_json(PACKET / "summary.json", summary)
    (PACKET / "README.md").write_text(
        "# Completed6s unnotched SRF1.40 native attempt002\n\n"
        "Native source3ed36a3 completes exit0 at25October04:12:52WIB:6physical seconds,61actual saved states,880fixed particle IDs and7740accepted updates. "
        "The native status is preserved as NATIVE_COMPLETE_REVIEW_PENDING; later independent saved review is a separate operation. "
        "Actual raw outputs,282frozen sources, manifest, loaded-byte provenance, mapped DLL, modern supervisor logs and detached worker exit/start proof remain intact.\n\n"
        "The one saved-data review completes exit0. Integrity is " + str(review["integrityStatus"]) + "; coherent motion and landslide detection are "
        + str(review["coherentMotionDetected"]) + "/" + str(review["landslideDetected"]) + ". "
        "The study's predeclared0–6s and2–6s windows are retained without redefining success. Native completion is not a verified landslide, scientific validation or calibrated runout. "
        "Fixed-grid bed, coarse mesh, explicit ramp and adapted source geometry remain limitations.\n\n"
        "Media contains61actual states at4fps,15.25s playback, scale1, no interpolation/amplification; full decode exit0 is retained. "
        "The exact review script/imported reader/contract were copied and hashed before execution. Every actual-frame PNG is retained in the review ZIP. "
        "The0–0.9s prefix comparison reports " + str(prefix["status"]) + ":10VTK states and both CSV prefixes match exactly, without interpolation or tolerance adjustment. "
        "Its exact script/results are retained as received, with no rerun by this collector.\n\n"
        "Both archives are CRC-tested, decoded and checked byte for byte against original members. Source/cache separation preserves only manifest-indexed source; private FASL/Python caches are excluded. "
        "Historical unsuccessful live-proof clock checks remain alongside the later actual live verification. "
        "Original native, review and prefix directories remain in output/. Packaging executes only read/copy/hash/ZIP verification, with no native or analysis repetition.\n",
        encoding="utf-8", newline="\n")
    files = [record(p, PACKET) for p in sorted(PACKET.rglob("*")) if p.is_file()]
    write_json(PACKET / "artifact-index.json", {"schema": "cl-mpm.evidence.artifact-index.v1", "artifacts": files,
               "note": "Index excludes itself. Raw bytes preserved by * -text. Ignored indexed PNG/MP4 need explicit staging and staged-blob verification."})
    for row in files:
        if record(PACKET / row["path"], PACKET) != row:
            raise RuntimeError("Final indexed artifact changed")
    print(json.dumps({"packet": str(PACKET), "indexedArtifacts": len(files),
                      "actualNativeSourceFiles": len(source_members),
                      "decodedZipMembers": sum(r["decodedMembers"] for r in verification),
                      "nativeComplete": True, "landslideVerified": False}, indent=2))


if __name__ == "__main__":
    main()
