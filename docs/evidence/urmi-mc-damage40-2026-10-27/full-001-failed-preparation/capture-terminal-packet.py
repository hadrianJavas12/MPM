"""Saved-only terminal evidence collector. Never imports/launches the solver."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone

ROOT = Path(r"D:\MPM")
BASE = ROOT / "output/urmi-mc-damage40-2026-10-27"
RUN = BASE / "full-001"
PREP = BASE / "full-001-launch-preparation"
OBS = BASE / "full-001-terminal-saved-observer-001"
PACKET = Path(__file__).resolve().parent
ARCHIVE = PACKET / "terminal-retained-data-and-records.zip"


def stamp():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def record(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": digest(data)}


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(name, value):
    path = PACKET / name
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


if ARCHIVE.exists() or (PACKET / "summary.json").exists():
    raise RuntimeError("Refusing duplicate terminal packet capture")
started = stamp()
observation = load(OBS / "observation.json")
sparse = load(OBS / "stdout-sampled-summary.json")
status = load(BASE / "full-001-status.json")
worker = load(BASE / "full-001-detached/worker-exit.json")
manifest = load(RUN / "manifest.json")
assert observation["status"] == "PASS_SCOPED_INITIAL_VTK_ONLY"
assert observation["sources"]["frozenSourcesVerified"] == 300
assert observation["prelaunchNativePayloadsMatched"] == 300
assert observation["prelaunchSupportCopiesVerified"] == 7
assert not observation["preparedFullReviewExecuted"]
assert status["status"] == "FAILED_NATIVE" and status["nativeExitCode"] == 1
assert worker["status"] == "WORKER_EXITED" and worker["exitCode"] == 1
assert manifest["updates"] == 19320 and manifest["savedFrames"] == 0
assert sparse["samples"] == 193 and sparse["lastLoggedUpdates"] == 19300
assert sparse["postRampLoggedSamplesRFStrictlyBelow1e4"] == 0
assert load(OBS / "observer-exit.json")["exitCode"] == 0
assert load(OBS / "stdout-summary-exit.json")["exitCode"] == 0

copied = []


def copy_exact(source, destination):
    target = PACKET / destination
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    original = record(source)
    frozen = record(target)
    assert original["sha256"] == frozen["sha256"]
    copied.append({"original": original, "copy": dict(frozen, path=destination)})


# Keep exact commands, inputs, stdout/stderr, exits and results of the ONE observer.
for source in sorted(OBS.rglob("*")):
    if source.is_file() and "__pycache__" not in source.parts:
        copy_exact(source, "observer/" + source.relative_to(OBS).as_posix())

preparation = load(PREP / "preparation.json")
copy_exact(PREP / "preparation.json", "prepared/preparation.json")
for support in preparation["support"]:
    source = Path(support["copy"]["path"])
    assert record(source)["sha256"] == support["copy"]["sha256"]
    copy_exact(source, "prepared/" + source.relative_to(PREP).as_posix())

# All surviving non-source run files, terminal logs and detached records ONCE.
# The already closed source/cache archive is referenced rather than recreated.
run_members = [source for source in sorted(RUN.rglob("*"))
               if source.is_file() and source.relative_to(RUN).parts[0] != "source"]
assert [source.relative_to(RUN).as_posix() for source in run_members] == [
    "manifest.json", "source-provenance.json", "vtk/initial.vtk", "vtk/mesh.vtk"]
adjacent = sorted(source for source in BASE.glob("full-001*") if source.is_file())
detached = sorted(source for source in (BASE / "full-001-detached").rglob("*")
                  if source.is_file())
members = [(source, "full-001/" + source.relative_to(RUN).as_posix())
           for source in run_members]
members += [(source, "adjacent/" + source.name) for source in adjacent]
members += [(source, "detached/" + source.relative_to(BASE / "full-001-detached").as_posix())
            for source in detached]
assert len(members) == 17
archive_members = []
with zipfile.ZipFile(ARCHIVE, "x", compression=zipfile.ZIP_DEFLATED) as archive:
    for source, name in members:
        data = source.read_bytes()
        archive.writestr(name, data)
        archive_members.append({"member": name, "original": str(source),
                                "bytes": len(data), "sha256": digest(data)})
with zipfile.ZipFile(ARCHIVE) as archive:
    assert len(archive.infolist()) == len(members)
    for item in archive_members:
        assert digest(archive.read(item["member"])) == item["sha256"]
write("archive-members.json", archive_members)
write("copy-bindings.json", copied)

missing = observation["preflight"]["missingInputs"]
assert all(not (RUN / name).exists() for name in missing)
write("missing-input-inventory.json", {
    "checkedUtc": stamp(), "runDirectory": str(RUN),
    "survivingNonSourceRunFiles": [source.relative_to(RUN).as_posix() for source in run_members],
    "absent": missing, "preparedFullReviewExecuted": False,
    "decision": "NOT_EXECUTED_MISSING_REQUIRED_SAVED_INPUTS",
    "csvReconstructed": False, "noSavedDrainedTransferOrDynamicState": True,
    "sourceSupportedExplanation": "Runner with-open-file scopes use :if-exists :error. Error unwind may close newly created CSVs with :abort T and delete them, despite flushing. Causal native preservation control remains pending; this is not a reproduced experiment."})

# Terminal source-byte/DLL verification is the already executed ONE observer.
# Do not rehash/reload 300 payloads or query historical processes in this collector.
source_reference = observation["sourceArchiveReference"]
assert record(Path(source_reference["path"]))["sha256"] == source_reference["sha256"]
write("source-and-runtime-reference.json", {
    "nativeSourceCommit": observation["terminal"]["sourceCommit"],
    "closedLaunchSourceArchive": source_reference,
    "terminalVerification": "observer/observation.json",
    "terminalVerificationCommandBefore": "observer/observer-command-before.json",
    "terminalVerificationExit": "observer/observer-exit.json",
    "terminalVerificationCount": 1,
    "frozenNativePayloads": 300,
    "prelaunchPayloadsMatched": 300,
    "prelaunchSupportCopies": 7,
    "actualMappedBackend": observation["sources"]["nativeBackend"],
    "basis": "Persisted actual native loader provenance plus frozen bytes and prelaunch bindings; no new DLL load/native projection/process query.",
    "sourceCacheArchiveRecreated": False})

write("spatial-review.json", {
    "reviewedUtc": stamp(), "method": "Actual generated PNG inspected with view_image before packet closure",
    "image": observation["media"]["png"], "packetImage": "observer/initial-only-scale1.png",
    "coordinateScale": 1, "equalPhysicalAxes": True, "colourRangeStrengthDamage": [0, 1],
    "visibleState": "Only initial geometry: H10m above active4m soil foundation; crest12m; 40degree face reaches toe about23.9175m; domain60x20m; no notch.",
    "particles": 6714, "maxStrengthDamage": 0, "damageActive": False,
    "video": "NOT_PRODUCED_SINGLE_INITIAL_STATE",
    "scope": "No surviving evolved state, motion, damage onset or landslide is inferred."})

summary = {
    "status": "CLOSED_TERMINAL_PREPARATION_FAILURE_WITH_SCOPED_INITIAL_OBSERVER",
    "capturedUtc": stamp(), "nativeTerminal": observation["terminal"],
    "nativeStatus": status["status"], "workerStatus": worker["status"],
    "preparationFailureIsMaterialIntegrationFailure": False,
    "remainingRawArchive": record(ARCHIVE), "archiveMembers": len(archive_members),
    "survivingRunDataFiles": len(run_members), "adjacentModernRecords": len(adjacent),
    "detachedRecords": len(detached), "copiedObserverAndPreparedRecords": len(copied),
    "preparedFullReviewExecuted": False,
    "initialObserver": {"exitCode": 0, "status": observation["status"],
                        "particles": 6714, "scalarFields": 44,
                        "initialVtkStates": 1, "evolvedStates": 0,
                        "dynamicSavedFrames": 0, "png": "observer/initial-only-scale1.png"},
    "sparseStdout": {key: sparse[key] for key in [
        "samples", "acceptedUpdatesFromTerminalManifest", "lastLoggedUpdates",
        "unprintedTailAcceptedUpdates", "minimumRF", "maximumRF", "last",
        "minimumRK", "maximumRK", "postRampLoggedSamplesRFStrictlyBelow1e4",
        "postRampLoggedSamplesBothCriteria", "RFThresholdCrossingsBetweenSparseSamples"]},
    "sourceVerification": {"frozenPayloads": 300, "prelaunchMatched": 300,
                           "supportCopies": 7, "backend": observation["sources"]["nativeBackend"]},
    "fullSourceZipReference": source_reference,
    "savedOnlyCollectorFailureRetained": "collector-attempt-001/failure-result.json",
    "collectorRepair": "Adjacent record selection corrected after first prearchive assertion; existing copied bytes verified without overwrite. Only one raw-data archive created. Initial observer/source verification not repeated.",
    "limitations": observation["limitations"] + [sparse["limitation"]],
    "nativeSolverRerun": False, "replay": False, "oldPidQuery": False,
    "csvReconstructed": False, "landslideVerified": False,
    "scientificValidation": False}
write("summary.json", summary)
readme = """# full-001 failed preparation: terminal saved-only evidence

