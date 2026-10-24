"""Collection-only metadata/hash checks; no solver, rendering or physical review."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    args = parser.parse_args()
    repo = Path(args.repository).resolve()
    run = repo / "output/wang2017-soil2-2026-10-24/apex-fast-010-001"
    dest = repo / "docs/evidence/wang2017-soil2-2026-10-24/apex-fast-010-001-completed"
    original_index = dest / "evidence-manifest.json"
    original_entries = load(original_index)["entries"]
    for row in original_entries:
        data = (dest / row["path"]).read_bytes()
        assert sha(data) == row["sha256"] and len(data) == row["bytes"]
    shutil.copy2(original_index, dest / "collector-evidence-manifest.json")
    shutil.copy2(dest / "summary.json", dest / "collector-summary-original.json")
    shutil.copy2(dest / "README.md", dest / "collector-README-original.md")
    shutil.copy2(__file__, dest / "support/collection-review.py")
    shutil.copy2(run.with_name(run.name + "-completed-collection.log"), dest / "collection.log")
    archive_proof = load(dest / "archive-verification.json")
    assert archive_proof["passed"] is True
    archives = []
    native_member_names = []
    for archive in archive_proof["archives"]:
        records = archive["members"]
        archive_path = dest / archive["archive"]
        with tarfile.open(archive_path, "r:gz") as handle:
            actual = handle.getmembers()
            assert len(actual) == len(records)
            for member, expected in zip(actual, records):
                data = handle.extractfile(member).read()
                assert member.name == expected["path"] and len(data) == expected["bytes"] and sha(data) == expected["sha256"]
        archives.append({"path": archive_path.name, "bytes": archive_path.stat().st_size, "sha256": sha(archive_path.read_bytes()), "verifiedMembers": len(records)})
        if archive_path.name == "native-output.tar.gz":
            native_member_names = [row["path"] for row in records]
    manifest, audit, provenance = map(load, [run / "manifest.json", run / "output-audit.json", run / "source-provenance.json"])
    status = load(run.with_name(run.name + "-status.json"))
    worker = load(run.with_name(run.name + "-detached") / "worker-exit.json")
    assert status["sourceCommitAtLaunch"] == "55bc85d9d4567b6677439846035127751fbc4c7f"
    assert status["nativeExitCode"] == status["exitCode"] == status["auditAndRenderExitCode"] == worker["exitCode"] == 0
    assert manifest["complete"] is True and audit["passedConsistencyChecks"] and audit["nativeComplete"]
    assert manifest["timeS"] == 6.0 and manifest["commandedSettlementM"] == .06
    frozen = load(run / "source/source-manifest.json")["files"]
    for row in frozen:
        data = (run / row["path"]).read_bytes()
        assert len(data) == row["bytes"] and sha(data) == row["sha256"].lower()
    backend = provenance["nativeBackend"]
    assert provenance["sourceSnapshotExactLoadedBytes"] and provenance["copiedByteEqualityBeforeLoad"]
    assert sha(Path(backend["modulePath"]).read_bytes()) == backend["sha256"].lower()
    assert backend["verifiedBy"] == "GetModuleHandleW/GetModuleFileNameW"
    vtk_sources = [row for row in audit["sources"] if row["path"].lower().endswith(".vtk")]
    for row in vtk_sources:
        assert sha((run / row["path"].replace("\\", "/")).read_bytes()) == row["sha256"].lower()
    arguments = [shutil.which("ffprobe"), "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", str(dest / "slope-descent.mp4")]
    probe = subprocess.run(arguments, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    assert probe.returncode == 0, probe.stderr
    media = json.loads(probe.stdout)
    save(dest / "media-metadata.json", {"command": arguments, "exitCode": probe.returncode, "metadata": media, "stderr": probe.stderr})
    video = [item for item in media["streams"] if item["codec_type"] == "video"]
    assert len(video) == 1
    summary = load(dest / "summary.json")
    summary.update({"scope": "Completed configured accelerated Soil2 composite-apex trial; completion only, no landslide or scientific PASS claim",
                    "constitutiveVariant": "composite-apex", "apexFlowIsAnExplicitMaterialChange": True,
                    "apexFlowConvention": "Additional positive hydrostatic plastic flow gA=p at the MC apex; not strict psi0 shear-only flow or an exact Wang paper convention",
                    "landslideAssessmentInCollection": "NOT_ASSESSED; separate saved-output physical analysis", "scientificValidation": False})
    save(dest / "summary.json", summary)
    note = """# Completed opt-in Soil2 composite-apex trial

**Configured run complete:** native exit0,6s physical loading,60mm commanded
descent at0.01m/s (100times paper rate); audit/render and detached worker exit0.
This is not the600s paper-rate run and collection does not establish a landslide.

