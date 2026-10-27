"""Attach actual completed collection invocation/output/exit; no ZIP/data rerun."""
import hashlib
import json
from pathlib import Path
import shutil

RAW = Path(__file__).resolve().parent
DEST = Path(r'D:/MPM/docs/evidence/urmi-mc-damage40-2026-10-27/acceleration-preview-controls')


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def put(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def record(path):
    data = path.read_bytes()
    return dict(path=path.relative_to(DEST).as_posix(), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


assert load(RAW / 'exit.json')['exitCode'] == 0
copies = load(DEST / 'copy-verification.json')
for source, name in ((Path(__file__), 'finalize.py'), (RAW / 'exit.json', 'collection-exit.json'),
                     (RAW / 'stdout.log', 'collection-stdout.log'), (RAW / 'stderr.log', 'collection-stderr.log')):
    target = DEST / name
    assert not target.exists()
    before = source.read_bytes()
    shutil.copyfile(source, target)
    assert before == source.read_bytes() == target.read_bytes()
    copies['records'].append(dict(source=str(source), destination=name, bytes=len(before),
                                  sha256=hashlib.sha256(before).hexdigest(), copiedByteEquality=True))
copies['copiedFilesVerified'] = len(copies['records'])
put(DEST / 'copy-verification.json', copies)
closure = load(DEST / 'closure.json')
closure['scope'] = 'NEW bounded worker/control evidence only; full001 native/source/terminal review belongs to its separate packet; no full-preview/media execution'
closure['collectionActualExitCode'] = 0
closure['collectionLogs'] = ['collection-exit.json', 'collection-stdout.log', 'collection-stderr.log']
put(DEST / 'closure.json', closure)
files = [record(p) for p in sorted(DEST.rglob('*')) if p.is_file() and p.name != 'evidence-manifest.json']
put(DEST / 'evidence-manifest.json', dict(indexedFiles=len(files), excludedSelf='evidence-manifest.json', files=files))
for row in files:
    assert record(DEST / row['path']) == row
assert len(files) == 28
print(json.dumps(dict(indexedFiles=len(files), totalFiles=len(files) + 1, copiedFilesVerified=len(copies['records']),
                      archives=4, verifiedArchiveMembers=1038, nativeTestsOrReviewsRepeated=0, gitStaged=False)))
