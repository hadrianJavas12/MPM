"""Freeze interrupted-run evidence; no solver, rerendering, or original-output edits."""
from pathlib import Path
import gzip
import hashlib
import io
import json
import shutil
import tarfile

ROOT = Path(__file__).resolve().parents[4]
RUN = ROOT / "output/wang2017-reference-2026-10-23/rate-002-001"
REVIEW = RUN.with_name(RUN.name + "-review")
DEST = ROOT / "docs/evidence/wang2017-reference-2026-10-24/rate-002-001-interruption"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archive(destination, files):
    entries = []
    with destination.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as zipped:
        with tarfile.open(fileobj=zipped, mode="w") as tar:
            for name, path in sorted(files):
                data = path.read_bytes()
                info = tarfile.TarInfo(name)
                info.size, info.mtime = len(data), 0
                tar.addfile(info, io.BytesIO(data))
                entries.append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    with tarfile.open(destination, "r:gz") as tar:
        if len(tar.getmembers()) != len(entries):
            raise ValueError("Archive member count differs")
        for record in entries:
            data = tar.extractfile(record["path"]).read()
            if len(data) != record["bytes"] or hashlib.sha256(data).hexdigest() != record["sha256"]:
                raise ValueError("Archived bytes differ from inputs")
    return entries