This run intentionally uses the NEW optional composite-apex material. It adds
positive hydrostatic volumetric plastic flow at the MC apex (gA=p), while retaining
the stated shear/strength inputs. It is different constitutive physics from the
retained strict zero-dilation run, whose failure evidence remains separate. It
must not be described as an unchanged or paper-exact material model.

The trusted collector executed once after native completion. Its unmodified
original summary/README/index are retained as `collector-*-original` and
`collector-evidence-manifest.json`; this collection-only review adds the explicit
model scope and media/source checks. Production source, solver, renderer and
original run outputs were not modified or rerun.

All native raw CSV/VTK/deformation-gradient files, original audit/manifest/runtime
proof and exact selected executed sources are archived. Detached request, worker
start/exit and adjacent native/wrapper logs are in `control-logs.tar.gz`. The raw
rendered PNG sequence and private compiled cache/FASLs are omitted; their original
folders remain intact. Overview/energy PNGs and the exact MP4 are retained here.
Every archive member is reopened and checked for size/SHA256 and full inventory.

`collection-review.json` records completion/status, source/DLL checks, archive
counts/hashes and media metadata. It performs no physical interpretation, solver,
rendering, numerical test or replay; physical analysis is handled separately.

## Unmodified generic collector context

"""
    (dest / "README.md").write_text(note + (dest / "collector-README-original.md").read_text(), encoding="utf-8")
    csv_names = [name for name in native_member_names if name.lower().endswith(".csv")]
    vtk_names = [name for name in native_member_names if name.lower().endswith(".vtk")]
    excluded_cache = [path for path in (run / "source").rglob("*") if path.is_file() and (".native-cache" in path.parts or path.suffix.lower() == ".fasl")]
    review = {"status": "PASS_COLLECTION_INTEGRITY", "reviewedUtc": datetime.now(timezone.utc).isoformat(),
              "collectorInvocations": 1, "collectorExitCode": 0,
              "collectorExitSource": "Original unified exec session55197 final result, no rerun",
              "sourceCommitAtNativeLaunch": status["sourceCommitAtLaunch"], "nativeExitCode": status["nativeExitCode"],
              "auditAndRenderExitCode": status["auditAndRenderExitCode"], "detachedWorkerExitCode": worker["exitCode"],
              "nativeComplete": manifest["complete"], "physicalTimeS": manifest["timeS"], "commandedSettlementM": manifest["commandedSettlementM"],
              "measuredSettlementM": manifest["measuredSettlementM"], "sourceFiles": len(frozen), "frozenManifestHashesAndSizesMatch": True,
              "launchMappedNativeDllProof": backend, "rendererVtkSourceHashesMatch": len(vtk_sources),
              "archives": archives, "totalVerifiedArchiveMembers": sum(row["verifiedMembers"] for row in archives),
              "archivedCsvFiles": csv_names, "archivedVtkFiles": len(vtk_names), "archivedVtkNameExamples": vtk_names[:4] + vtk_names[-4:],
              "excludedPrivateCacheOrFaslFiles": len(excluded_cache), "omittedRenderedPngFiles": len(list((run / "rendered-frames").glob("*.png"))),
              "media": {key: video[0].get(key) for key in ["codec_name", "pix_fmt", "width", "height", "avg_frame_rate", "nb_read_frames", "duration"]},
              "constitutiveVariant": "Explicit new composite-apex flow; not exact Wang or unchanged strict model",
              "physicalLandslideReview": "NOT_PERFORMED_HERE", "scientificValidation": False,
              "solverRenderTestReplayInvocations": 0}
    save(dest / "collection-review.json", review)
    entries = []
    for path in sorted(dest.rglob("*")):
        if path.is_file() and path.name not in {"evidence-manifest.json", "SHA256SUMS"}:
            data = path.read_bytes()
            entries.append({"path": path.relative_to(dest).as_posix(), "bytes": len(data), "sha256": sha(data)})
    save(original_index, {"scope": "Completed accelerated opt-in composite-apex run, evidence integrity only; no landslide/scientific validation claim.", "entries": entries})
    (dest / "SHA256SUMS").write_text("".join(row["sha256"] + "  " + row["path"] + "\n" for row in entries), encoding="ascii")
    assert all(sha((dest / row["path"]).read_bytes()) == row["sha256"] for row in entries)
    print(json.dumps({"status": review["status"], "indexedArtifacts": len(entries), "sourceFiles": len(frozen), "archives": archives,
                      "totalVerifiedArchiveMembers": review["totalVerifiedArchiveMembers"], "csvFiles": len(csv_names), "vtkFiles": len(vtk_names), "media": review["media"]}, indent=2))


if __name__ == "__main__":
    main()
