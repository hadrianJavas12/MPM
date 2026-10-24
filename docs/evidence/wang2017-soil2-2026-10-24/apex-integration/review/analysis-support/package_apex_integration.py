"""Verify/package existing apex integration evidence. Never rerun a test or solver."""
from pathlib import Path
import csv
import gzip
import hashlib
import io
import json
import shutil
import tarfile

ROOT=Path(__file__).resolve().parents[4]
BASE=ROOT/"output/wang2017-soil2-2026-10-24"
ONE=BASE/"apex-integration-001"
TWO=BASE/"apex-integration-002"
REVIEW=BASE/"apex-integration-review"
DEST=ROOT/"docs/evidence/wang2017-soil2-2026-10-24/apex-integration"


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
        for item in records:
            data=tar.extractfile(item["path"]).read()
            assert len(data)==item["bytes"] and hashlib.sha256(data).hexdigest()==item["sha256"]
    return records


def copy(source,destination):
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,destination)
    assert sha(source)==sha(destination)


def rows(path):
    with path.open(encoding="utf-8-sig",newline="") as stream:
        return sum(1 for _ in csv.DictReader(stream))


def frozen_proof(run):
    before,after=read(run/"source-proof-before.json"),read(run/"source-proof-after.json")
    assert before==after
    assert all(sha(run/entry["path"])==entry["sha256"] for entry in before["files"])
    provenance=read(run/"source-provenance.json")
    assert provenance["sourceSnapshotExactLoadedBytes"] and provenance["copiedByteEqualityBeforeLoad"]
    assert provenance["nativeBackend"]["verifiedBy"]=="GetModuleHandleW/GetModuleFileNameW"
    return {"path":run.relative_to(BASE).as_posix(),"verifiedFrozenFiles":len(before["files"]),
            "beforeAfterProofEqual":True,"selectedAsdfLoadedBytesVerified":True,
            "mappedCopiedBackend":provenance["nativeBackend"],
            "scope":"Own selected native/output process snapshot; this does not retrospectively freeze separate workspace regression runs"}


