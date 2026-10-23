import hashlib,json,shutil,tarfile,io,gzip
from pathlib import Path
root=Path.cwd(); out=root/'output/wang2017-reference-2026-10-24'; dest=root/'docs/evidence/wang2017-reference-2026-10-24/fast-010-preparation'
dest.mkdir(exist_ok=False)
(dest/'.gitattributes').write_text('* -text -whitespace\n*.gz binary\n',encoding='utf8')
files=[]
for attempt in ('fast-010-inputs-001','fast-010-inputs-002'):
    for p in sorted((out/attempt).rglob('*')):
        if p.is_file():files.append((p.relative_to(out).as_posix(),p))
with (dest/'native-input-controls.tar.gz').open('wb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as gz,tarfile.open(fileobj=gz,mode='w') as tar:
    for rel,p in files:
        b=p.read_bytes();info=tarfile.TarInfo(rel);info.size=len(b);info.mtime=0;tar.addfile(info,io.BytesIO(b))
with tarfile.open(dest/'native-input-controls.tar.gz','r:gz') as tar:
    for rel,p in files:assert tar.extractfile(rel).read()==p.read_bytes(),rel
for a,b in [('executed-test.lisp','tests/benchmarks/wang2017-fast-010-inputs.lisp'),('trial-case.lisp','cases/benchmarks/wang2017-soil1-fast-010.lisp'),('reference-case.lisp','cases/benchmarks/wang2017-soil1.lisp')]:
    assert (out/'fast-010-inputs-002'/a).read_bytes()==(root/b).read_bytes(),b
video=out/'friend-fem-video'
for name in ['probe.json','frame-start.png','frame-middle.png','frame-end.png']:
    shutil.copyfile(video/name,dest/name)
rawvideo=root/'wiki-vault/raw/assets/wang2017-friend-fem-2026-10-24.mp4'
summary={'status':'INPUT_GATE_PASS_NOT_SOLVER_COMPLETE','nativeControlGroups':3,'nativeExit':0,'physicalUpdates':0,'twoNativeMaterialParticles':True,'activeSourceCommit':'4e3140cf49659707e3e71ba5eb5d3bd8c2bbf896','approvedVelocityMPerS':.01,'approvedTravelM':.06,'approvedDurationS':6,'paperRateMultiplier':100,'userConfirmedTravelRatherThan600s':True,'arithmeticFixtureFailureRetained':{'attempt':'001','cause':'exact equality .060000000000000005 vs .06','fixedArithmeticUnitToleranceM':1e-15,'numericSolverTolerancesChanged':False},'preflightProvenance':'Executed test and cases copied before002 and match workspace after; full framework/runtime not independently frozen by preflight. Actual MPM run separately freezes all first-party sources/DLL.','friendVideoRepositoryPath':rawvideo.relative_to(root).as_posix(),'friendVideoSha256':hashlib.sha256(rawvideo.read_bytes()).hexdigest(),'friendVideoScope':'Qualitative mesh deformation only; no verified material/time/deformation scale','scientificValidation':False,'archiveMembersVerified':len(files)}
(dest/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
(dest/'README.md').write_text('# Wang fast010 input preparation\n\nUser confirmed0.01m/s to60mm/6physicalseconds,100x paper rate. Three native input controls PASS with zero MPM updates; this is not a completed slope or quantitative paper match. Initial exact-floating-equality fixture failure is retained separately from final002PASS; no material/regression tolerances changed. All input archive members were reopened and byte-matched. Test/cases before002 equal current source; preflight did not freeze the full dependency runtime. Actual native run source4e3140c has separate full source/DLL freezing.\n\nFriend FEM clip is preserved once in wiki-vault/raw/assets/wang2017-friend-fem-2026-10-24.mp4 (SHA in summary). Video playback11.133seconds is not FEM physical time. Representative frames show localization but do not establish material parameters or deformation scale.\n',encoding='utf8')
recipe=out/'fast-010-preparation-support/pack.py';shutil.copyfile(recipe,dest/'pack.py')
entries=[{'path':p.relative_to(dest).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(dest.rglob('*')) if p.is_file()]
(dest/'evidence-manifest.json').write_text(json.dumps({'entries':entries},indent=2)+'\n',encoding='utf8')
for e in entries:assert hashlib.sha256((dest/e['path']).read_bytes()).hexdigest()==e['sha256']
print(json.dumps({'verifiedArtifactHashes':len(entries),'archiveMembers':len(files),'destination':str(dest)}))
