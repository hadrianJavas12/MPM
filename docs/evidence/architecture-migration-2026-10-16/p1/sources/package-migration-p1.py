"""Retain actual bounded P1 evidence, including initial failed test fixtures."""
import hashlib,importlib.util,json,re
from pathlib import Path
R=Path('D:/MPM');B=R/'output/architecture-migration-2026-10-16/p1'
D=R/'docs/evidence/architecture-migration-2026-10-16/p1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def log(p):
    b=p.read_bytes();return b.decode('utf-16' if b.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig')
def result(name,pattern):
    m=re.search(pattern,log(B/name));assert m,(name,pattern);return int(m[1])
checks={
 'framework':result('framework-components.log',r'CHECKS:\s*(\d+) passed, 0 failed'),
 'configuration':result('config-contracts.log',r'CONTRACTS:\s*(\d+) passed'),
 'material':result('material-diagnostics.log',r'CONTRACTS:\s*(\d+) passed'),
 'node':result('node-tests.log',r'pass\s+(\d+)'),
 'ownershipNormal':result('ownership-normal-002.log',r'\(normal\):\s*(\d+) passed, 0 failed'),
 'ownershipLegacy':result('ownership-legacy-001.log',r'\(legacy\):\s*(\d+) passed, 0 failed'),
 'snapshot':result('snapshot-contract-002.log',r'CONTRACTS:\s*(\d+) passed')}
assert result('node-tests.log',r'fail\s+(\d+)')==0 and result('node-tests.log',r'skipped\s+(\d+)')==0
comparisons={s:read(B/(s+'-comparison.json')) for s in ('triaxial-short','mc-triaxial')}
assert all(v['passed'] for v in comparisons.values())
ns={};exec((R/'.tmp/migrate-p1.py').read_text().split('if B.exists():')[0],ns)
def named_forms(p):
    out={}
    for form in ns['forms'](p.read_bytes().decode('utf8')):
        m=re.match(r'\((\S+)\s+([^\s()]+)',form)
        if m and m[1]!='in-package':
            assert m[2] not in out;out[m[2]]=form.encode('utf8')
    return out
before=R/'output/architecture-migration-2026-10-16/p1-source-before'
original=named_forms(before/'framework/components/specifications.lisp')
targets={};form_hashes=[]
for relative in ('src/simulation/components/base.lisp','materials/core/definition.lisp','src/simulation/components/specifications.lisp'):
    for name,data in named_forms(R/relative).items():
        assert name not in targets and data==original[name]
        targets[name]=data;form_hashes.append({'name':name,'target':relative,'beforeSha256':hashlib.sha256(original[name]).hexdigest(),'afterSha256':hashlib.sha256(data).hexdigest()})
assert targets==original
assert (R/'materials/adapters/native.lisp').read_bytes()==(before/'framework/components/materials.lisp').read_bytes()
old_cliff=R/'output/framework-refactor-2026-10-15/current-head-cliff-mc'
new_cliff=B/'cliff-mc'
vtk_before={p.relative_to(old_cliff).as_posix():sha(p) for p in old_cliff.rglob('*.vtk')}
vtk_after={p.relative_to(new_cliff).as_posix():sha(p) for p in new_cliff.rglob('*.vtk')}
assert vtk_before and vtk_before==vtk_after
spec=importlib.util.spec_from_file_location('evidence',R/'.tmp/pack-framework-evidence.py')
lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)
lib.DEST=D;lib.rows=[];D.mkdir(parents=True,exist_ok=True)
lib.put_bytes('.gitattributes',b'* -text -whitespace\n*.gz binary\n')
for p in sorted(B.glob('*.log')):lib.zipped_file('logs/'+p.name+'.gz',p)
for name in ('triaxial-short','mc-triaxial'):
    lib.zipped_file('comparisons/'+name+'.json.gz',B/(name+'-comparison.json'))
    lib.archive('runs/'+name+'.tar.gz',[(p.relative_to(B/name).as_posix(),p) for p in (B/name).rglob('*') if p.is_file()])
lib.archive('runs/cliff-mc.tar.gz',[(p.relative_to(new_cliff).as_posix(),p) for p in new_cliff.rglob('*') if p.is_file()])
lib.archive('sources/before-contracts.tar.gz',[(p.relative_to(before).as_posix(),p) for p in before.rglob('*') if p.is_file()])
for relative in ('tests/material-ownership-compat.lisp','tests/case-snapshot-contracts.lisp',
                 '.tmp/p1-original-cpl-control.lisp','.tmp/migrate-p1.py','.tmp/package-migration-p1.py',
                 '.tmp/pack-framework-evidence.py','docs/architecture/MIGRATION_APPROVALS.json'):
    lib.put_file('sources/'+Path(relative).name,R/relative)
lib.put_json('source-extraction.json',{'formCount':len(form_hashes),'allFormBytesIdentical':True,
 'nativeAdapterFileBytesIdentical':True,'forms':form_hashes})
lib.put_json('cliff-mc-vtk-identity.json',{'allVtkByteIdentical':True,'vtkFiles':vtk_after,
 'baseline':'0fece3b native MC cliff bounded control','plotWarning': 'Plotting disabled' in log(B/'cliff-mc.log'),
 'plotStatus':'NOT_GENERATED' if 'Plotting disabled' in log(B/'cliff-mc.log') else 'INSPECT_REQUIRED'})
summary={'productionImplementationCommit':'3cd172e','scope':'Bounded current-code Windows native contracts and CLI controls; full G3 pending',
 'checks':checks,'strictBoundedRegressions':{k:{f:v.get(f) for f in ('passed','baseline_states','candidate_states','max_position_difference_m')} for k,v in comparisons.items()},
 'cliffMcVtkExact':True,'sourceFormsExact':True,
 'initialFailuresRetained':[
  'ownership-normal.log: test incorrectly omitted SBCL SLOT-OBJECT; old-source control confirms it; only test assertion corrected',
  'snapshot-contract-001.log: negative fixture still preferred frozen registry; fixture registry corrected, guard unchanged'],
 'plotWarningRetained':'cliff MC gnuplot PNG unavailable; numerical VTK hashes match exactly',
 'nativeEngineNumericalChanges':False,'newMcEvolutionInstalled':False,'scientificValidation':False,
 'fullG3':'NOT_RUN at bounded checkpoint','P1Acceptance':'PROVISIONAL','G1':'PARTIAL',
 'unitProvenance':'Units loaded committed production code from working tree, not pre-load frozen unit sources; full executed CLI source copies retained in run archives',
 'transitiveNativeDependencyProvenanceComplete':False}
lib.put_json('summary.json',summary)
(D/'manifest.json').write_text(json.dumps({'entries':lib.rows},indent=2)+'\n',encoding='utf8')
assert all(sha(D/r['path'])==r['sha256'] for r in lib.rows)
print(json.dumps({'evidence':str(D),'verifiedArtifacts':len(lib.rows),'checks':checks,
 'boundedStrict':summary['strictBoundedRegressions'],'cliffVtkFiles':len(vtk_after)},indent=2))
