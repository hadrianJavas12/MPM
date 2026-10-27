"""ONE archive/hash closure for existing worker and preview controls; no tests/solver/review."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(r'D:/MPM')
RAW = ROOT / 'output/urmi-mc-damage40-2026-10-27'
DEST = ROOT / 'docs/evidence/urmi-mc-damage40-2026-10-27/acceleration-preview-controls'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def put(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def file_record(path, base):
    data = path.read_bytes()
    return dict(path=path.relative_to(base).as_posix(), bytes=len(data), sha256=digest(data))


def copy(source, destination, records):
    before = source.read_bytes()
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    after, copied = source.read_bytes(), destination.read_bytes()
    assert before == after == copied, source
    records.append(dict(source=str(source), destination=destination.relative_to(DEST).as_posix(),
                        bytes=len(copied), sha256=digest(copied), copiedByteEquality=True))


def archive(target, paths, base):
    members = []
    assert len(paths) == len(set(paths)), 'Duplicate archive input'
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED) as output:
        for path in sorted(paths):
            data = path.read_bytes()
            name = path.relative_to(base).as_posix()
            output.writestr(name, data)
            members.append(dict(path=name, bytes=len(data), sha256=digest(data)))
            assert path.read_bytes() == data, f'Changed archive input: {path}'
    with zipfile.ZipFile(target) as check:
        assert check.testzip() is None and len(check.namelist()) == len(members)
        for entry in members:
            data = check.read(entry['path'])
            assert len(data) == entry['bytes'] and digest(data) == entry['sha256']
    return dict(archive=target.relative_to(DEST).as_posix(), verifiedMemberCount=len(members),
                verifiedMembers=members)


def verify_native(run):
    rows = load(run / 'source/source-manifest.json')['files']
    known, current_differences = {}, []
    for row in rows:
        path = (run / row['path']).resolve()
        assert path.is_relative_to((run / 'source').resolve()), row
        data = path.read_bytes()
        assert len(data) == row['bytes'] and digest(data) == row['sha256'], row
        assert row['path'] not in known, row
        known[row['path']] = row['sha256']
        original = Path(row['originalPath'])
        if not original.is_file() or digest(original.read_bytes()) != row['sha256']:
            current_differences.append(str(original))
    for name in ('source-proof-before.json', 'source-proof-after.json'):
        assert {r['path']: r['sha256'] for r in load(run / name)['files']} == known, name
    provenance = load(run / 'source-provenance.json')
    assert provenance['sourceSnapshotExactLoadedBytes'] is True
    assert provenance['copiedByteEqualityBeforeLoad'] is True
    before_provenance = load(run / 'source-provenance-before.json')
    assert before_provenance['nativeBackend'] == provenance['nativeBackend']
    dll = provenance['nativeBackend']
    assert Path(dll['modulePath']).resolve() == (run / 'source/libs/kirchoff.dll').resolve()
    assert dll['verifiedBy'] == 'GetModuleHandleW/GetModuleFileNameW'
    assert digest(Path(dll['modulePath']).read_bytes()) == dll['sha256']
    loaded = {}
    for action in provenance['verifiedAsdfActions']:
        if action.get('firstParty') and action.get('event') == 'performing' and action.get('operation') == 'load-op':
            for item in action.get('loadInputs', []):
                path = Path(item['path']).resolve()
                assert path.is_relative_to((run / 'source').resolve())
                assert digest(path.read_bytes()) == item['sha256']
                if str(path) in loaded:
                    assert loaded[str(path)] == item['sha256']
                loaded[str(path)] = item['sha256']
    result = load(run / 'result.json')
    assert result['passed'] is True and len(result['passedGroups']) == 4
    assert result['mpmUpdatesAccepted'] == 20
    assert load(Path(str(run) + '.exit.json'))['exitCode'] == 0
    expected = [('drained', 67140, 67140), ('transfer', 6714, 6714),
                ('undrained', 67140, 67140), ('plastic-native', 72, 72), ('expected-failure', 1, 0)]
    assert [(r['stage'], r['attempted'], r['accepted']) for r in result['counters']] == expected
    assert result['observations']['particleCount'] == 6714
    assert result['observations']['actualCustomWorkers'] == result['workers']
    assert result['observations']['actualLparallelWorkers'] == result['workers']
    return dict(status='PASS', sourceFilesVerified=len(rows), uniqueLoadedFaslInputsVerified=len(loaded),
                actualMappedDll=dll, currentOriginalDifferences=current_differences,
                sourceBeforeAfterAndManifestIdentical=True,
                openblasThreadsRecorded=provenance.get('openblasThreads'), ompThreadsRecorded=provenance.get('ompThreads'),
                externalMathThreadLimitClaim='UNAVAILABLE: benchmark provenance values are null; no single-thread assertion inferred',
                nativeGroups=4, genuineUSFUpdates=20, particleCount=6714, counters=result['counters'])


def main():
    verifications = {name: verify_native(RAW / name) for name in ('workers1-001', 'workers4-001')}
    one, four = [load(RAW / name / 'source/source-manifest.json')['files'] for name in verifications]
    assert {r['path']: r['sha256'] for r in one} == {r['path']: r['sha256'] for r in four}
    assert load(RAW / 'worker-comparison-001/review.json')['passed'] is False
    diagnosis = load(RAW / 'worker-diagnosis-001/diagnosis.json')
    assert diagnosis['inputsUnchangedAfterAnalysis'] is True
    assert diagnosis['sourceManifestPayloadSame'] is True
    assert load(RAW / 'worker-diagnosis-001/exit.json')['exitCode'] == 0
    assert load(RAW / 'preview-controls-001/exit.json')['exitCode'] == 2
    assert load(RAW / 'preview-controls-002/exit.json')['exitCode'] == 0
    before, after = [load(RAW / 'preview-controls-002' / n) for n in ('source-before.json', 'source-after.json')]
    assert before == after and len(before) == 2
    for row in before:
        frozen = RAW / 'preview-controls-002/source' / row['path']
        assert digest(frozen.read_bytes()).lower() == row['frozenSha256'].lower() == row['sourceSha256'].lower()
    control_log = (RAW / 'preview-controls-002/stderr.log').read_text(encoding='utf-8-sig')
    assert 'Ran 3 tests in ' in control_log and '\nOK' in control_log
    preflight = load(RAW / 'preview-preflight-001/stdout.log')
    assert preflight['status'] == 'NOT_READY' and preflight['previewCreated'] is False
    assert load(RAW / 'preview-preflight-001/exit.json')['exitCode'] == 0
    DEST.mkdir(parents=True, exist_ok=False)
    (DEST / '.gitattributes').write_text('** -text\n', encoding='utf-8')
    copies, archives = [], []
    copy(Path(__file__), DEST / 'collector.py', copies)
    copy(Path(__file__).with_name('invocation-before.json'), DEST / 'collection-invocation-before.json', copies)
    for name in verifications:
        run = RAW / name
        target = DEST / name
        target.mkdir()
        source_files = [p for p in (run / 'source').rglob('*') if p.is_file()]
        archives.append(archive(target / 'source-and-private-cache.zip', source_files, run))
        for filename in ('result.json', 'source-provenance.json', 'source/source-manifest.json'):
            copy(run / filename, target / Path(filename).name, copies)
        put(target / 'verification.json', verifications[name])
    native_files = []
    for name in verifications:
        run = RAW / name
        native_files += [p for p in run.rglob('*') if p.is_file() and not p.is_relative_to(run / 'source')]
        native_files += [p for p in RAW.glob(name + '.*') if p.is_file()]
    archives.append(archive(DEST / 'native-outputs-and-invocations.zip', native_files, RAW))
    analysis_files = []
    for name in ('worker-comparison-001', 'worker-diagnosis-001', 'preview-controls-001',
                 'preview-controls-002', 'preview-preflight-001'):
        analysis_files += [p for p in (RAW / name).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    archives.append(archive(DEST / 'saved-analysis-and-preview-attempts.zip', analysis_files, RAW))
    for source, name in ((RAW / 'worker-comparison-001/review.json', 'first-worker-comparison-failure.json'),
                         (RAW / 'worker-diagnosis-001/summary.json', 'worker-diagnosis-summary.json'),
                         (RAW / 'worker-diagnosis-001/diagnosis.json', 'worker-diagnosis.json'),
                         (RAW / 'preview-controls-001/exit.json', 'first-preview-invocation-exit.json'),
                         (RAW / 'preview-controls-002/exit.json', 'preview-controls-exit.json'),
                         (RAW / 'preview-preflight-001/stdout.log', 'first-preview-preflight-stdout.log')):
        copy(source, DEST / name, copies)
    put(DEST / 'archive-members.json', archives)
    put(DEST / 'copy-verification.json', dict(records=copies, copiedFilesVerified=len(copies)))
    put(DEST / 'closure.json', dict(createdUtc=datetime.now(timezone.utc).isoformat(),
        scope='NEW bounded worker/control evidence only; active full001 not rerun/reviewed/copied; no full-preview/media execution',
        nativeRuns=verifications, sourcePayloadsByteIdentical=True,
        firstStrictWorkerEquivalence='FAIL preserved: particleCSV/sig_xx_pa; no tolerance relaxation or production switch',
        diagnosis='ONE saved discrepancy analysis, exit0; original negative comparator remains authoritative',
        previewControls='FIRST invocation error2 before test source opened; corrected fresh002 exactly3NEW synthetic controls PASS/exit0; 0native/MPM',
        firstActualPreview='Preflight exit0 NOT_READY/drained/savedFrames0/no preview directory; full workflow NOT_EXECUTED',
        sourceArchives=2, sourceFilesOriginalVerified=sum(v['sourceFilesVerified'] for v in verifications.values()),
        archiveMemberCount=sum(a['verifiedMemberCount'] for a in archives),
        artifactsExcludedFromAnalysisArchive='Only generated __pycache__ files; original raw folders unchanged',
        mediaFiles=0, gitStaged=False, gitBlobVerification='NOT_EXECUTED: parent owns staging and exact Git blob verification'))
    files = [file_record(path, DEST) for path in sorted(DEST.rglob('*')) if path.is_file()]
    put(DEST / 'evidence-manifest.json', dict(indexedFiles=len(files), excludedSelf='evidence-manifest.json', files=files))
    # Independently re-read every indexed artifact after all packaging writes.
    for row in files:
        assert file_record(DEST / row['path'], DEST) == row
    print(json.dumps(dict(packet=str(DEST), indexedFiles=len(files), archives=len(archives),
        archiveMembers=sum(a['verifiedMemberCount'] for a in archives),
        originalSourceFilesVerified=sum(v['sourceFilesVerified'] for v in verifications.values()),
        decodedSourceArchiveMembers=sum(a['verifiedMemberCount'] for a in archives[:2]),
        actualMediaFiles=0, gitStaged=False)))


if __name__ == '__main__':
    main()
