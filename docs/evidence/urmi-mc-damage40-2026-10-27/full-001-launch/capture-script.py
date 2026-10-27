"""One immutable launch packet after actual native load and live identity proof."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT/'output/urmi-mc-damage40-2026-10-27/full-001'
DEST = ROOT/'docs/evidence/urmi-mc-damage40-2026-10-27/full-001-launch'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    prep = Path(str(RUN)+'-launch-preparation')
    preparation = read(prep/'preparation.json')
    manifest = read(RUN/'source/source-manifest.json')
    actual = {entry['path']: entry for entry in manifest['files']}
    expected = {entry['path']: entry for entry in preparation['expectedNativeFiles']}
    assert set(actual) == set(expected)
    for name, entry in actual.items():
        data = (RUN/name).read_bytes()
        assert (len(data), sha(data)) == (entry['bytes'], entry['sha256']) == (expected[name]['bytes'], expected[name]['sha256']), name
    provenance = read(RUN/'source-provenance.json')
    assert provenance['sourceSnapshotExactLoadedBytes'] and provenance['copiedByteEqualityBeforeLoad']
    backend = provenance['nativeBackend']
    assert Path(backend['modulePath']).resolve() == (RUN/'source/libs/kirchoff.dll').resolve()
    assert backend['sha256'] == sha((RUN/'source/libs/kirchoff.dll').read_bytes())
    live = read(Path(str(RUN)+'-live-process-verification.json'))
    assert live['passed'] and len(live['processes']) == 4
    assert all(p['exactOriginalProviderMatch'] and p['cimMatchesGetProcessAtMicrosecondPrecision'] for p in live['processes'])
    DEST.mkdir(parents=True, exist_ok=False)
    copies = []
    def copy(path, relative):
        target = DEST/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        assert path.read_bytes() == target.read_bytes()
        copies.append(dict(path=relative, bytes=target.stat().st_size, sha256=sha(target.read_bytes())))
    for suffix in ('-launch.json', '-status.json', '-live-process-verification.json', '-live-proof-helper-attempt-001.json', '.stdout.log', '.stderr.log'):
        copy(Path(str(RUN)+suffix), 'capture/'+RUN.name+suffix)
    for path in Path(str(RUN)+'-detached').rglob('*'):
        if path.is_file():
            copy(path, 'detached/'+path.relative_to(Path(str(RUN)+'-detached')).as_posix())
    for path in prep.rglob('*'):
        if path.is_file() and not path.is_relative_to(prep/'native-expected'):
            copy(path, 'preparation/'+path.relative_to(prep).as_posix())
    copy(RUN/'source-provenance.json', 'source-provenance.json')
    copy(RUN/'source/source-manifest.json', 'source-manifest.json')
    copy(RUN/'manifest.json', 'initial-capture-manifest.json')
    copy(Path(__file__), 'capture-script.py')
    archive = DEST/'executed-source-and-cache.zip'
    members = []
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as output:
        for path in sorted((RUN/'source').rglob('*')):
            if path.is_file():
                data = path.read_bytes()
                relative = path.relative_to(RUN).as_posix()
                output.writestr(relative, data)
                members.append(dict(path=relative, bytes=len(data), sha256=sha(data)))
    with zipfile.ZipFile(archive) as check:
        assert check.testzip() is None and len(check.namelist()) == len(members)
        for entry in members:
            data = check.read(entry['path'])
            assert len(data) == entry['bytes'] and sha(data) == entry['sha256']
    (DEST/'archive-members.json').write_text(json.dumps(members, indent=2)+'\n')
    summary = dict(passed=True, capturedUtc=datetime.now(timezone.utc).isoformat(), nativeFiles=len(actual),
                   completeNativeSourceArchiveMembers=len(members), nativeBackend=backend, nativeSourceCommit=preparation['sourceCommit'],
                   liveIdentity=live, scope='Exact actual native source/DLL, before-launch binding and ONE live parent/clock proof. Early phase capture is not equilibrium, damage onset or full-run validation.',
                   limitations=['Wrapper scenario label gravity-slope is harness family; native actual urmi-damage40',
                                'CIM/GetProcess timestamp precision helper rejection retained; no native/physics change',
                                'Session not proven immune to sleep, reboot or logoff; logs captured only at this timestamp'])
    (DEST/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    entries=[]
    for path in sorted(DEST.rglob('*')):
        if path.is_file():
            data=path.read_bytes();entries.append(dict(path=path.relative_to(DEST).as_posix(),bytes=len(data),sha256=sha(data)))
    (DEST/'evidence-manifest.json').write_text(json.dumps(dict(files=entries,indexedFiles=len(entries),excludedSelf='evidence-manifest.json'),indent=2)+'\n')
    print(json.dumps(dict(passed=True,nativeFiles=len(actual),sourceZipMembers=len(members),indexedFiles=len(entries))))


if __name__ == '__main__':
    main()
