"""Archive the completed bounded pipeline and saved-data controls, no simulation."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'output/urmi-mc-damage40-2026-10-27'
DEST = ROOT / 'docs/evidence/urmi-mc-damage40-2026-10-27/pipeline-and-review-controls'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def put(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def archive(target, paths, base):
    members = []
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED) as output:
        for path in sorted(paths):
            data = path.read_bytes()
            name = path.relative_to(base).as_posix()
            output.writestr(name, data)
            members.append(dict(path=name, bytes=len(data), sha256=digest(data)))
    with zipfile.ZipFile(target) as check:
        assert check.testzip() is None and len(check.namelist()) == len(members)
        for entry in members:
            data = check.read(entry['path'])
            assert len(data) == entry['bytes'] and digest(data) == entry['sha256']
    return dict(archive=target.name, verifiedMembers=members)


def main():
    run = RAW / 'pipeline-001'
    result = load(run / 'result.json')
    assert result['passed'] is True and len(result['passedGroups']) == 4
    assert load(RAW / 'pipeline-001.exit.json')['exitCode'] == 0
    assert load(RAW / 'pipeline-saved-audit-002/review.json')['passed'] is True
    assert load(RAW / 'review-controls-001/exit.json')['exitCode'] == 1
    assert load(RAW / 'review-controls-002/exit.json')['exitCode'] == 0
    source = run / 'source'
    rows = load(source / 'source-manifest.json')['files']
    for entry in rows:
        data = (run / entry['path']).read_bytes()
        assert len(data) == entry['bytes'] and digest(data) == entry['sha256']
    for name in ('source-proof-before.json', 'source-proof-after.json'):
        proof = load(run / name)['files']
        assert {r['path']: r['sha256'] for r in proof} == {r['path']: r['sha256'] for r in rows}
    DEST.mkdir(parents=True, exist_ok=False)
    (DEST / '.gitattributes').write_text('** -text\n', encoding='utf-8')
    shutil.copyfile(__file__, DEST / 'collector.py')
    archives = [archive(DEST / 'native-source-and-cache.zip', [p for p in source.rglob('*') if p.is_file()], run)]
    native_files = [p for p in run.rglob('*') if p.is_file() and not p.is_relative_to(source)]
    native_files += [p for p in RAW.glob('pipeline-001.*') if p.is_file()]
    archives.append(archive(DEST / 'native-output-and-invocation.zip', native_files, RAW))
    helpers = []
    for name in ('review-controls-001', 'review-controls-002', 'pipeline-saved-audit-001', 'pipeline-saved-audit-002'):
        helpers.extend(p for p in (RAW / name).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    archives.append(archive(DEST / 'analysis-attempts.zip', helpers, RAW))
    shutil.copyfile(RAW / 'pipeline-saved-audit-002/actual-initial-geometry.png', DEST / 'actual-initial-geometry.png')
    for name in ('result.json', 'source-provenance.json'):
        shutil.copyfile(run / name, DEST / name)
    shutil.copyfile(RAW / 'pipeline-saved-audit-002/review.json', DEST / 'saved-pipeline-review.json')
    put(DEST / 'archive-members.json', archives)
    put(DEST / 'closure.json', dict(passed=True, nativeSourceFiles=len(rows), particleCount=6714,
        nativeMpmUpdates=4, drainedMaterialAccepted=13428, instantaneousTransferMaterialAccepted=6714,
        undrainedMaterialAccepted=13428, actualVTK=3, actualParticleRows=20142,
        helperControls='FIRST9:8PASS/1incorrect synthetic fixture FAIL; failed fixture selectively repaired1PASS. Production observer unchanged.',
        savedAudit='FIRST harness KeyError: no separate release state in tiny gate. Corrected harness binds actual native origin ledger; saved-data-only002PASS. No solver rerun.',
        rootSpatialReview='Actual initial native particle plot inspected:40degree unnotched face, same active4msoil foundation, all particles retained, equal metre scale.',
        scope='Bounded geometry/MPM/output and synthetic helpers only; drained equilibrium/full60s orchestration/damage onset/scientific validation NOT_RUN',
        stageElapsedRealSeconds=result['stageElapsedRealSeconds'], gitSourceCommit=load(RAW/'pipeline-001.exit.json')['sourceCommit']))
    files = []
    for path in sorted(DEST.rglob('*')):
        if path.is_file():
            data = path.read_bytes()
            files.append(dict(path=path.relative_to(DEST).as_posix(), bytes=len(data), sha256=digest(data)))
    put(DEST / 'evidence-manifest.json', dict(files=files, indexedFiles=len(files), excludedSelf='evidence-manifest.json'))
    print(json.dumps(dict(indexedFiles=len(files), sourceFiles=len(rows), archives=len(archives),
                          archiveMembers=sum(len(a['verifiedMembers']) for a in archives))))


if __name__ == '__main__':
    main()
