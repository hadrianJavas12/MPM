"""Pack completed VM evidence and separately retain user-cancelled partial Joss."""
import hashlib,importlib.util,json
from pathlib import Path
R=Path('D:/MPM');B=R/'output/architecture-migration-2026-10-16/p1-full'
D=R/'docs/evidence/architecture-migration-2026-10-16/p1-full'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
names=('triaxial-2d','triaxial-3d')
status={n:read(B/(n+'-status.json')) for n in names}
comparisons={n:read(B/(n+'-comparison.json')) for n in names}
for n in names:
    assert all(status[n].get(k)==0 for k in ('nativeExitCode','comparisonExitCode','auditExitCode'))
    assert read(B/n/'manifest.json')['complete'] is True
    assert comparisons[n]['passed'] is True
    assert read(B/n/'audit.json')['passed_consistency_checks'] is True
cancel=read(B/'joss-serial-status.json')
assert cancel['status']=='STOPPED_BY_USER' and cancel['nativeExitCode'] is None
assert not D.exists(),'Do not overwrite prior evidence'
spec=importlib.util.spec_from_file_location('evidence',R/'docs/evidence/architecture-migration-2026-10-16/p1/sources/pack-framework-evidence.py')
lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)
lib.DEST=D;lib.rows=[];D.mkdir(parents=True)
lib.put_bytes('.gitattributes',b'* -text -whitespace\n*.gz binary\n')
results={n:lib.run_evidence(n,B/n) for n in names}
for n in names:lib.zipped_file('comparisons/'+n+'.json.gz',B/(n+'-comparison.json'))
for p in sorted(B.iterdir()):
    if p.is_file() and p.suffix=='.log':lib.zipped_file('logs/'+p.name+'.gz',p)
    elif p.is_file() and p.suffix in ('.ps1','.json','.txt'):lib.put_file('control/'+p.name,p)
lib.archive('sources/executed-full-source.tar.gz',[(n+'/'+p.relative_to(B/n/'source').as_posix(),p)
    for n in (*names,'joss-serial') for p in (B/n/'source').rglob('*') if p.is_file()])
lib.archive('joss-cancelled/partial-output.tar.gz',[(p.relative_to(B/'joss-serial').as_posix(),p)
    for p in (B/'joss-serial').rglob('*') if p.is_file() and 'source' not in p.relative_to(B/'joss-serial').parts])
lib.put_file('sources/finish-p1-vm.py',Path(__file__))
lib.put_file('sources/evidence-library.py',R/'docs/evidence/architecture-migration-2026-10-16/p1/sources/pack-framework-evidence.py')
lib.put_json('summary.json',{'executedSourceCommit':'62adb5013e6379ae1d970e4ad334fc92cc5ef912',
 'completedVmStrictComparisonsAndAuditsPass':True,'runs':results,'jossStatus':'STOPPED_BY_USER',
 'jossComplete':False,'jossLastObservedTimeS':4.2,'jossNativeExitCode':None,'fullG3':'PARTIAL',
 'scientificValidation':False,'scope':'Completed P1 VM regression only; cancelled Joss retained without PASS/FAIL claim'})
lib.put_bytes('README.md',b'# P1 full VM regression and cancelled Joss\n\nFrozen source 62adb50. Both VM controls completed with native/comparison/audit exit 0.\nJoss was stopped by the user at 4.2 s; partial raw output is retained. No complete\nJoss comparison or full architecture/scientific acceptance is claimed.\n')
(D/'manifest.json').write_text(json.dumps({'entries':lib.rows},indent=2)+'\n')
assert all(hashlib.sha256((D/r['path']).read_bytes()).hexdigest()==r['sha256'] for r in lib.rows)
print(json.dumps({'verifiedArtifacts':len(lib.rows),'completedVmPass':True,'fullG3':'PARTIAL'}))
