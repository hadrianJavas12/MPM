"""Compare actual fixed-code two-update outputs to retained pre-fix gate bytes."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[1]
old = root / 'output/unnotched-gravity-2026-10-24/native-controls-002'
new = root / 'output/unnotched-gravity-2026-10-25/native-output-fixed-001'
def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))
manifest = read(new / 'source/source-manifest.json')
expected = {r['path']: r['sha256'] for r in manifest['files']}
assert len(expected) == len(manifest['files']) == 285
for relative, sha in expected.items():
    assert hashlib.sha256((new / relative).read_bytes()).hexdigest() == sha
for phase in ('before', 'after'):
    actual = {r['path']: r['sha256'] for r in read(new / f'source-proof-{phase}.json')['files']}
    assert actual == expected
rows = []
files = sorted((old / 'observations/vtk').glob('particles_*.vtk'))
assert len(files) == 3
files += [old / 'observations/particles.csv', old / 'observations/history.csv']
for previous in files:
    relative = previous.relative_to(old)
    current = new / relative
    payload = current.read_bytes()
    assert payload == previous.read_bytes(), str(relative)
    rows.append(dict(path=relative.as_posix(), bytes=len(payload),
                     sha256=hashlib.sha256(payload).hexdigest(), byteIdentical=True))
result = dict(status='PASS', comparedFiles=rows, sourceCountVerified=285,
              sourceBeforeAfterVerified=True, physicalUpdates=2,
              acceptedMaterialCalls=1760, savedStates=3,
              scope='Actual post-fix native output is byte-identical to the independently audited pre-fix two-update gate. No new solver, render, full slope or instability validation.')
out = new / 'comparison-to-pre-fix.json'
assert not out.exists()
out.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps(dict(status='PASS', byteIdenticalFiles=len(rows), sourcesVerified=285)))
