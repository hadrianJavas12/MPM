"""Archive existing gravity-slope gate evidence. Never execute a solver or review."""
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
PACKET = ROOT / "docs/evidence/unnotched-gravity-2026-10-24/native-controls"
BASELINE = "2308a1eee996e2e0e9c4730b2591b54b0860ddac"


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def record(path: Path, relative_to: Path | None = None) -> dict:
    payload = path.read_bytes()
    return {"path": path.relative_to(relative_to).as_posix() if relative_to else str(path),
            "bytes": len(payload), "sha256": digest(payload)}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise RuntimeError(f"Refusing overwrite: {destination}")
    shutil.copyfile(source, destination)
    if source.read_bytes() != destination.read_bytes():
        raise RuntimeError(f"Copy mismatch: {source}")


def git(*arguments: str) -> bytes:
    return subprocess.run(["git", *arguments], cwd=ROOT, check=True, capture_output=True).stdout


def archive_attempt(name: str) -> tuple[dict, dict]:
    attempt = RAW / name
    target = PACKET / name
    manifest = json.loads((attempt / "source/source-manifest.json").read_text(encoding="utf-8-sig"))
    rows = manifest["files"]
    if len(rows) != 285 or len({row["path"] for row in rows}) != 285:
        raise RuntimeError("Unexpected frozen source member set")
    expected = {row["path"]: row for row in rows}
    for label in ("before", "after"):
        proof = json.loads((attempt / f"source-proof-{label}.json").read_text(encoding="utf-8-sig"))
        if {row["path"]: row["sha256"] for row in proof["files"]} != {
                key: row["sha256"] for key, row in expected.items()}:
            raise RuntimeError(f"{name} {label} source proof mismatch")
    for key, row in expected.items():
        actual = record(attempt / key)
        if (actual["sha256"], actual["bytes"]) != (row["sha256"], row["bytes"]):
            raise RuntimeError(f"Frozen source mismatch: {name}/{key}")

    for source in attempt.rglob("*"):
        if source.is_file() and "source" not in source.relative_to(attempt).parts:
            copy_file(source, target / source.relative_to(attempt))
    for ending in (".log", "-exit.json"):
        copy_file(RAW / f"{name}{ending}", target / f"native{ending}")
    members = [*sorted(expected), "source/source-manifest.json",
               "source-proof-before.json", "source-proof-after.json",
               "source-provenance-before.json", "source-provenance.json"]
    archive = target / "native-source-and-runtime.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zipped:
        for member in members:
            zipped.write(attempt / member, member)
    decoded = []
    with zipfile.ZipFile(archive) as zipped:
        if zipped.testzip() is not None or len(zipped.namelist()) != len(set(members)):
            raise RuntimeError("Archive CRC/member count mismatch")
        for member in members:
            payload = zipped.read(member)
            if payload != (attempt / member).read_bytes():
                raise RuntimeError(f"Decoded ZIP member changed: {member}")
            decoded.append({"path": member, "bytes": len(payload), "sha256": digest(payload)})
    return ({"attempt": name, "sourceCount": len(expected), "zipMemberCount": len(members),
             "allDecodedPayloadsByteIdentical": True, "crcTestPassed": True,
             "members": decoded}, expected)


