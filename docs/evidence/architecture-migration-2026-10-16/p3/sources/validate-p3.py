"""Finite focused stage checks only. Never starts the cancelled full Joss run."""
import datetime,hashlib,json,os,subprocess,sys
from pathlib import Path
R=Path('D:/MPM');B=R/'output/architecture-migration-2026-10-16/p3'
if B.exists():raise SystemExit('Refusing duplicate validation directory')
B.mkdir(parents=True)
os.chdir(R)
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',STUDIO_REQUIRE_SBCL_TESTS='1')
PY=str(R/'toolchain/analysis-venv/Scripts/python.exe')
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
paths=subprocess.check_output(['git','ls-files','materials','src/measurements','framework','scripts/run-case.lisp','tests'],text=True).splitlines()
hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in paths if (R/p).is_file()}
report={'sourceCommitAtLaunch':head,'startedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'sourceSha256':hashes,'status':'RUNNING','checks':{},'fullJoss':'NOT_RUN_USER_CANCELLED'}
def save(): (B/'status.json').write_text(json.dumps(report,indent=2)+'\n')
def run(name,args,cwd=R):
    with (B/(name+'.log')).open('wb') as out:
        code=subprocess.call(args,cwd=cwd,stdout=out,stderr=subprocess.STDOUT)
    report['checks'][name]={'exitCode':code};save()
    if code:report['status']='FAILED';save();raise SystemExit(code)
def native(name,*args):run(name,[os.environ.get('COMSPEC','cmd.exe'),'/c',str(R/'windows/cl-mpm.cmd'),*args])
save()
native('framework-components','tests/framework-components.lisp')
native('config-contracts','tests/config-contracts.lisp')
native('material-diagnostics','tests/material-diagnostics.lisp',str(B/'mc-triaxial'))
native('diagnostics-normal','tests/diagnostics-ownership-compat.lisp')
native('diagnostics-legacy','tests/diagnostics-ownership-compat.lisp','legacy')
native('ownership-normal','tests/material-ownership-compat.lisp')
native('ownership-legacy','tests/material-ownership-compat.lisp','legacy')
native('snapshot-contract','tests/case-snapshot-contracts.lisp',str(B/'snapshot-contract'))
run('node-check',['cmd.exe','/c','npm','run','check'],R/'studio')
run('node-tests',['cmd.exe','/c','npm','test'],R/'studio')
native('triaxial-short','scripts/run-case.lisp','tests/cases/triaxial-integration.lisp',str(B/'triaxial-short'))
for name in ('mc-triaxial','triaxial-short'):
    run(name+'-comparison',[PY,'scripts/compare-framework-runs.py','--baseline',str(B.parent/'p1'/name),
                            '--candidate',str(B/name),'--output',str(B/(name+'-comparison.json'))])
report['sourceUnchangedDuringChecks']=all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
report['status']='PASS' if report['sourceUnchangedDuringChecks'] else 'SOURCE_CHANGED'
report['endedUtc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
