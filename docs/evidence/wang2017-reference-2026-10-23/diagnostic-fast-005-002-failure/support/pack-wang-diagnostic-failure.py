import gzip,hashlib,io,json,shutil,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
run=ROOT/'output/wang2017-reference-2026-10-23/diagnostic-fast-005-002'
dest=ROOT/'docs/evidence/wang2017-reference-2026-10-23/diagnostic-fast-005-002-failure'
status=json.loads(Path(str(run)+'-status.json').read_text(encoding='utf-8-sig'))
assert status['status']=='FAILED_NATIVE' and status['nativeExitCode']==1
review=json.loads((run/'failure-feasibility-review.json').read_text())
replay=json.loads((run/'failure-replay.json').read_text())
assert replay['passed'] and review['sourceBytesMatch'] and review['necessaryApexBoundViolated']
dest.mkdir(parents=True,exist_ok=False)
(dest/'.gitattributes').write_text('* -text -whitespace\n')
def archive(path,entries):
 with path.open('wb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as zipped:
  with tarfile.open(fileobj=zipped,mode='w') as target:
   for name,p in sorted(entries):
    data=p.read_bytes();info=tarfile.TarInfo(name);info.size=len(data);info.mtime=0;target.addfile(info,io.BytesIO(data))
archive(dest/'raw-native-output.tar.gz',[(p.relative_to(run).as_posix(),p) for p in run.rglob('*') if p.is_file() and 'source' not in p.relative_to(run).parts])
archive(dest/'executed-source.tar.gz',[(p.relative_to(run/'source').as_posix(),p) for p in (run/'source').rglob('*') if p.is_file() and '.native-cache' not in p.parts])
archive(dest/'supervision-logs.tar.gz',[(p.name,p) for p in run.parent.glob(run.name+'*') if p.is_file()])
for name in ('mc-integration-failure.json','failure-feasibility-review.json','failure-replay.json','manifest.json','force-displacement.csv','energy-history.csv','gravity-history.csv'):
 shutil.copyfile(run/name,dest/name)
shutil.copyfile(Path(str(run)+'-status.json'),dest/'native-status.json')
(dest/'support').mkdir();shutil.copyfile(__file__,dest/'support'/Path(__file__).name)
shutil.copyfile(ROOT/'scripts/replay-mc-failure.lisp',dest/'support/replay-mc-failure.lisp')
(dest/'README.md').write_text(
 '# Actual accelerated Wang Soil1 failure capture\n\n'
 'Source d60335a,0.005m/s (50x paper), fresh Windows native diagnostic. Native exit1 at12:35WIB, '
 'after last saved15.4s/command77mm; incomplete20s target. User extension applied to3h via verified monitor handoff '
 'a3afef0, unchanged cmd/SBCL identities. Failure occurred before extended deadline.\n\n'
 'Exact actual failed-return inputs retained, six MC source files match executed frozen bytes, JSON replay PASS. '
 'J1.0032291051924629; mean trial42985.3710489162Pa exceeds necessary perfect-MC/psi0 bound42982.78940658873Pa '
 'by2.58164232747Pa. No admissible zero-dilation return can lower the mean into this domain. '
 'This proves captured-state failure, not failure at paper speed or validity of a new tensile model.\n\n'
 '78 loading particle VTKs,78 force/energy rows and137 gravity rows retained. Raw source/inputs, DLL/ASDF '
 'proof, supervisor metadata, capsule, histories and logs are archived. Replay is one pure material return, '
 'not whole-MPM restart; saved15.4s is not the exact time of the subsequent rejected substep. '
 'No full-run audit PASS, scientific validation, reference-speed curve, clamp or parameter adjustment is claimed.\n',encoding='utf-8')
entries=[dict(path=p.relative_to(dest).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(dest.rglob('*')) if p.is_file()]
(dest/'evidence-manifest.json').write_text(json.dumps({'entries':entries},indent=2)+'\n')
assert all(hashlib.sha256((dest/e['path']).read_bytes()).hexdigest()==e['sha256'] for e in entries)
print(json.dumps({'verifiedArtifacts':len(entries),'archiveBytes':sum(e['bytes'] for e in entries)}))
