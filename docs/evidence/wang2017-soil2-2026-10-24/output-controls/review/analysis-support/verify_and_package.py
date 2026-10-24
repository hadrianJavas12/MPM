"""Archive two genuine native output-control attempts and retain the harness failure."""
from pathlib import Path
import gzip
import hashlib
import io
import json
import shutil
import tarfile
import numpy as np
from vtk_reader import vtk

ROOT=Path(__file__).resolve().parents[4]
BASE=ROOT/"output/wang2017-soil2-2026-10-24"
REVIEW=BASE/"output-controls-review"
DEST=ROOT/"docs/evidence/wang2017-soil2-2026-10-24/output-controls"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def archive(path, files):
    records=[]
    with path.open("wb") as raw,gzip.GzipFile(fileobj=raw,mode="wb",mtime=0,filename="") as zipped:
        with tarfile.open(fileobj=zipped,mode="w") as tar:
            for name,source in sorted(files):
                data=source.read_bytes()
                info=tarfile.TarInfo(name)
                info.size,info.mtime=len(data),0
                tar.addfile(info,io.BytesIO(data))
                records.append({"path":name,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()})
    with tarfile.open(path,"r:gz") as tar:
        assert len(tar.getmembers())==len(records)
        for item in records:
            data=tar.extractfile(item["path"]).read()
            assert len(data)==item["bytes"] and hashlib.sha256(data).hexdigest()==item["sha256"]
    return records


