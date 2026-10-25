"""Package existing new static controls and one formal search; no calculations."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

root = Path(__file__).resolve().parents[1]
raw = root / 'output/unnotched-statics-2026-10-25'
out = root / 'docs/evidence/unnotched-gravity-2026-10-25/static-diagnostic'
out.mkdir(parents=True, exist_ok=False)

def copy(src, rel):
    dst = out / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    assert dst.read_bytes() == src.read_bytes()

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

assert read(raw / 'controls-001/result.json')['exitCode'] == 0
assert read(raw / 'controls-001/result.json')['sourceBeforeAfterMatch']
assert read(raw / 'search-001-exit.json')['exitCode'] == 0
result = read(raw / 'search-001/result.json')
assert not result['globalFactorOfSafetyCertified'] and not result['mpmValidation']
for name in ('controls-001', 'search-001'):
    for path in sorted((raw / name).rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts:
            copy(path, path.relative_to(raw))
for name in ('search-001.log', 'search-001-exit.json'):
    copy(raw / name, Path(name))
for name in ('static-reference-audit.md', 'static-reference-audit.json'):
    copy(root / 'research/notes/unnotched-landslide-2026-10-24' / name, Path('source-audit') / name)
copy(Path(__file__), Path('executed-pack-script.py'))
(out / '.gitattributes').write_bytes(b'* -text\n')
(out / 'README.md').write_text(
    '# Independent formal static diagnostic\n\n'
    'Five new mathematical controls and one preregistered dry simplified-Bishop search. '
    'No native MPM updates or old tests/reviews were repeated. Exact sources and contract '
    'were copied before the numerical search; the copied backend was executed. All candidate '
    'outcomes, negative base-normal forces, boundary minima and restricted-family/slice results '
    'are retained. Negative normals are not clamped; no tension-crack model is adopted. '
    'This is not a certified global FoS, physical-admissibility PASS, exact-paper reproduction '
    'or validation of MPM/dynamic landslide/runout. Original raw evidence remains in output.\n',
    encoding='utf-8')
records = []
for path in sorted(out.rglob('*')):
    if path.is_file():
        data = path.read_bytes()
        records.append(dict(path=path.relative_to(out).as_posix(),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
(out / 'artifact-index.json').write_text(json.dumps(dict(artifacts=records),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(packet=str(out),indexedArtifacts=len(records))))
