import datetime,json,os,subprocess,hashlib
from pathlib import Path
r=Path('D:/MPM');b=r/'output/architecture-migration-2026-10-16/p2-baseline-002'
assert not b.exists();b.mkdir()
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
sources=[r/'cl-mpm.asd',*r.glob('src/**/*.lisp'),*r.glob('materials/**/*.lisp'),*r.glob('framework/**/*.lisp')]
rec={'sourceCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip(),'startedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sources':{p.relative_to(r).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'results':{},'status':'RUNNING'}
def save():(b/'status.json').write_text(json.dumps(rec,indent=2)+'\n')
save()
for label,system in [('base','cl-mpm-framework'),('chalk','cl-mpm/models/chalk'),('ice','cl-mpm/models/ice'),('limestone','cl-mpm/models/limestone'),('visco','cl-mpm/models/visco')]:
 with (b/(label+'.log')).open('wb') as log:
  code=subprocess.call(['cmd.exe','/c',str(r/'windows/cl-mpm.cmd'),'tests/native-model-catalog.lisp',system,str(b/(label+'.sexp'))],cwd=r,stdout=log,stderr=subprocess.STDOUT)
 rec['results'][label]={'exitCode':code};save()
rec['sourceUnchangedDuringChecks']=all(p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==rec['sources'][p.relative_to(r).as_posix()] for p in sources)
rec['status']='COMPLETE';save()

