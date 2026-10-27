"""ONE immutable extended001 partial collection; no solver/review/render invocation."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(r'D:/MPM')
RAW = ROOT / 'output/urmi-mc-damage40-2026-10-27'
NAME = 'extended-left12-base8-001'
RUN = RAW / NAME
REVIEW = RUN / 'paired-review-001'
DEST = ROOT / 'docs/evidence/urmi-mc-damage40-2026-10-27/extended-left12-base8-001-partial'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def put(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def record(path, base=DEST):
    data = path.read_bytes()
    return dict(path=path.relative_to(base).as_posix(), bytes=len(data), sha256=sha(data))


def copied(source, destination, ledger):
    before = source.read_bytes()
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    assert before == source.read_bytes() == destination.read_bytes(), source
    ledger.append(dict(original=str(source), copy=record(destination), byteEquality=True))


def files(directory):
    return [p for p in directory.rglob('*') if p.is_file()]


def archive(target, paths, base):
    assert len(paths) == len(set(paths)), 'Duplicate archive input'
    members = []
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED) as output:
        for path in sorted(paths):
            data = path.read_bytes()
            name = path.relative_to(base).as_posix()
            output.writestr(name, data)
            members.append(dict(path=name, bytes=len(data), sha256=sha(data)))
            assert data == path.read_bytes(), f'Archive input changed: {path}'
    with zipfile.ZipFile(target) as check:
        assert check.testzip() is None and len(check.namelist()) == len(members)
        for row in members:
            data = check.read(row['path'])
            assert len(data) == row['bytes'] and sha(data) == row['sha256']
    return dict(archive=target.relative_to(DEST).as_posix(), verifiedMembers=members, count=len(members))


def main():
    assert not DEST.exists(), 'Preserve existing packet; do not duplicate collection'
    manifest = load(RUN / 'manifest.json')
    assert manifest['scenario'] == 'urmi-damage40-extended' and manifest['status'] == 'failed'
    assert manifest['complete'] is False and manifest['savedFrames'] == 5 and manifest['particleCount'] == 219
    assert manifest['timeS'] == 2.5 and manifest['nativeTimeS'] == 5.5
    status = load(RAW / (NAME + '-status.json'))
    assert status['nativeExitCode'] == 1
    assert load(RAW / (NAME + '-detached') / 'worker-exit.json')['exitCode'] == 1
    diagnostic = load(RUN / 'output-state-failure.json')
    assert diagnostic['particleId'] == 138
    assert diagnostic['checks']['domainYPositive'] is False
    assert all(v is True for k, v in diagnostic['checks'].items() if k != 'domainYPositive')
    source_rows = load(RUN / 'source/source-manifest.json')['files']
    current_differences = []
    for row in source_rows:
        path = (RUN / row['path']).resolve()
        assert path.is_relative_to((RUN / 'source').resolve())
        data = path.read_bytes()
        assert len(data) == row['bytes'] and sha(data) == row['sha256'], row['path']
        original = Path(row['originalPath'])
        if not original.is_file() or sha(original.read_bytes()) != row['sha256']:
            current_differences.append(str(original))
    provenance = load(RUN / 'source-provenance.json')
    assert provenance['sourceSnapshotExactLoadedBytes'] is True and provenance['copiedByteEqualityBeforeLoad'] is True
    dll = provenance['nativeBackend']
    assert Path(dll['modulePath']).resolve() == (RUN / 'source/libs/kirchoff.dll').resolve()
    assert dll['verifiedBy'] == 'GetModuleHandleW/GetModuleFileNameW'
    assert sha(Path(dll['modulePath']).read_bytes()) == dll['sha256']
    fasls = {}
    for action in provenance['verifiedAsdfActions']:
        if action.get('firstParty') is True and action.get('event') == 'performing' and action.get('operation') == 'load-op':
            for row in action.get('loadInputs', []):
                path = Path(row['path']).resolve()
                assert path.is_relative_to((RUN / 'source').resolve()) and sha(path.read_bytes()) == row['sha256']
                fasls[str(path)] = row['sha256']
    report = load(REVIEW / 'review.json')
    assert report['savedIntegrity'] == 'PASS' and report['nativeComplete'] is False
    assert report['actualDynamicSavedFrames'] == 5 and report['actualLastDynamicTimeS'] == 2
    assert [s['timeS'] for s in report['states']] == [0, .5, 1, 1.5, 2]
    assert load(REVIEW / 'exit.json')['exitCode'] == 2
    assert load(RUN / 'paired-review-001.exit.json')['exitCode'] == 2
    media = report['media']
    assert media['interpolation'] is False and media['allParticlesShown'] is True
    for movie in media['movies'].values():
        assert movie['decodedFrames'] == 5 and movie['fullDecodeExitCode'] == 0 and movie['framesPerSecond'] == 1
        row = movie['video']
        data = Path(row['path']).read_bytes()
        assert len(data) == row['bytes'] and sha(data) == row['sha256']
    for row in media['summaries'].values():
        data = Path(row['path']).read_bytes()
        assert len(data) == row['bytes'] and sha(data) == row['sha256']
    DEST.mkdir(parents=True)
    (DEST / '.gitattributes').write_text('** -text\n', encoding='utf-8')
    copies = []
    copied(Path(__file__), DEST / 'collector.py', copies)
    copied(Path(__file__).with_suffix('.invocation-before.json'), DEST / 'collection-invocation-before.json', copies)
    archives = [archive(DEST / 'native-source-and-private-cache.zip', files(RUN / 'source'), RUN)]
    native_files = [p for p in files(RUN) if not p.is_relative_to(RUN / 'source') and not p.is_relative_to(REVIEW)]
    native_files += [p for p in RAW.glob(NAME + '*') if p.is_file()]
    native_files += files(RAW / (NAME + '-detached')) + files(RAW / (NAME + '-launch-preparation'))
    archives.append(archive(DEST / 'native-output-runtime-launch.zip', native_files, RAW))
    archives.append(archive(DEST / 'first-paired-review-media.zip', files(REVIEW), RAW))
    for source, name in ((RUN / 'manifest.json', 'native-manifest.json'),
                         (RUN / 'source/source-manifest.json', 'source-manifest.json'),
                         (RUN / 'source-provenance.json', 'source-provenance.json'),
                         (RUN / 'output-state-failure.json', 'output-state-failure.json'),
                         (RAW / (NAME + '-status.json'), 'terminal-status.json'),
                         (RAW / (NAME + '-detached') / 'worker-exit.json', 'worker-exit.json'),
                         (REVIEW / 'review.json', 'first-paired-review.json'),
                         (REVIEW / 'integrity.json', 'first-paired-integrity.json'),
                         (REVIEW / 'exit.json', 'paired-review-child-exit.json'),
                         (RUN / 'paired-review-001.exit.json', 'paired-review-invocation-exit.json'),
                         (REVIEW / 'rough-damage-result.png', 'rough-damage-result.png'),
                         (REVIEW / 'rough-motion-result.png', 'rough-motion-result.png'),
                         (REVIEW / 'rough-motion.mp4', 'rough-motion.mp4'),
                         (REVIEW / 'rough-strength-damage.mp4', 'rough-strength-damage.mp4')):
        copied(source, DEST / name, copies)
    put(DEST / 'verification.json', dict(sourceFilesOriginalVerified=len(source_rows), selectedSourceFilesArchived=len(source_rows),
        fullSourceArchiveMembers=archives[0]['count'], loadedFaslInputsVerified=len(fasls), actualMappedDll=dll,
        currentOriginalSourceDifferences=current_differences, allCurrentOriginalSourcesMatch=not current_differences,
        openblasThreadsRecorded=provenance.get('openblasThreads'), ompThreadsRecorded=provenance.get('ompThreads'),
        savedReviewActualExitCode=2, partialSavedIntegrity='PASS', nativeAndWorkerExitCodes=[1, 1],
        sourceArchiveCopiesPerNativeAttempt=1, mediaFilesIndexed=4,
        bothMoviesDecodedFrames=5, bothMoviesFramesPerSecond=1, bothMovieDecodeExitCodes=[0, 0],
        noSolverReviewOrRenderRepeated=True, gitStaged=False, gitBlobVerification='NOT_EXECUTED: root owns staging/blob proof'))
    put(DEST / 'closure.json', dict(createdUtc=datetime.now(timezone.utc).isoformat(),
        scope='Approved12m left extension/8m foundation rough40degree MC strength-damage demonstration; actual partial failure retained',
        requestedDynamicSeconds=20, actualSavedLastDynamicSeconds=2, attemptedUnsavedDynamicSeconds=2.5,
        actualNativeClockAtFailureS=5.5, savedDynamicFrames=5, particleCount=219, savedDynamicParticleRows=1095,
        exactFailureDiagnosticCaptured=True, failedFullParticleStateRetained=False,
        failure='Actual output guard ID138: only domainYPositive=false, domainSizeY=-0.09135596708695834m; other captured predicates true',
        failureMeaning='Negative CPDI particle-domain y size; NOT a native MC material rejection or constitutive replay capsule',
        failureDiagnosticSource='Direct retained output-state-failure.json, no failed state reconstructed',
        nativeTerminalUtc=status['endedUtc'], firstPairedSavedReviewExitCode=2,
        preparedObserverFrozenBeforeLaunch=True,
        media='Both movies use the SAME5 actual saved states at1fps/5s; no interpolation; fixed equal-metre axes; all219MP',
        visualInspection='Parent agent reports both actual PNGs visually inspected; collector performs byte preservation only',
        scientificallyValidated=False, native20sCompleted=False,
        mediaFilesIndexed=4, fullSourceArchives=1, archives=len(archives), archiveMembers=sum(a['count'] for a in archives)))
    put(DEST / 'archive-members.json', archives)
    put(DEST / 'copy-verification.json', dict(records=copies, byteIdenticalCopies=len(copies)))
    indexed = [record(p) for p in sorted(DEST.rglob('*')) if p.is_file()]
    put(DEST / 'evidence-manifest.json', dict(files=indexed, indexedFiles=len(indexed), excludedSelf='evidence-manifest.json'))
    for row in indexed:
        assert record(DEST / row['path']) == row
    print(json.dumps(dict(packet=str(DEST), indexedFiles=len(indexed), totalFiles=len(indexed)+1, archives=len(archives),
        decodedArchiveMembers=sum(a['count'] for a in archives), originalSourceFilesVerified=len(source_rows),
        fullSourceArchiveMembers=archives[0]['count'], loadedFaslInputsVerified=len(fasls), mediaFilesIndexed=4,
        currentOriginalSourceDifferences=current_differences, gitStaged=False)))


if __name__ == '__main__':
    main()
