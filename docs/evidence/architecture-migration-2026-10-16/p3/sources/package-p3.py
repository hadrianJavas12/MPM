"""Collect completed focused checks; no solver or comparison rerun."""
import hashlib,importlib.util,json,re
from pathlib import Path
R=Path('D:/MPM');B=R/'output/architecture-migration-2026-10-16/p3'
D=R/'docs/evidence/architecture-migration-2026-10-16/p3'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
status=read(B/'status.json')
assert status['status']=='PASS' and status['sourceUnchangedDuringChecks'] is True
assert len(status['checks'])==13 and all(c['exitCode']==0 for c in status['checks'].values())
assert not D.exists(),'Do not overwrite evidence'
comparisons={n:read(B/(n+'-comparison.json')) for n in ('triaxial-short','mc-triaxial')}
assert all(c['passed'] is True for c in comparisons.values())
vtk_identity={}
for n in comparisons:
    files=lambda root:{p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*.vtk')}
    before=files(B.parent/'p1'/n);after=files(B/n)
    vtk_identity[n]={'count':len(after),'byteIdentical':bool(before) and before==after}
    assert vtk_identity[n]['byteIdentical']
proof=read(B.parent/'p3-extraction-form-hashes.json')
for p,h in proof['targets'].items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==h
spec=importlib.util.spec_from_file_location('evidence',R/'docs/evidence/architecture-migration-2026-10-16/p1/sources/pack-framework-evidence.py')
lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)
lib.DEST=D;lib.rows=[];D.mkdir(parents=True)
lib.put_bytes('.gitattributes',b'* -text -whitespace\n*.gz binary\n')
results={n:lib.run_evidence(n,B/n) for n in comparisons}
for p in B.iterdir():
    if p.is_file() and p.suffix=='.log':lib.zipped_file('logs/'+p.name+'.gz',p)
    elif p.is_file() and p.suffix=='.json':lib.put_file('control/'+p.name,p)
lib.zipped_file('before/diagnostics.lisp.gz',B.parent/'p3-source-before/framework/components/diagnostics.lisp')
lib.put_file('source-extraction.json',B.parent/'p3-extraction-form-hashes.json')
lib.archive('sources/frozen-cli-source.tar.gz',[(p.relative_to(B/'triaxial-short/source').as_posix(),p)
    for p in (B/'triaxial-short/source').rglob('*') if p.is_file()])
lib.archive('sources/tested-source.tar.gz',[(p,R/p) for p in status['sourceSha256']])
for p in ('validate-p3.py','package-p3.py'):lib.put_file('sources/'+p,R/'.tmp'/p)
lib.put_file('sources/evidence-library.py',R/'docs/evidence/architecture-migration-2026-10-16/p1/sources/pack-framework-evidence.py')
counts={}
for name,pattern in {'framework-components':r'CHECKS:\s*(\d+) passed, 0 failed','config-contracts':r'CONTRACTS:\s*(\d+) passed',
 'material-diagnostics':r'CONTRACTS:\s*(\d+) passed','diagnostics-normal':r'\(normal\):\s*(\d+) passed',
 'diagnostics-legacy':r'\(legacy\):\s*(\d+) passed','ownership-normal':r'\(normal\):\s*(\d+) passed, 0 failed',
 'ownership-legacy':r'\(legacy\):\s*(\d+) passed, 0 failed','snapshot-contract':r'CONTRACTS:\s*(\d+) passed',
 'node-tests':r'\bpass\s+(\d+)'}.items():
    raw=(B/(name+'.log')).read_bytes();text=raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig')
    match=re.search(pattern,text)
    assert match,(name,pattern)
    counts[name]=int(match[1])
lib.put_json('summary.json',{'executedSourceCommit':status['sourceCommitAtLaunch'],'focusedStagePass':True,
 'counts':counts,'nativeBoundedComparisons':{n:{k:c.get(k) for k in ('passed','baseline_states','candidate_states','max_position_difference_m')} for n,c in comparisons.items()},
 'runs':results,'vtkByteIdentity':vtk_identity,'sourceUnchangedDuringChecks':True,'all31OriginalFormsRetained':True,'numericalBodyChanges':False,
 'unitProvenance':'Live committed files hashed before and after checks; CLI separately copies and loads frozen source',
 'fullG3':'PARTIAL; latest full Joss cancelled by user','G1':'PARTIAL; native model/state/evolution migration pending',
 'scientificValidation':False})
lib.put_bytes('README.md',b'# P3 diagnostics ownership evidence\n\nFresh Windows native checks on 333306b; all 13 commands exit 0.\nTwo bounded VM/MC regressions use the unchanged strict comparator against P1.\nExisting defining bodies remain byte-identical. Full architecture and scientific\nacceptance remain pending; cancelled Joss was not restarted.\n')
(D/'manifest.json').write_text(json.dumps({'entries':lib.rows},indent=2)+'\n')
assert all(hashlib.sha256((D/r['path']).read_bytes()).hexdigest()==r['sha256'] for r in lib.rows)
print(json.dumps({'verifiedArtifacts':len(lib.rows),'counts':counts,'focusedStagePass':True}))
