"""Freeze the real partial Soil2 output, failure, runtime, source and media evidence."""
from pathlib import Path
import gzip
import hashlib
import io
import json
import shutil
import tarfile
import numpy as np

ROOT=Path(__file__).resolve().parents[4]
RUN=ROOT/"output/wang2017-soil2-2026-10-24/fast-010-001"
REVIEW=RUN.with_name(RUN.name+"-review")
DEST=ROOT/"docs/evidence/wang2017-soil2-2026-10-24/fast-010-001-failed"


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding="utf-8-sig"))


def archive(path,files):
    records=[]
    with path.open("wb") as raw,gzip.GzipFile(fileobj=raw,mode="wb",mtime=0,filename="") as zipped:
        with tarfile.open(fileobj=zipped,mode="w") as tar:
            for name,source in sorted(files):
                data=source.read_bytes();info=tarfile.TarInfo(name);info.size,info.mtime=len(data),0
                tar.addfile(info,io.BytesIO(data))
                records.append({"path":name,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()})
    with tarfile.open(path,"r:gz") as tar:
        assert len(tar.getmembers())==len(records)
        for record in records:
            data=tar.extractfile(record["path"]).read()
            assert len(data)==record["bytes"] and hashlib.sha256(data).hexdigest()==record["sha256"]
    return records


def copy(source,target):
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    assert sha(source)==sha(target)


