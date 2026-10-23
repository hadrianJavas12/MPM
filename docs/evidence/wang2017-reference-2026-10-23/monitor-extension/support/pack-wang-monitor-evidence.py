import gzip, hashlib, io, json, shutil, tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/wang2017-reference-2026-10-23'
DEST=ROOT/'docs/evidence/wang2017-reference-2026-10-23/monitor-extension'
DEST.mkdir(parents=True,exist_ok=False)
(DEST/'.gitattributes').write_text('* -text -whitespace\n')
fixtures=sorted(p for p in OUT.glob('monitor-handoff-test-*') if p.is_file())
for folder in sorted(OUT.glob('monitor-handoff-test-*-support')):
    fixtures.extend(p for p in folder.rglob('*') if p.is_file())
with (DEST/'synthetic-controls.tar.gz').open('wb') as raw, gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as zipped:
    with tarfile.open(fileobj=zipped,mode='w') as target:
        for path in fixtures:
            data=path.read_bytes(); entry=tarfile.TarInfo(path.relative_to(OUT).as_posix())
            entry.size=len(data);entry.mtime=0;target.addfile(entry,io.BytesIO(data))
for name in ('test-wang-monitor-child.lisp','test-wang-monitor-parent.ps1','test-wang-monitor-handoff.ps1'):
    target=DEST/'support'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/'.tmp'/name,target)
shutil.copyfile(__file__,DEST/'support'/Path(__file__).name)
shutil.copyfile(ROOT/'scripts/run-wang2017-trial.ps1',DEST/'support/run-wang2017-trial.ps1')
prefix='diagnostic-fast-005-002'
for name in (prefix+'-launch.json',prefix+'-status.json',prefix+'-monitor-25584-ready.json'):
    shutil.copyfile(OUT/name,DEST/name)
proof=json.loads((OUT/'monitor-handoff-test-003-proof.json').read_text(encoding='utf-8-sig'))
assert proof['passed'] and proof['nativeExitCode']==7
shutil.copyfile(OUT/'monitor-handoff-test-003-proof.json',DEST/'synthetic-proof.json')
state=json.loads((DEST/(prefix+'-status.json')).read_text(encoding='utf-8-sig'))
initial=json.loads((DEST/(prefix+'-launch.json')).read_text(encoding='utf-8-sig'))
assert state['wrapperPid']==25584 and state['previousWrapperPid']==18936
assert state['nativeCommandPid']==21008 and state['maxWallHours']==3
assert state['sourceCommitAtLaunch']==initial['sourceCommitAtLaunch']
assert state['caseSha256']==initial['caseSha256'] and initial['maxWallHours']==1.5
assert state['postprocessorSha256']==initial['postprocessorSha256']
(DEST/'README.md').write_text(
    '# Live Wang diagnostic monitor extension\n\n'
    'User requested a longer running limit. Same cmd21008/SBCL49524 (start04:24:16.4348816UTC), '
    'new supervisor25584 replaces18936. Total deadline is14:24WIB/3h instead of12:54WIB/1.5h. '
    'Native source d60335a, case hash and postprocessor hashes are unchanged; original launch remains immutable. '
    'Monitor implementation a3afef0; READY/event transfer and retained handles are recorded.\n\n'
    'Synthetic control003 PASS: logging continues beyond old deadline and exact native exit7 is retained; '
    'zero MPM updates. Controls001/002 failed fixture argument quoting and are retained, not counted PASS. '
    'This evidence concerns supervision only, not scientific validation or native full-run completion.\n\n'
    '[Official PowerShell7.6.5 Windows file-handle implementation](https://github.com/PowerShell/PowerShell/blob/v7.6.5/src/Microsoft.PowerShell.Commands.Management/commands/management/Process.cs#L2244) '
    'was inspected before transfer; the synthetic test also checks continued inherited-file logging.\n',encoding='utf-8')
entries=[dict(path=p.relative_to(DEST).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(DEST.rglob('*')) if p.is_file()]
(DEST/'evidence-manifest.json').write_text(json.dumps({'entries':entries},indent=2)+'\n')
assert all(hashlib.sha256((DEST/e['path']).read_bytes()).hexdigest()==e['sha256'] for e in entries)
print(json.dumps({'verifiedArtifacts':len(entries),'statusAtCollection':state['status'],'nativePidUnchanged':True,'maxWallHours':state['maxWallHours']}))