def main():
    input_status=read(ONE/"input-status.json")
    regression=read(ONE/"regression-status.json")
    resumed=read(TWO/"status.json")
    assert input_status["status"]=="PASS" and input_status["inputExitCode"]==0
    assert read(ONE/"apex-inputs.json")["controlsCount"]==3 and read(ONE/"apex-inputs.json")["passed"]
    assert regression["status"]=="FAILED"
    assert [(row["name"],row["exitCode"]) for row in regression["tests"]]==[
        ("strict-point",0),("old-mc",0),("framework",0),("strict-native",0),("strict-inputs",0),("strict-output",1)]
    guard=ONE/"strict-output strict"
    assert [p.name for p in guard.iterdir()]==["WRAPPER_ARGUMENT_GUARD.txt"]
    assert "stop before MPM output test" in (guard/"WRAPPER_ARGUMENT_GUARD.txt").read_text()
    assert "Control output already contains files" in (ONE/"strict-output.log").read_text(encoding="utf-8-sig")
    assert read(ONE/"strict-point.json")["passed"] and read(ONE/"strict-point.json")["controlsCount"]==19
    native=read(ONE/"strict-native/result.json")
    assert native["passed"] and native["controlsCount"]==18 and native["physicalUpdatesExecuted"]==0
    assert read(ONE/"strict-inputs.json")["passed"] and read(ONE/"strict-inputs.json")["controlsCount"]==3
    assert "34 passed; 0 failed" in (ONE/"old-mc.log").read_text(encoding="utf-8-sig")
    assert "10 passed, 0 failed" in (ONE/"framework.log").read_text(encoding="utf-8-sig")
    assert resumed["status"]=="PASS" and len(resumed["tests"])==2
    outputs=[]
    for entry in resumed["tests"]:
        variant=entry["variant"]
        assert variant in ("strict","composite-apex") and entry["exitCode"]==0
        assert len(entry["arguments"])==3 and entry["arguments"][-1]==variant
        run=TWO/variant;result=read(run/"result.json")
        assert result["passed"] and result["materialVariant"]==variant
        assert (result["passedCount"],result["failedCount"],result["notRunCount"])==(8,0,0)
        assert result["physicalUpdatesExecuted"]==2 and result["actualSavedStates"]==2
        vtk=sorted((run/"observations/vtk").glob("particles_*.vtk"))
        material_rows=rows(run/"observations/wang2017-material-history.csv")
        contact_rows=rows(run/"observations/wang2017-contact-history.csv")
        assert len(vtk)==2 and material_rows==50 and contact_rows==4
        outputs.append({"variant":variant,"exitCode":0,"passedCount":8,"failedCount":0,"notRunCount":0,
                        "actualMpmUpdates":2,"observedVtkFiles":len(vtk),"observedMaterialCsvRows":material_rows,
                        "observedContactCsvRows":contact_rows,"actualParticleCount":result["observations"]["particleCount"],
                        "assertedArgumentArray":entry["arguments"]})
    comparison=read(TWO/"strict-output-byte-comparison.json")
    assert len(comparison)==4
    for entry in comparison:
        before=BASE/"output-controls-002/observations"/entry["file"]
        after=TWO/"strict/observations"/entry["file"]
        assert entry["byteIdentical"] and sha(before)==entry["beforeSha256"]==sha(after)==entry["afterSha256"]
        assert before.read_bytes()==after.read_bytes()
    proofs=[frozen_proof(run) for run in (ONE/"strict-native",TWO/"strict",TWO/"composite-apex")]
    assert (ONE/"strict-native-executed-test.lisp").read_bytes()==(ONE/"strict-native/source/case.lisp").read_bytes()
    total_updates=sum(entry["actualMpmUpdates"] for entry in outputs)
    assert total_updates==4
    summary={
        "scope":"Existing native regression and bounded output gates only; no tests, constitutive replays or solvers were rerun during collection",
        "scientificValidation":False,"fullSlopeExecutedInTheseAttempts":False,
        "initialApexInputGate":{"status":"PASS","groups":3,"exitCode":0,"physicalUpdates":0,
                               "sourceScope":"Separate workspace input process; not claimed as a frozen native/output load"},
        "attempt001":{"originalStatus":"FAILED","completedRegressionGates":[
            {"name":"strict-point","groups":19,"exitCode":0,"sourceScope":"Workspace load with retained executed test; not full source freeze"},
            {"name":"old-mc","groups":34,"exitCode":0,"sourceScope":"Workspace load with retained executed test; not full source freeze"},
            {"name":"framework","groups":10,"exitCode":0,"sourceScope":"Workspace load with retained executed test; not full source freeze"},
            {"name":"strict-native","groups":18,"exitCode":0,"sourceScope":"Own frozen process, zero MPM updates"},
            {"name":"strict-inputs","groups":3,"exitCode":0,"sourceScope":"Workspace load with retained executed test; not full source freeze"}],
            "stoppedGate":"strict-output","stoppedExitCode":1,"stoppedMpmUpdates":0,
            "stopClassification":"OPERATOR_ARGUMENT_GUARD / HARNESS_FAILURE",
            "reason":"Original PowerShell wrapper combined output path and variant into one argument. An operator guard file deliberately caused the fresh-output check to reject before snapshot/material/MPM execution. Original FAILED status, wrapper, raw error and guard are preserved.",
            "apexOutputGate":"NOT_RUN in001"},
        "attempt002":{"status":"PASS","scope":"Resume only two missing output gates with corrected explicit3-element argument arrays",
                      "outputs":outputs,"noCompletedRegressionRepeated":True},
        "totalActualMpmUpdatesAcrossStage":total_updates,"frozenProcessProofs":proofs,
        "strictOutputBeforeAfterByteIdentity":{"matchedFiles":4,"comparison":comparison,
             "beforeReference":"Retained old output-controls-002 observations and docs/evidence/wang2017-soil2-2026-10-24/output-controls/attempt-002-native-artifacts.tar.gz"},
        "limitations":["Microgeometry output gates do not establish activation of the new apex branch, plastic-path validity or full-slope completion",
                       "Separate apex material-point evidence owns the extension's numerical checks; it is not repeated here",
                       "Explicit volumetric apex is a new constitutive convention, not silent repair of strict zero-dilation Soil2",
                       "No paper agreement, rate/mesh/timestep convergence or landslide PASS"]}
    (REVIEW/"integration-evidence-review.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    DEST.parent.mkdir(parents=True,exist_ok=True);DEST.mkdir(exist_ok=False)
    (DEST/".gitattributes").write_text("* -text -whitespace\n*.gz binary\n",encoding="utf-8")
    archive_records={}
    for number,run in ((1,ONE),(2,TWO)):
        name=f"attempt-{number:03d}-raw-artifacts.tar.gz"
        archive_records[name]=archive(DEST/name,[(p.relative_to(run).as_posix(),p) for p in run.rglob("*")
            if p.is_file() and "source" not in p.relative_to(run).parts and ".native-cache" not in p.parts])
    source_files=[]
    for label,run in (("attempt001/strict-native",ONE/"strict-native"),("attempt002/strict",TWO/"strict"),("attempt002/composite-apex",TWO/"composite-apex")):
        source=run/"source"
        source_files.extend((label+"/"+p.relative_to(source).as_posix(),p) for p in source.rglob("*")
                            if p.is_file() and ".native-cache" not in p.parts)
    archive_records["frozen-process-sources.tar.gz"]=archive(DEST/"frozen-process-sources.tar.gz",source_files)
    direct=[(ONE/"input-status.json","attempt001/input-status.json"),
            (ONE/"apex-inputs.json","attempt001/apex-inputs.json"),
            (ONE/"regression-status.json","attempt001/regression-status.json"),
            (ONE/"run-apex-regressions-at-start.ps1","attempt001/executed-wrapper.ps1"),
            (guard/"WRAPPER_ARGUMENT_GUARD.txt","attempt001/WRAPPER_ARGUMENT_GUARD.txt"),
            (TWO/"status.json","attempt002/status.json"),(TWO/"executed-wrapper.ps1","attempt002/executed-wrapper.ps1"),
            (TWO/"strict-output-byte-comparison.json","attempt002/strict-output-byte-comparison.json"),
            (TWO/"strict/result.json","attempt002/strict-result.json"),
            (TWO/"composite-apex/result.json","attempt002/composite-apex-result.json")]
    for source,name in direct:copy(source,DEST/name)
    for path in REVIEW.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:copy(path,DEST/"review"/path.relative_to(REVIEW))
    (DEST/"archive-input-manifest.json").write_text(json.dumps(archive_records,indent=2)+"\n",encoding="utf-8")
    (DEST/"README.md").write_text(
        "# Apex-stage native integration evidence\n\n"
        "Collection only: no test, replay or solver was rerun to create this packet. Initial apex input configuration gate passed3 groups, exit0. "
        "Attempt001 then completed strict point19, old MC34, framework10, strict native18 and strict input3 groups with exit0. Its original final status remains FAILED: a malformed PowerShell argument expression combined output path and variant. "
        "An operator guard deliberately made the fresh-output check reject before the mistaken output run could create a snapshot or perform any MPM update. The original executed wrapper, guard, raw error and FAILED status are retained. Apex output was NOT_RUN in001. This is a harness stop, not a constitutive/physics failure.\n\n"
        "Attempt002 resumed only the two missing output gates with explicit three-element argument arrays. Strict and composite-apex each passed8 groups, exit0, with exactly2 actual MPM updates,25 MPs,2 observed VTK states,50 material CSV rows and4 contact CSV rows. "
        "The result material variant/count assertions match each invocation; total actual MPM updates across this stage are4. Four strict output files (2 VTK and material/contact CSV) are byte-identical to the retained old output-controls-002 baseline, checked against the actual files and recorded hashes.\n\n"
        "Source scope is explicit: workspace point/MC/framework/input runs have logs and available executed test copies, but are not called fully frozen. The strict-native process and both output processes each own275 before/after matching source records, private compilation snapshots and Windows-verified mapped copied DLLs. "
        "All three frozen source trees and their runtime proofs are retained; private compiled caches/FASLs are explicitly excluded from the archive. Their proof does not retrospectively freeze the other workspace runs.\n\n"
        "Every archive was reopened and all member lengths/SHA-256 checked against its input; copied files and the final artifact index were also verified. This packet does not establish a full slope, activation of the apex branch in the elastic microcase, laboratory/paper agreement, mesh/rate/timestep convergence or landslide validation. "
        "The volumetric apex option is an explicit new constitutive convention; strict defaults and negative evidence remain separate.\n",encoding="utf-8")
    entries=[{"path":p.relative_to(DEST).as_posix(),"bytes":p.stat().st_size,"sha256":sha(p)}
             for p in sorted(DEST.rglob("*")) if p.is_file()]
    (DEST/"evidence-manifest.json").write_text(json.dumps({"scope":"Bounded native integration; original harness failure retained; no scientific validation", "entries":entries},indent=2)+"\n",encoding="utf-8")
    assert all(sha(DEST/item["path"])==item["sha256"] for item in entries)
    print(json.dumps({"verifiedArtifacts":len(entries),"archiveMembers":{name:len(records) for name,records in archive_records.items()},
                      "actualMpmUpdates":total_updates,"strictFilesByteIdentical":4,"destination":str(DEST)}))


if __name__=="__main__":main()