def main():
    manifest=read(RUN/"manifest.json")
    status=read(RUN.with_name(RUN.name+"-status.json"))
    review=read(REVIEW/"failed-soil2-saved-review.json")
    boundary=read(REVIEW/"boundary-tension-review.json")
    provenance=read(RUN/"source-provenance.json")
    audit=read(RUN/"output-audit.json")
    assert manifest["complete"] is False and status["nativeExitCode"]==1
    assert read(REVIEW/"partial-render-status.json")["rendererExitCode"]==2
    assert read(REVIEW/"video-decode-status.json")["decodeExit"]==0
    probe=read(REVIEW/"video-probe.json")["streams"][0]
    timestamps=read(REVIEW/"video-frame-timestamps.json")["frames"]
    pts=[float(row["best_effort_timestamp_time"]) for row in timestamps]
    assert len(pts)==58 and int(probe["nb_read_frames"])==58 and np.allclose(np.diff(pts),.25,rtol=0,atol=1e-12)
    assert audit["frames"]==58 and audit["nativeComplete"] is False and audit["passedConsistencyChecks"]
    assert audit["visualization"]["displacementScale"]==1 and not audit["visualization"]["interpolatedStates"]
    files=read(RUN/"source/source-manifest.json")["files"]
    assert all(sha(RUN/item["path"])==item["sha256"] for item in files)
    current_matches=[sha(Path(item["originalPath"]))==item["sha256"] for item in files]
    assert all(current_matches)
    assert provenance["sourceSnapshotExactLoadedBytes"] and provenance["copiedByteEqualityBeforeLoad"]
    for name,expected in status["postprocessorSha256"].items():assert sha(ROOT/name)==expected.lower()
    assert all(sha(RUN/row["path"])==row["sha256"] for row in audit["sources"])
    media_qa={"scope":"Actual partial native states only; not completed simulation or scientific validation",
              "nativeFrames":58,"nativeTimeRangeS":[0,5.7],"savedPhysicalCadenceS":.1,
              "videoFrames":58,"videoFps":4,"videoDurationS":float(probe["duration"]),
              "firstVideoPresentationTimestampS":pts[0],"lastVideoPresentationTimestampS":pts[-1],
              "playbackTimePerPhysicalTimeBetweenFrames":2.5,"lastFrameHoldS":.25,
              "temporalInterpretation":"Each displayed label uses actual native time;4fps playback slows .1s saved intervals to .25s. This is not real-time playback.",
              "displacementScale":1,"interpolation":False,"fixedAxesAndColour":audit["visualization"],
              "codec":probe["codec_name"],"pixelFormat":probe["pix_fmt"],"width":probe["width"],"height":probe["height"],
              "fullDecodeExitCode":0,"rendererExitCode":2,"renderScope":"Expected incomplete exit retained; completion assertion was not weakened",
              "viewportInspection":"Overview and boundary-diagnosis PNG visually inspected; labels explicitly show INCOMPLETE, assumed geometry,100x reference,actual coordinates and non-damage paper kps",
              "nativeVtkHashesVerified":len(audit["sources"])}
    (REVIEW/"media-qa.json").write_text(json.dumps(media_qa,indent=2)+"\n",encoding="utf-8")
    summary={"classification":"FAILED_NATIVE / INCOMPLETE","nativeExitCode":1,"nativeComplete":False,
             "sourceCommitAtLaunch":status["sourceCommitAtLaunch"],"nativeEndedUtc":status["nativeEndedUtc"],
             "lastSavedStates":58,"lastSavedTimeS":5.7,"lastSavedCommandedSettlementM":.057,
             "lastSavedLoadingUpdates":review["lastSavedLoadingUpdates"],"failureManifestLoadingUpdates":review["failureManifestLoadingUpdates"],
             "failureTime":"Later unsaved material transaction; last saved time/displacement is not exact failure time. Capsule has no global particle ID/time.",
             "failureReason":read(RUN/"mc-integration-failure.json")["reason"],"historyGuardFailure":"Not the recorded reason",
             "scientificValidation":False,"landslideVerified":False,"referenceSpeed":False,
             "frozenSourcesVerified":len(files),"workspaceSourceBytesStillMatchExecutedSnapshot":all(current_matches),
             "actualMappedBackend":provenance["nativeBackend"],
             "commonSavedSoil1CommandPairs":review["soil1Comparison"]["sameSavedCommandPairs"],
             "savedBoundaryDiagnosis":{"negativeGeometricGapCount":boundary["negativeSavedGeometricGapCount"],
                                       "exactIndividualPredictedTractions":"Not saved","failureParticle":"Nearest saved Ep signature only an inference"},
             "media":media_qa}
    DEST.parent.mkdir(parents=True,exist_ok=True);DEST.mkdir(exist_ok=False)
    (DEST/".gitattributes").write_text("* -text -whitespace\n*.gz binary\n*.png binary\n*.mp4 binary\n",encoding="utf-8")
    archive_records={}
    native_files=[(p.relative_to(RUN).as_posix(),p) for p in RUN.rglob("*") if p.is_file()
                  and "source" not in p.relative_to(RUN).parts and "rendered-frames" not in p.relative_to(RUN).parts
                  and p.suffix not in (".png",".mp4")]
    archive_records["native-partial-output.tar.gz"]=archive(DEST/"native-partial-output.tar.gz",native_files)
    source=RUN/"source"
    archive_records["executed-source.tar.gz"]=archive(DEST/"executed-source.tar.gz",
        [(p.relative_to(source).as_posix(),p) for p in source.rglob("*") if p.is_file() and ".native-cache" not in p.parts])
    runtime=[(p.name,p) for p in RUN.parent.glob(RUN.name+"*") if p.is_file()]
    detached=RUN.with_name(RUN.name+"-detached")
    runtime.extend(("detached/"+p.relative_to(detached).as_posix(),p) for p in detached.rglob("*") if p.is_file())
    archive_records["runtime-and-native-logs.tar.gz"]=archive(DEST/"runtime-and-native-logs.tar.gz",runtime)
    for name in ("manifest.json","output-audit.json","source-provenance.json","mc-integration-failure.json","descent-overview.png","energy-diagnostics.png","slope-descent.mp4"):
        copy(RUN/name,DEST/name)
    for path in REVIEW.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            copy(path,DEST/"review"/path.relative_to(REVIEW))
    for name in status["postprocessorSha256"]:
        copy(ROOT/name,DEST/"renderer-support"/Path(name).name)
    (DEST/"archive-input-manifest.json").write_text(json.dumps(archive_records,indent=2)+"\n",encoding="utf-8")
    (DEST/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    (DEST/"README.md").write_text(
      "# Incomplete native Wang2017 Soil2 run: retained failure and partial output\n\n"
      "Actual Windows native exit1 on24October2026 at08:26:52WIB. Fifty-eight saved states cover0–5.7physical seconds and0–57mm at0.01m/s (100x paper rate); the requested6s/60mm target was NOT completed. "
      "Last saved CSV records19608 loading updates; the failure manifest reports19820 after later unsaved work. The material capsule has no global particle ID or exact solver time. Its reason is no admissible signed-tensor Soil2 solution; this is not reported as a history-guard failure or a landslide.\n\n"
      "Raw915-ID VTK,53070 material rows,348 contact rows, gravity/loading CSV, capsule and runtime logs are retained without alteration. Actual F/J, transported Ep/paper invariant, cohesion, rotation and contact identities were checked from the saved data. "
      "Saved accepted history-decrease flags include only roundoff-scale differences; details remain explicit in the review. Sparse frames do not reconstruct every unsaved material transaction. "
      "The58 exact common settlements versus completed Soil1 are compared without interpolation or scientific-agreement PASS; each run uses its own settled displacement origin. Native summed-J2 and paper tensor invariants are not subtracted as though identical.\n\n"
      "The partial video contains exactly58 actual states, fixed coordinate/colour bounds, displacement scale1 and no interpolation. Renderer exit2 correctly preserves INCOMPLETE; full H264/yuv420p decode exit0 is only media QA. "
      "Four-fps playback lasts14.5s and slows native0.1s saved intervals to0.25s; every displayed time is the actual native time, not real-time playback. Overview and boundary-diagnosis viewports were inspected.\n\n"
      "No saved geometric strip gap is tensile; actual individual predicted-corner tractions were not recorded. Reconstructed positive mean stress is explicitly distinguished from directly exported stress; nearest failed-state Ep matching is labelled INFERENCE, not an exact failure particle. "
      "A compression-only platen would be a new boundary experiment, not a demonstrated cure. Driven settlement, plastic colour and isolated speed do not establish coherent landslide or run-out; no free above-base mass crossed the original toe. "
      "Elastic/plastic/spring quantities are observations, not closed energy accounting. Assumed relief, fixed boundaries, local-softening mesh sensitivity and unverified paper-speed/curve agreement remain limitations.\n\n"
      "Every archive was reopened and all member bytes/lengths/SHA-256 checked against its input. The271 frozen source records and current workspace originals still match; source/DLL/provenance and exact renderer/analysis sources are included, excluding private compiled caches. "
      "The independent capsule replay is owned by a separate retained review and was not repeated here. No solver, constitutive change, completion-tolerance change or paper validation was performed by this postprocessing.\n",encoding="utf-8")
    assert all(sha(RUN/item["path"])==item["sha256"] for item in files)
    entries=[{"path":p.relative_to(DEST).as_posix(),"bytes":p.stat().st_size,"sha256":sha(p)}
             for p in sorted(DEST.rglob("*")) if p.is_file()]
    (DEST/"evidence-manifest.json").write_text(json.dumps({"scope":"Native failed/incomplete; no scientific PASS", "entries":entries},indent=2)+"\n",encoding="utf-8")
    assert all(sha(DEST/entry["path"])==entry["sha256"] for entry in entries)
    print(json.dumps({"verifiedArtifacts":len(entries),"archiveMembers":{k:len(v) for k,v in archive_records.items()},"destination":str(DEST)}))


if __name__=="__main__":
    main()
