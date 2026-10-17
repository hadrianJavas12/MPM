"""Retain actual refactor regression evidence; refuses incomplete native runs."""
import csv,gzip,hashlib,importlib.util,io,json,shutil,tarfile
from pathlib import Path
ROOT=Path('D:/MPM');BASE=ROOT/'output/framework-refactor-2026-10-15';DEST=ROOT/'docs/evidence/framework-refactor-2026-10-15'
spec=importlib.util.spec_from_file_location('comparison',ROOT/'scripts/compare-framework-runs.py');cmp=importlib.util.module_from_spec(spec);spec.loader.exec_module(cmp)
rows=[]
def digest(data):return hashlib.sha256(data).hexdigest()
def put_bytes(relative,data,source=None,**extra):
    path=DEST/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    rows.append(dict(path=str(relative).replace('\\','/'),bytes=len(data),sha256=digest(data),source=source,**extra));return path
def put_file(relative,path):return put_bytes(relative,path.read_bytes(),str(path.relative_to(ROOT)))
def put_json(relative,value):return put_bytes(relative,(json.dumps(value,indent=2,allow_nan=False)+'\n').encode('utf8'))
def zipped_file(relative,path):return put_bytes(relative,gzip.compress(path.read_bytes(),compresslevel=9,mtime=0),str(path.relative_to(ROOT)),uncompressedSha256=digest(path.read_bytes()))
def archive(relative,files):
    stream=io.BytesIO();members=[]
    with tarfile.open(fileobj=stream,mode='w') as tar:
        for name,path in sorted(files):
            data=path.read_bytes();info=tarfile.TarInfo(name.replace('\\','/'));info.size=len(data);info.mtime=0;info.mode=0o644;tar.addfile(info,io.BytesIO(data));members.append({'path':info.name,'bytes':len(data),'sha256':digest(data),'source':str(path.relative_to(ROOT))})
    return put_bytes(relative,gzip.compress(stream.getvalue(),compresslevel=9,mtime=0),members=members)

def run_evidence(label,run):
    table,columns,states=cmp.recorded_states(run)
    meta=run/('reference-metadata.json' if table=='timesteps.csv' else 'manifest.json')
    metadata=json.loads(meta.read_text(encoding='utf-8-sig'))
    if metadata.get('complete') is not True:raise ValueError('Incomplete native run '+str(run))
    put_file(label+'/'+table,run/table);put_file(label+'/'+meta.name,meta)
    for name in ('transitions.csv','source-provenance.json','effective-config.json','audit.json','final-t40.png','simulation.mp4','triaxial-result.png','triaxial-simulation.mp4','visualization-provenance.json','triaxial-refactor-comparison.png','comparison-visualization-provenance.json','media-validation.json'):
        path=run/name
        if path.exists():put_file(label+'/'+name,path)
    frame_rows=[]
    for state in states:
        points,fields=cmp._reader.read_particle_vtk(state['path'])
        frame_rows.append({'time':state['time'],'file':state['path'].relative_to(run).as_posix(),'sha256':cmp.sha256(state['path']),**cmp.state_summary(points,fields)})
    put_json(label+'/all-saved-state-audit.json',{'basis':'Strict native binaryVTK parser checks allavailablearraysfinite; x-u identity; no interpolation or invented deformation','frameCount':len(states),'states':frame_rows})
    if table=='timesteps.csv':
        chosen={states[0]['path'],states[-1]['path']}
        for key in ('lower_reference_y_le_4m','upper_reference_y_ge_9m'):
            record=next((r for r in frame_rows if r.get(key) is not None and r[key]>.05),None)
            if record:chosen.add(run/record['file'])
        chosen.update(p for p in (run/'vtk/initial.vtk',run/'vtk/equilibrium.vtk') if p.exists())
    else:chosen={state['path'] for state in states}
    archive(label+'/particle-vtk.tar.gz',[(p.relative_to(run).as_posix(),p) for p in chosen])
    return {'complete':True,'frames':len(states),'finalTimeS':states[-1]['time'],'particleCount':frame_rows[-1]['particles'],'finalMass':frame_rows[-1]['mass'],'maxRelativeMassDrift':max(abs(r['mass']/frame_rows[0]['mass']-1) for r in frame_rows),'last':frame_rows[-1]}

