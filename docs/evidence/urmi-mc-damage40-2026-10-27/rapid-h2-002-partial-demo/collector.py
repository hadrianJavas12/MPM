"""ONE immutable rapid002 partial-result collection; no solver/review/media rerun."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(r'D:/MPM')
RAW = ROOT / 'output/urmi-mc-damage40-2026-10-27'
RUN = RAW / 'rapid-h2-002'
REVIEW = RAW / 'rapid-h2-002-review-001'
DEST = ROOT / 'docs/evidence/urmi-mc-damage40-2026-10-27/rapid-h2-002-partial-demo'


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


def archive(target, paths, base):
    assert len(paths) == len(set(paths)), 'Duplicate archive member input'
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


def files(directory):
    return [p for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts]


def main():
    assert not DEST.exists(), 'Inspect existing packet instead of duplicating it'
    manifest = load(RUN / 'manifest.json')
    assert manifest['scenario'] == 'urmi-damage40-rapid' and manifest['status'] == 'failed'
    assert manifest['complete'] is False and manifest['savedFrames'] == 5 and manifest['particleCount'] == 105
    assert manifest['timeS'] == 2.5 and manifest['nativeTimeS'] == 5.5
    assert manifest['error'] == 'Owned frame violates V=J*V0, domain/history/work/yield at ID55.'
    assert load(RAW / 'rapid-h2-002-status.json')['nativeExitCode'] == 1
    assert load(RAW / 'rapid-h2-002-detached/worker-exit.json')['exitCode'] == 1
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
    report, slow = load(REVIEW / 'review.json'), load(REVIEW / 'slow-media.json')
    assert report['savedIntegrity'] == 'PASS' and report['nativeComplete'] is False
    assert report['actualDynamicSavedFrames'] == 5 and report['actualLastDynamicTimeS'] == 2
    assert [s['timeS'] for s in report['states']] == [0, .5, 1, 1.5, 2]
    assert load(REVIEW / 'exit.json')['exitCode'] == 2
    assert load(RAW / 'rapid-h2-002-review-001-invocation/exit.json')['exitCode'] == 2
    assert report['media']['fullDecodeExitCode'] == 0 and report['media']['decodedFrames'] == 5
    assert slow['fullDecodeExitCode'] == 0 and slow['decodedFrameCount'] == 5 and slow['playbackFramesPerSecond'] == 1
    assert slow['interpolation'] is False and slow['sourceFrameHashesUnchanged'] is True
    for row in slow['sourceFrames']:
        assert sha(Path(row['path']).read_bytes()) == row['sha256']
    for row in (slow['video'], report['media']['video'], report['media']['summary']):
        data = Path(row['path']).read_bytes()
        assert len(data) == row['bytes'] and sha(data) == row['sha256']
    diagnosis = load(RAW / 'rapid-h2-002-frame-failure-diagnosis-001/diagnosis.json')
    assert diagnosis['allInputsUnchangedAfter'] is True
    assert load(RAW / 'rapid-h2-002-frame-failure-diagnosis-001/exit.json')['exitCode'] == 0
    negative = RAW / 'rapid-h2-001-detached/wrapper.stderr.log'
    assert "parameter name 'EvidenceDirectory'" in negative.read_text(encoding='utf-8-sig')
    assert not (RAW / 'rapid-h2-001').exists(), 'Do not claim absent native run without inspecting changed state'
    DEST.mkdir(parents=True)
    (DEST / '.gitattributes').write_text('** -text\n', encoding='utf-8')
    copies = []
    copied(Path(__file__), DEST / 'collector.py', copies)
    copied(Path(__file__).with_name('invocation-before.json'), DEST / 'collection-invocation-before.json', copies)
    archives = [archive(DEST / 'native-source-and-private-cache.zip', files(RUN / 'source'), RUN)]
    native_files = [p for p in files(RUN) if not p.is_relative_to(RUN / 'source')]
    native_files += [p for p in RAW.glob('rapid-h2-002*') if p.is_file()]
    native_files += files(RAW / 'rapid-h2-002-detached') + files(RAW / 'rapid-h2-002-launch-preparation')
    archives.append(archive(DEST / 'native-output-runtime-launch.zip', native_files, RAW))
    review_files = files(REVIEW) + files(RAW / 'rapid-h2-002-review-001-invocation')
    review_files += files(RAW / 'rapid-h2-002-frame-failure-diagnosis-001')
    archives.append(archive(DEST / 'first-partial-review-media-diagnosis.zip', review_files, RAW))
    negative_files = files(RAW / 'rapid-h2-001-detached') + files(RAW / 'rapid-h2-001-launch-preparation')
    archives.append(archive(DEST / 'prior-001-wrapper-negative.zip', negative_files, RAW))
    for source, name in ((RUN / 'manifest.json', 'native-manifest.json'),
                         (RUN / 'source/source-manifest.json', 'source-manifest.json'),
                         (RUN / 'source-provenance.json', 'source-provenance.json'),
                         (RAW / 'rapid-h2-002-status.json', 'terminal-status.json'),
                         (RAW / 'rapid-h2-002-detached/worker-exit.json', 'worker-exit.json'),
                         (REVIEW / 'review.json', 'first-partial-review.json'),
                         (REVIEW / 'slow-media.json', 'slow-media.json'),
                         (REVIEW / 'rough-damage-result.png', 'rough-damage-result.png'),
                         (REVIEW / 'rough-strength-damage.mp4', 'rough-strength-damage.mp4'),
                         (REVIEW / 'rough-strength-damage-slow.mp4', 'rough-strength-damage-slow.mp4'),
                         (RAW / 'rapid-h2-002-frame-failure-diagnosis-001/summary.json', 'frame-failure-summary.json')):
        copied(source, DEST / name, copies)
    last = report['states'][-1]
    put(DEST / 'spatial-review.json', dict(scope='Actual initial-release and final native PNGs visually inspected at equal metre scale; rough numerical demo only',
        roughQualitativeBulkSlidingObserved=True, native20sCompleted=False, scientificallyValidated=False,
        actualSavedDynamicTimesS=[0, .5, 1, 1.5, 2], actualParticleCount=105,
        lastUpperCohortCentroidDisplacementM=last['upperCohortCentroidDisplacementM'],
        lastMaximumDisplacementFromReleaseM=last['maximumDisplacementFromReleaseM'],
        lastConnectedMovingFractionOfUpperCohortMass=last['connectedMovingFractionOfUpperCohortMass'],
        lastMaximumStrengthDamage=last['maximumStrengthDamage'], minimumSavedJ=min(s['minJ'] for s in report['states']),
        observed='Upper body lowers and spreads downslope across coherent mass, not an isolated outlier or colour-only change',
        toeRunoutMetricUsable=False, toeRunoutClaim='NOT_EVALUATED: original metric includes foundation already past toe at release; no runout claim',
        releaseEvent='At dynamic0s actual dt0 material switch already gives lower-foundation D_s up to0.3755; not elapsed dynamics',
        limitations='h2m/PPC1/105MP; fixed3s non-equilibrated preparation; partial native failure later2.5s; not physical calibration or fracture opening'))
    put(DEST / 'verification.json', dict(sourceFilesOriginalVerified=len(source_rows), selectedSourceFilesArchived=len(source_rows),
        fullSourceArchiveMembers=archives[0]['count'], loadedFaslInputsVerified=len(fasls), actualMappedDll=dll,
        currentOriginalSourceDifferences=current_differences,
        openblasThreadsRecorded=provenance.get('openblasThreads'), ompThreadsRecorded=provenance.get('ompThreads'),
        savedReviewActualExitCode=2, partialSavedIntegrity='PASS', nativeAndWorkerExitCodes=[1, 1],
        sourceArchiveCopiesPerNativeAttempt=1, sourceArchiveNotDuplicatedFromFull001=True,
        originalVideoDecodedFrames=5, slowVideoDecodedFrames=5, slowVideoDecodeExitCode=0,
        noSolverReviewOrRenderRepeated=True, gitStaged=False, gitBlobVerification='NOT_EXECUTED: root owns staging/blob proof'))
    put(DEST / 'closure.json', dict(createdUtc=datetime.now(timezone.utc).isoformat(),
        scope='Human-authorized rough unnotched40degree MC strength-damage demo: coherent early bulk motion observed; actual partial failure retained',
        requestedDynamicSeconds=20, actualSavedLastDynamicSeconds=2, attemptedUnsavedDynamicSeconds=2.5,
        actualNativeClockAtFailureS=5.5, savedDynamicFrames=5, particleRows=525,
        failedStateOrExactPredicateReconstructed=False,
        failure='Actual owned output guard ID55; absent failed frame tuple prevents determining its exact failing predicate',
        priorNegative='001 wrapper parameter EvidenceDirectory rejected before native launch; no native001 source snapshot invented',
        invalidRunoutMetric='Original first review retained unchanged; total mass past toe includes pre-existing foundation; unusable for a runout claim',
        preparedObserverFrozenBeforeSavedReview=True, nativeAnalysisTiming='See original launch-preparation and review analysis-freeze records; no invented stronger timing claim',
        media='5 actual saved states; original6fps and slowed1fps/5s; no interpolation or modified frames',
        mediaFilesIndexed=3, fullSourceArchives=1, archives=len(archives), archiveMembers=sum(a['count'] for a in archives)))
    put(DEST / 'archive-members.json', archives)
    put(DEST / 'copy-verification.json', dict(records=copies, byteIdenticalCopies=len(copies)))
    indexed = [record(p) for p in sorted(DEST.rglob('*')) if p.is_file()]
    put(DEST / 'evidence-manifest.json', dict(files=indexed, indexedFiles=len(indexed), excludedSelf='evidence-manifest.json'))
    for row in indexed:
        assert record(DEST / row['path']) == row
    print(json.dumps(dict(packet=str(DEST), indexedFiles=len(indexed), totalFiles=len(indexed)+1, archives=len(archives),
        decodedArchiveMembers=sum(a['count'] for a in archives), originalSourceFilesVerified=len(source_rows),
        fullSourceArchiveMembers=archives[0]['count'], loadedFaslInputsVerified=len(fasls), mediaFilesIndexed=3, gitStaged=False)))


if __name__ == '__main__':
    main()