def main():
    summaries=[]
    for number in (1,2):
        run=BASE/f"output-controls-{number:03d}"
        result=read(run/"result.json")
        expected=(False,6,1,1) if number==1 else (True,8,0,0)
        assert tuple(result[k] for k in ("passed","passedCount","failedCount","notRunCount"))==expected
        assert result["physicalUpdatesExecuted"]==2
        before=read(run/"source-proof-before.json")["files"]
        after=read(run/"source-proof-after.json")["files"]
        assert before==after
        assert all(sha(run/item["path"])==item["sha256"] for item in before)
        provenance=read(run/"source-provenance.json")
        assert provenance["sourceSnapshotExactLoadedBytes"] is True
        assert provenance["nativeBackend"]["verifiedBy"]=="GetModuleHandleW/GetModuleFileNameW"
        files=sorted((run/"observations/vtk").glob("particles_*.vtk"))
        assert len(files)==2
        states=[vtk(file) for file in files]
        first,last=states[0],states[1]
        assert len(first[0])==len(last[0])==25
        assert np.array_equal(first[1]["unique-id"],last[1]["unique-id"])
        assert (last[1]["mass"]>0).all() and (last[1]["volume"]>0).all()
        assert (last[1]["wang-det-f"]>0).all()
        assert np.array_equal(first[1]["mass"],last[1]["mass"])
        assert "wang-paper-kps" in last[1] and "mc-kappa" not in last[1]
        displacement=np.linalg.norm(last[0]-first[0],axis=1)
        assert displacement.max()>0
        summary={"attempt":run.name,"observedNativeLauncherExitCode":1 if number==1 else 0,
                 "exitObservation":"Windows launcher LASTEXITCODE propagated by the command wrapper; native test result/logs separately retained",
                 "nativeResult":result,"frozenSourcesMatchedBeforeAfter":len(before),
                 "mappedCopiedBackendSha256":provenance["nativeBackend"]["sha256"],
                 "vtkStates":len(files),"nativeParticleCount":len(first[0]),
                 "nativeIdsStable":True,"allReadVtkFieldsFinite":True,
                 "positiveMassVolumeAndActualJ":True,"perParticleMassExactlyUnchanged":True,
                 "massKgPerM":float(last[1]["mass"].sum()),
                 "maxSavedPositionDistanceM":float(displacement.max()),
                 "lastPaperKpsRange":[float(last[1]["wang-paper-kps"].min()),float(last[1]["wang-paper-kps"].max())],
                 "vtkHashes":[{"path":file.relative_to(run).as_posix(),"sha256":sha(file)} for file in files]}
        summaries.append(summary)
    production_differences=[]
    one,two=[BASE/f"output-controls-{i:03d}" for i in (1,2)]
    a={x["path"]:x["sha256"] for x in read(one/"source/source-manifest.json")["files"]}
    b={x["path"]:x["sha256"] for x in read(two/"source/source-manifest.json")["files"]}
    production_differences=[key for key in sorted(set(a)|set(b)) if a.get(key)!=b.get(key)]
    assert production_differences==["source/case.lisp"]
    review={"scope":"Actual Windows native microgeometry/output integration; not gravity equilibrium, plastic-flow validation or landslide/paper calibration",
            "scientificValidation":False,"passedFinalControlGroups":8,"failedFinalControlGroups":0,
            "attempts":summaries,"frozenSourceDifferencesBetweenAttempts":production_differences,
            "harnessRepair":"Soil1 comparison fixture now declares its mandatory strain assumption; final source reports observed saved VTK count separately from intended count. No production change.",
            "totalActualMpmUpdatesAcrossAttempts":4,"finalAttemptActualMpmUpdates":2,
            "acceptedIntegrationScope":"Two real USF updates, two native particle states, full actual F/J/Ep/R/cohesion/contact CSV reconstruction, read-only diagnostics and legacy Soil1 filesystem no-op",
            "plasticEvolutionScope":"Microcase remains elastic (paper kps0); existing separately retained material-point tests own plastic-path verification"}
    REVIEW.mkdir(exist_ok=True)
    (REVIEW/"native-output-review.json").write_text(json.dumps(review,indent=2)+"\n",encoding="utf-8")
    DEST.parent.mkdir(parents=True,exist_ok=True)
    DEST.mkdir(exist_ok=False)
    (DEST/".gitattributes").write_text("* -text -whitespace\n*.gz binary\n",encoding="utf-8")
    archive_records={}
    for number in (1,2):
        run=BASE/f"output-controls-{number:03d}"
        label=f"attempt-{number:03d}"
        source=run/"source"
        archive_records[label+"-executed-source.tar.gz"]=archive(DEST/(label+"-executed-source.tar.gz"),
          [(p.relative_to(source).as_posix(),p) for p in source.rglob("*") if p.is_file() and ".native-cache" not in p.parts])
        archive_records[label+"-native-artifacts.tar.gz"]=archive(DEST/(label+"-native-artifacts.tar.gz"),
          [(p.relative_to(run).as_posix(),p) for p in run.rglob("*") if p.is_file() and "source" not in p.relative_to(run).parts])
        for name in ("result.json","source-proof-before.json","source-proof-after.json","source-provenance-before.json","source-provenance.json"):
            shutil.copyfile(run/name,DEST/(label+"-"+name))
        shutil.copyfile(BASE/(run.name+"-native.log"),DEST/(label+"-native.log"))
    for path in REVIEW.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            target=DEST/"review"/path.relative_to(REVIEW)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(path,target)
            assert sha(path)==sha(target)
    (DEST/"archive-input-manifest.json").write_text(json.dumps(archive_records,indent=2)+"\n",encoding="utf-8")
    (DEST/"README.md").write_text(
      "# Native Soil2/output integration evidence\n\n"
      "Final frozen attempt002:8 groups PASS,0 FAIL,0 NOT_RUN, Windows launcher exit0. Exactly2 genuine native USF updates on25 MPs in a declared4m-wide microgeometry; two actual VTK states,50 material-history CSV rows and4 contact-history rows. "
      "The microcase applies gravity and the same fixed Soil2 law but does not perform gravity equilibration or a full paper slope run. It remains elastic; plastic material paths are covered by the separately retained point controls.\n\n"
      "Attempt001 exit1 is retained: six groups passed, two real updates and both states were already written; the legacy Soil1 no-op fixture lacked its required strain-coordinate declaration. The seventh group failed and the eighth was NOT_RUN. "
      "Only the test source differs between attempts: the fixture declaration, truthful observed-state reporting and independent group scopes were repaired. No production or numerical source was changed. Four actual updates were performed across both attempts, two per attempt.\n\n"
      "Native CSV readback reconstructs det(F), the physical-shear Ep invariant, Soil2 cohesion, proper R, surface/centre geometry and geometric spring energy. Output/native-reader accesses preserve current and committed constitutive/kinematic snapshots. "
      "The last group checks duplicate-frame, mixed-material and corrupted audit-input rejection; these declared negative fixtures are not physical run states. Soil1 produces no additional audit files. "
      "Archives were reopened and every member length/SHA-256 verified against its input; exact pre-load source/DLL and before/after provenance are retained, excluding private compiled caches. "
      "No landslide, closed energy balance, scientific validation or paper equivalence is claimed.\n",encoding="utf-8")
    entries=[{"path":p.relative_to(DEST).as_posix(),"bytes":p.stat().st_size,"sha256":sha(p)}
             for p in sorted(DEST.rglob("*")) if p.is_file()]
    (DEST/"evidence-manifest.json").write_text(json.dumps({"entries":entries},indent=2)+"\n",encoding="utf-8")
    assert all(sha(DEST/item["path"])==item["sha256"] for item in entries)
    print(json.dumps({"verifiedArtifacts":len(entries),"archiveMembers":{name:len(records) for name,records in archive_records.items()},"finalVtkStates":2,"finalActualMpmUpdates":2,"destination":str(DEST)}))


if __name__=="__main__":
    main()
