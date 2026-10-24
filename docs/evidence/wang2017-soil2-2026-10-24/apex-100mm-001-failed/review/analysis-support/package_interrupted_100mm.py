"""Freeze failed100mm evidence without changing originals or rerunning native work."""
from pathlib import Path
from datetime import datetime,timezone
import gzip
import hashlib
import io
import json
import shutil
import tarfile

ROOT=Path(__file__).resolve().parents[4]
RUN=ROOT/"output/wang2017-soil2-2026-10-24/apex-100mm-001"
REVIEW=RUN.with_name(RUN.name+"-review")
DEST=ROOT/"docs/evidence/wang2017-soil2-2026-10-24/apex-100mm-001-failed"


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding="utf-8-sig"))


def archive(path,files):
    records=[]
    assert len({name for name,_ in files})==len(files)
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
    status=read(RUN.with_name(RUN.name+"-status.json"));manifest=read(RUN/"manifest.json")
    review=read(REVIEW/"interrupted-100mm-physical-review.json")
    prefix=read(REVIEW/"completed-prefix-comparison.json")
    context=read(REVIEW/"residual-contact-prefix-context.json")
    media=read(REVIEW/"media-qa.json");audit=read(RUN/"output-audit.json")
    provenance=read(RUN/"source-provenance.json");capsule=read(RUN/"mc-integration-failure.json")
    assert status["nativeExitCode"]==1 and manifest["complete"] is False and manifest["loadingUpdates"]==31092
    assert review["lastSavedAcceptedUpdates"]==30960 and review["lastSavedTimeS"]==9
    assert review["audit"]["materialCsvRows"]==83265 and review["audit"]["contactCsvRows"]==546
    assert audit["frames"]==91 and audit["nativeComplete"] is False and audit["passedConsistencyChecks"]
    assert read(REVIEW/"partial-render-status.json")["rendererExitCode"]==2
    assert read(REVIEW/"video-decode-status.json")["decodeExit"]==0
    assert media["videoFrames"]==91 and media["spatialDisplacementScale"]==1 and not media["interpolation"]
    assert prefix["matchedStates"]==61 and not prefix["allCanonicalPointwiseMetricsPass"]
    assert prefix["tolerances"]["atol"]==1e-8 and prefix["tolerances"]["rtol"]==1e-7 and prefix["tolerances"]["timeAtol"]==1e-10
    assert set(prefix["failedMetricNames"])=={"vtk:mc-yield-residual-kirchhoff-pa","vtk:sig_xy","vtk:wang-history-decrease-accepted"}
    frozen=read(RUN/"source/source-manifest.json")["files"]
    assert len(frozen)==275 and all(sha(RUN/item["path"])==item["sha256"] for item in frozen)
    current_records=[{"path":item["originalPath"],"snapshotSha256":item["sha256"],
                      "currentSha256":sha(Path(item["originalPath"])) if Path(item["originalPath"]).is_file() else None}
                     for item in frozen]
    current_differences=[r for r in current_records if r["currentSha256"]!=r["snapshotSha256"]]
    assert provenance["sourceSnapshotExactLoadedBytes"] and provenance["copiedByteEqualityBeforeLoad"]
    assert all(sha(RUN/r["path"])==r["sha256"] for r in audit["sources"])
    assert all(sha(ROOT/name)==expected.lower() for name,expected in status["postprocessorSha256"].items())
    DEST.parent.mkdir(parents=True,exist_ok=True);DEST.mkdir(exist_ok=False)
    (DEST/".gitattributes").write_text("* -text -whitespace\n*.gz binary\n*.png binary\n*.mp4 binary\n",encoding="utf-8")
    source=RUN/"source"
    excluded=[p for p in source.rglob("*") if p.is_file() and (".native-cache" in p.parts or "__pycache__" in p.parts or p.suffix==".fasl")]
    archive_records={}
    native_files=[(p.relative_to(RUN).as_posix(),p) for p in RUN.rglob("*") if p.is_file()
                  and "source" not in p.relative_to(RUN).parts and "rendered-frames" not in p.relative_to(RUN).parts
                  and p.suffix not in (".png",".mp4")]
    archive_records["native-partial-output.tar.gz"]=archive(DEST/"native-partial-output.tar.gz",native_files)
    archive_records["executed-source.tar.gz"]=archive(DEST/"executed-source.tar.gz",
        [(p.relative_to(source).as_posix(),p) for p in source.rglob("*") if p.is_file() and p not in excluded])
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
    copy(ROOT/"scripts/compare-framework-runs.py",DEST/"analysis-reference"/"compare-framework-runs.py")
    (DEST/"archive-input-manifest.json").write_text(json.dumps(archive_records,indent=2)+"\n",encoding="utf-8")
    source_verification={"checkedUtc":datetime.now(timezone.utc).isoformat(),"frozenRecordsVerified":len(frozen),
                         "snapshotOriginalsScope":"Current comparison is temporal; newer authorized code changes do not alter the executed snapshot",
                         "workspaceDifferencesFromExecutedSnapshot":current_differences,
                         "excludedPrivateCompiledCacheFiles":[{"path":p.relative_to(source).as_posix(),"bytes":p.stat().st_size} for p in excluded],
                         "postprocessorOriginalsMatchLaunchHashes":True,"allAuditVtkSourceHashesMatch":True}
    (DEST/"source-verification.json").write_text(json.dumps(source_verification,indent=2)+"\n",encoding="utf-8")
    summary={"classification":"FAILED_NATIVE / INCOMPLETE","sourceCommitAtLaunch":status["sourceCommitAtLaunch"],
             "nativeExitCode":1,"nativeComplete":False,"nativeEndedUtc":status["nativeEndedUtc"],"stoppedByWallBudget":False,
             "requestedEndTimeS":10,"requestedEndSettlementM":.1,"lastSavedTimeS":9,"lastSavedCommandedSettlementM":.09,
             "savedLoadingUpdates":30960,"failureManifestLoadingUpdates":31092,"savedStates":91,"particleIds":915,
             "materialRows":83265,"contactRows":546,"failureReason":capsule["reason"],
             "failureTimingScope":"Failed transaction is later than last saved state. Capsule has no global particle ID or exact solver time.",
             "scientificValidation":False,"coherentLandslideVerified":False,"frozenSourceRecordsVerified":len(frozen),
             "savedIdentityAudit":review["audit"],"reaction":review["reaction"],"freeMotion":review["motion"]["freeAboveBaseExcludingSixDriven"],
             "runout":review["runout"],"residualStrengthParticles":context["residualStrength"]["finalCount"],
             "canonicalPrefixPass":False,"canonicalPrefixFailedFields":prefix["failedMetricNames"],"media":media,
             "actualMappedBackend":provenance["nativeBackend"]}
    (DEST/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    (DEST/"README.md").write_text(
        "# Wang2017 Soil2 apex: failed100mm trial and actual saved evidence\n\n"
        "Windows native exit1 occurred24October2026 at15:55:34WIB on source3caa6bea5d447be34c8bd1104311f1aa34b57986, before the3h wall budget. "
        "The10s/100mm target at0.01m/s (100x paper rate) was NOT completed. Ninety-one saved states cover0–9s and0–90mm. "
        "The last saved CSV has30960 accepted loading updates; failure manifest31092 includes later unsaved work. "
        "The actual capsule rejects a signed-history decrease outside the declared monotonic scope. Its old/new kps are both on residual cohesion15kPa; independent replay is retained separately and was not repeated here. Capsule has no global particle ID or exact failure time.\n\n"
        "Raw915-ID VTK,83265 material rows,546 contact rows, gravity/loading CSV, F9/J/Ep6/rotation/apex-volume state, capsule, executed-source snapshot, loaded DLL proof, launch and detached-worker logs are retained. "
        "All saved numeric fields are finite, IDs/mass remain stable, volumes/J positive, and material/contact identities pass their recorded checks. Loading det(F) was independently reconstructed from saved material F9, not inferred solely from particle-volume ratio. "
        "These saved-state checks cannot approve the later rejected transaction. Post-commit volume increments may be0 although accumulated apex plastic volume increases. Four particles accumulate positive loading-interval apex volume, and15 reach residual cohesion by9s.\n\n"
        "Reaction peaks644.162kN/m at6.1s, then falls7.12% to598.325kN/m at9s. "
        "For509 originally above-base particles excluding6 driven contacts, the settled-origin centroid moves5.05mm right and19.91mm down; no selected mass crosses the original toe. "
        "Mean free velocity is small relative to RMS; the fastest final particle is moving upward. Local weakening and a reaction drop do not establish a coherent landslide or run-out. "
        "All saved geometric strip gaps are nonnegative. Individual predicted-corner forces are not exported; spring/elastic/plastic/work observations do not close energy or prove quasistatic response.\n\n"
        "The61 exact Decimal saved settlements0–60mm are compared to the completed60mm apex run using the unchanged canonical atol1e-8/rtol1e-7/time1e-10. "
        "Overall pointwise comparison is FAIL: yield-residual stress4 values, sig_xy5 values, and history-decrease flag130 values differ. "
        "Positions, reaction, paper kps, cohesion and other fields pass; raw maxima and individual failed values are retained. "
        "Small global field-scale stress diagnostics do not replace the pointwise failures. Differing history flags have roundoff-scale last-step kps changes; no flag/tolerance was removed to claim PASS. "
        "Soil1 comparison uses its own settled displacement origin and does not equate native summed-J2 with paper tensor norm.\n\n"
        "Partial video contains91 actual states at4fps,22.75s, fixed coordinate/colour scales, displacement scale1 and no interpolation. "
        "Expected renderer exit2 retains INCOMPLETE; full H264/yuv420p decode exit0 is media QA only. Native0.1s intervals display for0.25s, with actual native-time labels. "
        "Overview and physical-diagnostics viewports were inspected. Relief10m remains assumed; accelerated loading, finite penalty compliance, fixed bottom/side rollers, local-softening mesh sensitivity, no hold/release and unverified reference-speed agreement remain limitations.\n\n"
        "All three archives were reopened and every member byte count/SHA256 verified;275 frozen source records and all VTK audit hashes match. "
        "Private compiled caches are excluded from the archive and listed; originals remain untouched. Source-verification records any subsequent authorized workspace changes independently of immutable executed bytes. "
        "No solver, replay, numerical-policy edit, tolerance relaxation or scientific-validation PASS was performed by this saved-data review.\n",encoding="utf-8")
    assert all(sha(RUN/item["path"])==item["sha256"] for item in frozen)
    entries=[{"path":p.relative_to(DEST).as_posix(),"bytes":p.stat().st_size,"sha256":sha(p)}
             for p in sorted(DEST.rglob("*")) if p.is_file()]
    (DEST/"evidence-manifest.json").write_text(json.dumps({"scope":"Failed/incomplete native output; no scientific PASS","entries":entries},indent=2)+"\n",encoding="utf-8")
    assert all(sha(DEST/r["path"])==r["sha256"] for r in entries)
    print(json.dumps({"verifiedArtifacts":len(entries),"bytes":sum(r["bytes"] for r in entries),
                      "archiveMembers":{name:len(records) for name,records in archive_records.items()},
                      "snapshotRecords":len(frozen),"workspaceSourceDifferences":len(current_differences),"destination":str(DEST)},indent=2))


if __name__=="__main__":main()