def main() -> None:
    if PACKET.exists():
        raise RuntimeError(f"Evidence output must be fresh: {PACKET}")
    if not PACKET.resolve().is_relative_to(ROOT.resolve()):
        raise RuntimeError("Packet path escapes workspace")
    PACKET.mkdir(parents=True)
    (PACKET / ".gitattributes").write_bytes(b"* -text\n*.zip binary\n")
    copy_file(Path(__file__), PACKET / "executed-pack-script.py")
    verification, manifests = [], {}
    for name in ("native-controls-001", "native-controls-002"):
        verified, manifest = archive_attempt(name)
        verification.append(verified)
        manifests[name] = manifest
    write_json(PACKET / "archive-member-verification.json", {"archives": verification,
               "totalSourceFilesAcrossArchives": sum(v["sourceCount"] for v in verification),
               "totalDecodedMembers": sum(v["zipMemberCount"] for v in verification)})

    for name in ("native-controls-001-independent-review", "native-controls-002-independent-review",
                 "detached-controls-001", "detached-controls-002", "monitor-controls-001"):
        for source in sorted((RAW / name).rglob("*")):
            if source.is_file():
                copy_file(source, PACKET / name / source.relative_to(RAW / name))
        log = RAW / f"{name}.log"
        if log.exists():
            copy_file(log, PACKET / name / "review.log")

    support_paths = ["scripts/review-gravity-slope.py", "scripts/plot_m5_cliff_comparison.py",
                     "scripts/run-gravity-slope-trial.ps1", "scripts/start-gravity-slope.ps1",
                     "scripts/start-wang2017-detached.ps1", "tests/windows/gravity-slope-monitor.ps1",
                     "tests/windows/detached-launch-controls.ps1",
                     "tests/windows/fixtures/detached-exit-fixture.ps1"]
    support = []
    for relative in support_paths:
        source = ROOT / relative
        copy_file(source, PACKET / "analysis-and-process-support" / relative)
        row = record(source, ROOT)
        if relative != "scripts/review-gravity-slope.py":
            baseline = git("show", f"{BASELINE}:{relative}")
            row["matchesBaselineGitBlobExactly"] = baseline == source.read_bytes()
            row["matchesBaselineIgnoringCRLFOnly"] = baseline.replace(b"\r\n", b"\n") == source.read_bytes().replace(b"\r\n", b"\n")
            if not row["matchesBaselineIgnoringCRLFOnly"]:
                raise RuntimeError(f"Support source changed since baseline: {relative}")
        support.append(row)

    first_review = json.loads((RAW / "native-controls-001-independent-review/review.json").read_text())
    second_review = json.loads((RAW / "native-controls-002-independent-review/review.json").read_text())
    analysis = (ROOT / "scripts/review-gravity-slope.py").read_bytes()
    if digest(analysis) != second_review["analysisScript"]["sha256"]:
        raise RuntimeError("Current analysis does not match executed second review")
    if digest(analysis) == first_review["analysisScript"]["sha256"]:
        raise RuntimeError("Expected honest historical analysis provenance difference is absent")

    baseline_numerical_changes = git("diff", "--name-only", BASELINE, "--", "src", "materials",
                                     "scenarios", "cl-mpm.asd", "cl-mpm-framework.asd").decode().splitlines()
    if baseline_numerical_changes:
        raise RuntimeError("Numerical/production sources changed from baseline")
    left, right = manifests["native-controls-001"], manifests["native-controls-002"]
    if set(left) != set(right):
        raise RuntimeError("Frozen source sets differ")
    changed = [{"path": key, "attempt001": left[key]["sha256"], "attempt002": right[key]["sha256"]}
               for key in sorted(left) if left[key]["sha256"] != right[key]["sha256"]]
    if [row["path"] for row in changed] != ["source/case.lisp"]:
        raise RuntimeError(f"Unexpected source changes between attempts: {changed}")
    numerical = [key for key in right if key.startswith(("source/src/", "source/materials/", "source/scenarios/"))]
    working_mismatches = [key for key in numerical
                          if digest(Path(right[key]["originalPath"]).read_bytes()) != right[key]["sha256"]]
    if working_mismatches:
        raise RuntimeError(f"Current production differs from executed snapshot: {working_mismatches}")

    identical = []
    for relative in ["history.csv", "particles.csv", *[f"vtk/particles_{i:04d}.vtk" for i in range(3)]]:
        left_file = RAW / "native-controls-001/observations" / relative
        right_file = RAW / "native-controls-002/observations" / relative
        if left_file.read_bytes() != right_file.read_bytes():
            raise RuntimeError(f"Numerical output changed between attempts: {relative}")
        identical.append({"path": relative, "sha256": digest(left_file.read_bytes()),
                          "bytes": left_file.stat().st_size, "byteIdentical": True})
    native001 = json.loads((RAW / "native-controls-001/result.json").read_text())
    native002 = json.loads((RAW / "native-controls-002/result.json").read_text())
    if native001["passedCount"] != 5 or native001["passed"] or native002["passedCount"] != 4 or not native002["passed"]:
        raise RuntimeError("Actual gate results do not match requested retained summary")
    if native002["physicalUpdatesExecuted"] != 2 or native002["materialCallsAccepted"] != 1760:
        raise RuntimeError("Actual call counts do not match bounded scope")
    provenance_gap = {
        "firstReview": {"status": "HISTORICAL_SCRIPT_BYTES_NOT_RETAINED",
                        "recordedAnalysisScript": first_review["analysisScript"],
                        "currentAnalysisIsNotThoseExecutedBytes": True,
                        "limitations": "Original first review JSON/PNG/log are retained; historical analysis script cannot be reconstructed from untracked pre-support version. No exact-first-script claim is made."},
        "secondReview": {"status": "EXACT_SCRIPT_BYTES_RETAINED",
                         "recordedAnalysisScript": second_review["analysisScript"],
                         "savedPath": "analysis-and-process-support/scripts/review-gravity-slope.py"},
        "importedVtkReader": {"path": "analysis-and-process-support/scripts/plot_m5_cliff_comparison.py",
                              "status": "CURRENT_BYTES_MATCH_BASELINE; no separate at-review support hash was recorded"},
        "detached001VerifyConsole": "NOT_RETAINED; worker-exit8 and deadline fixture/request/start/log proof are retained, not retrospectively invented console output"}
    write_json(PACKET / "analysis-provenance-limits.json", provenance_gap)
    write_json(PACKET / "source-and-output-comparison.json", {
        "baselineCommit": BASELINE, "packagingHead": git("rev-parse", "HEAD").decode().strip(),
        "productionGitDiffPathsFromBaseline": baseline_numerical_changes,
        "numericalSourceEntriesChecked": len(numerical), "executedSourcesMatchWorkingTree": not working_mismatches,
        "snapshotFileSetCount": len(right), "identicalSourceEntriesBetweenAttempts": len(right)-len(changed),
        "changedSourceEntriesBetweenAttempts": changed, "onlyTestHarnessChanged": True,
        "outputs": identical, "supportSources": support})
    detached = json.loads((RAW / "detached-controls-002/result.json").read_text(encoding="utf-8-sig"))
    monitor = json.loads((RAW / "monitor-controls-001/result.json").read_text(encoding="utf-8-sig"))
    summary = {
        "schema": "cl-mpm.unnotched-gravity.native-controls.evidence.v1",
        "createdUtc": datetime.now(timezone.utc).isoformat(), "baselineCommit": BASELINE,
        "status": "FOCUSED_GATES_PASS_WITH_RETAINED_NEGATIVE_FIXTURES",
        "native001": {"harnessExit": 1, "passedGroups": native001["passedControls"],
                      "failure": native001["failure"], "actualMpmUpdates": 2,
                      "scope": "Real solver and outputs completed; caller-thread-only instrumentation flag missed worker constitutive calls. This is a test harness failure, not a zero-material-call production claim."},
        "native002": {"harnessExit": 0, "passedGroups": native002["passedControls"],
                      "skippedGroups": native002["skippedControls"],
                      "actualMpmUpdates": native002["physicalUpdatesExecuted"],
                      "materialCallsAttempted": native002["materialCallsAttempted"],
                      "materialCallsAccepted": native002["materialCallsAccepted"],
                      "wallSecondsForRunnerOnly": native002["observations"]["runnerWallSeconds"],
                      "savedStates": 3, "particleRows": 2640, "historyRows": 3, "particleCount": 880},
        "aggregateDistinctNativeGroupsPassed": 9, "totalActualMpmUpdatesBothAttempts": 4,
        "native001And002NumericalOutputsByteIdentical": True,
        "independentSavedAudits": {"attempt001": first_review["integrityStatus"], "attempt002": second_review["integrityStatus"]},
        "monitor": {"status": monitor["status"], "syntheticAssertions": len(monitor["controls"]), "actualMpmUpdates": 0},
        "detached001": {"status": "RETAINED_NEGATIVE_FIXTURE", "workerExit": 8,
                        "reason": "Verify arrived after the fixture 60-second release deadline; no MPM run."},
        "detached002": {"status": detached["status"], "controls": detached["controls"],
                        "gravitySelectionAssertions": detached["gravitySelectionAssertions"], "actualMpmUpdates": 0},
        "nativeFullSlopeStatus": "NOT_RUN_AT_THIS_GATE", "landslideVerified": False,
        "scientificallyValidated": False,
        "scope": "Input/boundary/ramp/material binding, source freezing, two-step native integration and process monitoring; no full-duration instability, runout or journal reproduction claim."}
    write_json(PACKET / "summary.json", summary)
    (PACKET / "README.md").write_text(
        "# Unnotched gravity/SSR native and process gates\n\n"
        "Nine distinct native groups passed across two retained attempts: five input groups in001, four output groups in002. "
        "Attempt001's runner assertion failed because a caller-thread dynamic flag was invisible to native worker threads. "
        "Attempt002 fixes only shared counter instrumentation, skips the five passed groups, and records1760 accepted constitutive calls and2 real updates. "
        "Both attempts saved the same3 VTK states and2 CSV files byte for byte. Four total MPM updates were executed, not one full-duration slope run.\n\n"
        "Each native archive includes285 exact pre-load source/input/DLL files, its manifest and four source/runtime proof files; all290 members were read and CRC/byte verified. "
        "ASDF actions and actual mapped DLL identity are in source-provenance*.json. The sole source difference between attempts is the executed test driver. "
        "All production numerical files match baseline2308a1e and the executed snapshots.\n\n"
        "Process fixtures retain detached001 worker exit8 (release deadline missed), detached0029 controls plus2 gravity-selection assertions, "
        "and13 synthetic monitor assertions. These fixtures perform zero MPM updates and do not prove survival of sleep/logoff/reboot. "
        "All available requests, worker scripts, logs and process identities remain included.\n\n"
        "Analysis provenance limitation: the exact first review script version was not saved before an update; its recorded SHA256 and original report/media remain retained. "
        "The copied analysis script exactly matches the second review's recorded hash. Do not attribute current analysis bytes to the first review. "
        "The unchanged imported VTK reader is included with baseline comparison; its at-review hash was not separately recorded.\n\n"
        "Full6-second slope trials are NOT_RUN at this gate. No landslide or scientific validation is claimed. "
        "The raw bytes, failed fixtures and original sources are preserved; .gitattributes prevents newline normalization. "
        "SHA256SUMS.json indexes all packet files except itself. Indexed PNG/VTK files may require git add -f; no staging is performed by this packer.\n",
        encoding="utf-8", newline="\n")
    files = [record(p, PACKET) for p in sorted(PACKET.rglob("*")) if p.is_file() and p.name != "SHA256SUMS.json"]
    write_json(PACKET / "SHA256SUMS.json", {"artifactCount": len(files), "files": files})
    for row in files:
        actual = record(PACKET / row["path"], PACKET)
        if actual != row:
            raise RuntimeError(f"Indexed payload mismatch: {row['path']}")
    if (PACKET / "executed-pack-script.py").read_bytes() != Path(__file__).read_bytes():
        raise RuntimeError("Executed packing script was not retained exactly")
    print(json.dumps({"packet": str(PACKET), "indexedArtifacts": len(files),
                      "decodedArchiveMembers": sum(v["zipMemberCount"] for v in verification),
                      "status": summary["status"]}))


if __name__ == "__main__":
    main()