def copy_file(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    if sha(source) != sha(target):
        raise ValueError("Copied bytes differ")


def main():
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.mkdir(exist_ok=False)
    (DEST / ".gitattributes").write_text("* -text -whitespace\n*.gz binary\n*.png binary\n*.mp4 binary\n", encoding="utf-8")
    original_inputs = {}
    for relative, file in [(p.relative_to(RUN).as_posix(), p) for p in RUN.rglob("*")
                           if p.is_file() and "source" not in p.relative_to(RUN).parts
                           and "rendered-frames" not in p.relative_to(RUN).parts]:
        original_inputs["run/" + relative] = sha(file)
    archive_records = {}
    archive_records["native-output.tar.gz"] = archive(DEST / "native-output.tar.gz", [
        (p.relative_to(RUN).as_posix(), p) for p in RUN.rglob("*") if p.is_file()
        and "source" not in p.relative_to(RUN).parts and "rendered-frames" not in p.relative_to(RUN).parts
        and p.suffix not in (".png", ".mp4")])
    archive_records["executed-source.tar.gz"] = archive(DEST / "executed-source.tar.gz", [
        (p.relative_to(RUN / "source").as_posix(), p) for p in (RUN / "source").rglob("*")
        if p.is_file() and ".native-cache" not in p.parts])
    archive_records["adjacent-status-and-logs.tar.gz"] = archive(DEST / "adjacent-status-and-logs.tar.gz", [
        (p.name, p) for p in RUN.parent.glob(RUN.name + "*") if p.is_file()])
    for name in ("manifest.json", "output-audit.json", "source-provenance.json", "descent-overview.png", "energy-diagnostics.png", "slope-descent.mp4"):
        copy_file(RUN / name, DEST / name)
    for file in REVIEW.rglob("*"):
        if file.is_file():
            copy_file(file, DEST / "review" / file.relative_to(REVIEW))
    for name in ("plot-wang2017-descent.py", "plot_m5_cliff_comparison.py", "collect-wang2017-evidence.py"):
        copy_file(ROOT / "scripts" / name, DEST / "renderer-support" / name)
    (DEST / "archive-input-manifest.json").write_text(json.dumps(archive_records, indent=2) + "\n", encoding="utf-8")
    comparison = json.loads((REVIEW / "saved-rate-comparison.json").read_text())
    process = json.loads(RUN.with_name(RUN.name + "-process-reconciliation.json").read_text(encoding="utf-8-sig"))
    manifest = json.loads((RUN / "manifest.json").read_text())
    summary = {
        "classification": process["classification"], "nativeExitCode": None, "nativeComplete": False,
        "originalAdjacentStatusPreserved": "NATIVE_RUNNING (stale; processes absent at later audit)",
        "sourceCommitAtLaunch": process["sourceCommitAtLaunch"], "loadingFrames": 33,
        "loadingTimeS": 6.4, "lastCommandedSettlementM": .0128,
        "velocityMPerS": .002, "paperVelocityMPerS": .0001, "loadingRateMultiplier": 20,
        "requestedDurationS": 50, "requestedSettlementM": .1,
        "materialFailureProven": False, "wallBudgetTerminationProven": False,
        "externalInterruptionCause": "UNPROVEN: logoff/sleep timing is correlation, not historical process-session attribution",
        "rendererExitCode": 2, "rendererScope": "Saved-output consistency and partial fixed-scale media; expected incomplete exit",
        "savedComparison": {"slowFrames": comparison["slow"]["loadingFrames"], "fastFrames": comparison["fast"]["loadingFrames"],
                            "exactMatchedCommandCount": comparison["matchedSavedCommandCount"], "commonCommandsM": comparison["commonCommandsM"]},
        "loadingDeterminantJ": "NOT_DIRECTLY_SAVED: positive saved volume ratios are not independent det(F) evidence",
        "scientificValidation": False, "referenceSpeedRun": False, "quasiStaticConvergence": "NOT_VERIFIED",
        "geometryCaveat": "Relief10m assumed; bottom tangential restraint and comparison endpoint not independently paper-verified",
        "energyCaveat": manifest["energyConvention"],
        "originalRunInputsSha256BeforeCollection": original_inputs,
    }
    (DEST / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (DEST / "README.md").write_text(
        "# Interrupted Wang2017 rate study: retained evidence\n\n"
        "Native Windows MPM saved33 loading states,915 particles, through6.4s and12.8mm commanded descent at0.002m/s (20x paper rate). "
        "The intended50s/0.1m run is INCOMPLETE. Historical wrapper/cmd/SBCL were absent at audit; final native exit code and cause are UNKNOWN. "
        "The original adjacent NATIVE_RUNNING status remains unmodified inside adjacent-status-and-logs.tar.gz; read the separate process reconciliation. "
        "A correlated Windows logoff/sleep is not proven attribution. Neither wall-budget termination nor a new material failure is established.\n\n"
        "native-output.tar.gz preserves actual VTK/CSV/provenance; executed-source.tar.gz excludes only the private compiled cache. "
        "Archives were reopened and every member SHA-256/byte length checked against its input. Original run inputs were not changed. "
        "Fixed-scale PNG/MP4 and full decode/probe evidence are included; renderer exit2 correctly reports incomplete native output. "
        "Review scripts/results compare33 slower and78 prior faster saved states at7 exact common commanded settlements0,2,4,6,8,10,12mm, with native ID alignment and no interpolation. "
        "No rate-agreement tolerance PASS is assigned. Loading deformation determinant J was not directly saved; positive volume ratios are reported separately.\n\n"
        "Native mc-kappa is accumulated plastic history, not damage or Soil2 paper history. KE/elastic/native-plastic quantities do not form a closed energy budget. "
        "No completed landslide, paper-speed result, FEM equivalence, mesh/time-step/rate convergence or scientific validation is claimed. "
        "The comparator fast run's complete raw evidence remains in the previously retained diagnostic-fast-005-002-failure packet; per-frame hashes are linked in review/analysis-input-hashes.json.\n",
        encoding="utf-8")
    for name, expected in original_inputs.items():
        if sha(RUN / name.removeprefix("run/")) != expected:
            raise ValueError("Original input changed during collection")
    entries = [{"path": p.relative_to(DEST).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p)}
               for p in sorted(DEST.rglob("*")) if p.is_file()]
    (DEST / "evidence-manifest.json").write_text(json.dumps({"scope": "Interrupted run; native exit unknown; not scientific validation", "entries": entries}, indent=2) + "\n", encoding="utf-8")
    if not all(sha(DEST / entry["path"]) == entry["sha256"] for entry in entries):
        raise ValueError("Evidence hash mismatch")
    print(json.dumps({"verifiedArtifactCount": len(entries), "archiveMemberCounts": {k: len(v) for k, v in archive_records.items()}, "destination": str(DEST)}))


if __name__ == "__main__":
    main()