def main():
    # Fail before writing any deliverable if eitherafterjob is incomplete.
    for name in ('joss-after','triaxial-2d-after'):
        run=BASE/name;path=run/('reference-metadata.json' if name.startswith('joss') else 'manifest.json')
        if not path.exists() or json.loads(path.read_text(encoding='utf-8-sig')).get('complete') is not True:raise ValueError('Postrun notcomplete '+name)
    DEST.mkdir(parents=True,exist_ok=True)
    put_bytes('.gitattributes',b'* -text -whitespace\n*.png binary\n*.mp4 binary\n*.gz binary\n')
    results={}
    for label,name in [('joss-before','joss-baseline'),('joss-after','joss-after'),('triaxial-before','triaxial-2d-before-mps2'),('triaxial-after','triaxial-2d-after')]:results[label]=run_evidence(label,BASE/name)
    for name in ('accepted-vs-frozen-strict.json','accepted-vs-frozen-final-shape.json','comparator-guard-checks.json','joss-extraction-review.json','triaxial-2d-baseline-adaptation.json','triaxial-2d-first-attempt-failure.json','environment-provenance.json','after-processes.json','joss-baseline-provenance.json','joss-baseline-status.json','joss-after-status.json','triaxial-2d-after-status.json','joss-full-regression-summary.json','current-head-integration-summary.json','current-head-source-comparison.json'):
        path=BASE/name
        if path.exists():put_file('verification/'+name,path)
    for name in ('joss-before-after-comparison.json','triaxial-before-after-comparison.json','accepted-vs-frozen-diagnostics.json','joss-before-after-diagnostics.json','accepted-vs-after-diagnostics.json'):
        path=BASE/name
        if not path.exists():raise ValueError('Missing comparison '+name)
        zipped_file('verification/'+name+'.gz',path)
    for name in ('comparator-self-check.json',):
        if (BASE/name).exists():zipped_file('verification/'+name+'.gz',BASE/name)
    for name in ('joss-baseline.log','joss-after.log','triaxial-2d-before-mps2.log','triaxial-2d-after.log','node-check.log','node-tests.log','framework-load.log','studio-custom-compat.log','triaxial-definitions-load.log','triaxial-component-contracts.log','joss-unit-compat.log','current-head-joss.log','current-head-joss-audit.log','current-head-triaxial.log','current-head-triaxial-audit.log','current-head-cliff-mc.log'):
        path=BASE/name
        if path.exists():zipped_file('logs/'+name+'.gz',path)
    for path in (BASE/'failed-cli-package-lock').glob('*'):
        if path.is_file():zipped_file('logs/failed-cli-package-lock/'+path.name+'.gz',path)
    for name in ('scripts/compare-framework-runs.py','scripts/compare-reference-video.py','scripts/render-particle-vtk.py','scripts/plot-triaxial.py','scripts/audit-triaxial.py'):
        put_file('sources/'+Path(name).name,ROOT/name)
    for name in ('run-frozen-joss.lisp','run-triaxial-2d-baseline.lisp','launch-joss-baseline.ps1','launch-joss-after.ps1','launch-triaxial-after.ps1','joss-baseline-config.json','triaxial-2d-baseline-adaptation.patch'):
        path=BASE/name
        if path.exists():put_file('sources/'+name,path)
    archive('sources/frozen-original-scenario-source.tar.gz',[(p.relative_to(BASE/'baseline-source').as_posix(),p) for p in (BASE/'baseline-source').rglob('*') if p.is_file()]+[('adapted-2d/triaxial.lisp',BASE/'triaxial-2d-baseline-source.lisp')])
    archive('sources/executed-after-source.tar.gz',[(p.relative_to(BASE/'joss-after/source').as_posix(),p) for p in (BASE/'joss-after/source').rglob('*') if p.is_file()]+[('triaxial-case.lisp',BASE/'triaxial-2d-after/source/case.lisp')])
    for name in ('joss-after','triaxial-2d-after'):
        records=[{'path':p.relative_to(BASE/name/'source').as_posix(),'sha256':cmp.sha256(p),'bytes':p.stat().st_size} for p in sorted((BASE/name/'source').rglob('*')) if p.is_file()]
        put_json('sources/'+name+'-executed-source-manifest.json',{'path':str(BASE/name/'source'),'scope':'Exact copied source loaded bypublicCLI, runtime dependenciesseparate','files':records})
    for name in ('stress-strain.csv','effective-config.json'):
        put_file('context/previous-3d-'+name,ROOT/'output/triaxial-3d-demo'/name)
    for name in ('analyze-framework-regression.py','summarize-joss-full-result.py','validate-framework-comparator.py'):
        put_file('sources/'+name,ROOT/'.tmp'/name)
    put_file('README.md',ROOT/'.tmp/framework-evidence-README.md')
    mc=BASE/'current-head-cliff-mc'
    for name in ('integration-audit.json','source-provenance.json'):
        put_file('bounded-cliff-mc/'+name,mc/name)
    archive('bounded-cliff-mc/particle-vtk.tar.gz',[(p.name,p) for p in (mc/'vtk').glob('*.vtk') if p.stem!='mesh'])
    archive('bounded-cliff-mc/executed-source.tar.gz',[(p.relative_to(mc/'source').as_posix(),p) for p in (mc/'source').rglob('*') if p.is_file()])
    comparisons={label:json.loads((BASE/file).read_text(encoding='utf8')) for label,file in [('joss','joss-before-after-comparison.json'),('triaxial','triaxial-before-after-comparison.json')]}
    put_json('validation-summary.json',{'dateLocal':'2026-10-15','beforeCommit':'c749d32','afterCommit':'2f6476f','regressionPassed':all(v.get('passed') is True for v in comparisons.values()),'regression':{k:{j:v[j] for j in ('passed','failure','error','baseline_states','candidate_states','max_position_difference_m') if j in v} for k,v in comparisons.items()},'runs':results,'historicalAcceptedReplay':'All three reach 40 s, initiate lower damage at 4 s and upper damage at 7.5 s, then collapse. Historical/fresh original/refactored have 174/176/191 saved frames. Strict equivalence fails; separate final-domain IoU is a shape diagnostic, not physical accuracy.','causality':'Early roundoff and later amplification are consistent with nondeterministic runtime, but causality is not proved by these runs. A controlled deterministic comparison remains necessary before claiming numerical equivalence.','scientificValidation':False,'limitations':['2D plane-strain rectangle at unit depth, not axisymmetric or a 3D cylinder','No independent laboratory clay calibration','Native 2D VTK exports in-plane stress only; full 3D qJ2 cannot be independently reconstructed from those VTK fields','Historical accepted warm start and fresh original baseline use different preparations','Original algorithmic audit caveats remain; no convergence or energy-closure proof']})
    (DEST/'manifest.json').write_text(json.dumps({'sourceRoot':'D:/MPM','scope':'Retainedactualnativeoutputs; fullJossVTKslocalignored, allframeshashesretained; selectedJoss/all2DVTKsarchived','entries':rows},indent=2)+'\n',encoding='utf8')
    for row in rows:
        path=DEST/row['path'];assert cmp.sha256(path)==row['sha256']
    print(json.dumps({'files':len(rows),'bytes':sum(row['bytes'] for row in rows),'destination':str(DEST)},indent=2))

if __name__ == '__main__':
    main()