The first run ended27October2026 at14:31:08WIB (07:31:08Z), native exit1 and worker exit1. It reached20native seconds/19,320accepted preparation updates; dynamic time and saved dynamic frames both0. The owned drained-equilibrium cap stopped preparation. This is not a material return failure or the48h wall deadline.

`terminal-retained-data-and-records.zip` preserves all four surviving non-source run files, six adjacent records/logs and seven detached records (17members). Every member is byte-hashed and read back once; `archive-members.json` lists original paths. Existing raw files remain untouched. The launch packet's executed-source-and-cache.zip is referenced in `source-and-runtime-reference.json`; no new full source archive was made.

The ONE terminal source verification/initial-VTK observer exited0. Its command-before, hashes, exact prepared helpers/contract, stdout/stderr and exit are retained under `observer/`. It verified300frozen native payloads and the actual mapped kirchoff.dll against persisted native loader provenance and prelaunch bindings; seven prepared support copies matched. Prepared support and preparation manifest are retained under `prepared/`; this packet does not reload the DLL or query old PIDs.

The first saved-only packet collector failed before archive creation: a filename glob omitted four dash-named adjacent records. Its exact script, before-command and actual failure are retained in `collector-attempt-001/`. The selection was corrected, existing copies verified without overwrite, and the one raw-data archive created. Neither initial observer/source verification nor solver was repeated.

The intended full saved-data review (--allow-partial --video) was NOT_EXECUTED: all three preparation CSVs are absent; dynamic CSVs/transfer ledger were never created. `missing-input-inventory.json` records actual absence and the unproved source-supported error-unwind explanation. No rows or end-state particles were reconstructed.

Only initial.vtk (6,714particles/44scalar fields) and mesh.vtk survive. The actually viewed `observer/initial-only-scale1.png` has equal physical axes, fixedD_s range0–1, all initialD_s0/inactive and no invented evolution. There is no saved drained, release, or dynamic state; no video can show one. GlobalF/J/volume-reference identity and CSV/VTK pairing cannot be independently checked from these remaining fields.

Actual stdout contains193sparse100-step samples: updates100through19300. MinimumRF=1.2652095995674303e-4 at update16500/time17.082793s; maximumRF=.7824346243003402 at100/.104213s; lastRF=1.328287857836794e-4 andRK=8.125602852883516e-11 at19300/19.980023s. Zero logged post-ramp samples metRF<1e-4, and none met both criteria. The final20accepted updates are not printed. Sparse logs cannot establish per-update/continuous convergence or a final MP state.

This packet is terminal failure preservation and a scoped initial-state observation. No native repeat, replay, old-PID query, CSV reconstruction, landslide evidence or scientific validation is claimed.
"""
with (PACKET / "README.md").open("x", encoding="utf-8", newline="\n") as handle:
    handle.write(readme)
write("collection-result.json", {"passed": True, "startedUtc": started,
                                 "finishedUtc": stamp(), "archiveMembersVerified": len(archive_members),
                                 "copyBindingsVerified": len(copied), "solverLaunched": False})
files = []
for path in sorted(PACKET.rglob("*")):
    if path.is_file() and path.name != "evidence-manifest.json":
        item = record(path)
        item["path"] = path.relative_to(PACKET).as_posix()
        files.append(item)
write("evidence-manifest.json", {"files": files, "indexedFiles": len(files),
                                 "archiveMembers": len(archive_members),
                                 "scope": "Terminal saved-only failure packet; manifest excludes itself."})
print(json.dumps({"passed": True, "indexedFiles": len(files),
                  "archiveMembers": len(archive_members), "copiedRecords": len(copied),
                  "nativeSolverRerun": False}))
