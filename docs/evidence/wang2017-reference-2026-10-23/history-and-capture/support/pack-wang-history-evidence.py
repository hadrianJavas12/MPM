"""One-off collector: immutable completed controls; no active solver output."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
COHORT = ROOT / 'output/wang2017-reference-2026-10-23'
DEST = ROOT / 'docs/evidence/wang2017-reference-2026-10-23/history-and-capture'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def archive(path, folder):
    with path.open('wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode='w') as target:
            for source in sorted(folder.rglob('*')):
                if not source.is_file() or '.native-cache' in source.parts:
                    continue
                data = source.read_bytes()
                entry = tarfile.TarInfo(source.relative_to(folder).as_posix())
                entry.size = len(data)
                entry.mtime = 0
                target.addfile(entry, io.BytesIO(data))

materials = read(COHORT / 'material-controls-001/status.json')
cli = read(COHORT / 'cli-controls-002/status.json')
assert materials['status'] == cli['status'] == 'PASS'
assert read(COHORT / 'material-controls-001/history.json')['controlsCount'] == 17
assert read(COHORT / 'material-controls-001/capture.json')['controlsCount'] == 7
assert cli['negativeExitCode'] == 1 and cli['capsulePresent']
assert cli['replayExitCode'] == cli['positiveExitCode'] == 0
assert read(COHORT / 'cli-controls-002/replay.json')['passed']
DEST.mkdir(parents=True, exist_ok=False)
(DEST / '.gitattributes').write_text('* -text -whitespace\n', encoding='utf-8')
for folder in ('history-001', 'material-controls-001', 'cli-controls-001', 'cli-controls-002'):
    archive(DEST / (folder + '.tar.gz'), COHORT / folder)
    for source in (COHORT / folder).glob('*'):
        if source.is_file():
            target = DEST / 'results' / folder / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
support = DEST / 'support'
support.mkdir()
shutil.copyfile(__file__, support / Path(__file__).name)
for relative in ('cl-mpm.asd', 'tests/materials/wang2017-history.lisp',
                 'tests/materials/mc-failure-capture.lisp', 'tests/materials/mc-evolution-points.lisp',
                 'scripts/replay-mc-failure.lisp'):
    target = support / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / relative, target)
summary = {
    'materialSourceCommit': materials['sourceCommit'], 'cliSourceCommit': cli['sourceCommit'],
    'historyControls': 17, 'captureControls': 7, 'legacyMCGroups': 34,
    'materialNativeExitCodes': materials['exits'],
    'cliNegativeExitCodeExpected': 1, 'cliReplayExitCode': 0, 'cliPositiveExitCode': 0,
    'initialHistoryControls': 16,
    'initialCLIFixture': 'FAILED_TEST_FIXTURE; exit0/no capsule, source5c6d6f7; retained, not counted PASS',
    'pointTestSourceIdentity': 'Committed db71b63; post-test sources retained. Focused point tests did not use pre-load source freezing.',
    'cliSourceIdentity': 'Actual pre-load copied bytes/manifests, ASDF and loaded DLL identity inside both run archives; private FASLs excluded.',
    'scope': 'Coordinate/law/replay/rollback and CLI infrastructure. Positive legacy MC smoke has two updates and one particle VTK.',
    'originalWangFailedStateCaptured': False, 'soil2ParticleImplemented': False,
    'fullReferenceCurveExecuted': False, 'scientificallyValidated': False,
}
(DEST / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
(DEST / 'README.md').write_text(
    '# Wang2017 history and MC failure-capture controls\n\n'
    'Actual Windows launcher results: 17 paper-history, 7 capture/replay and 34 MC regression groups PASS. '
    'Corrected frozen CLI: intentional rejection exit1 with exact JSON capsule, replay exit0, positive legacy MC smoke exit0. '
    'The initial negative CLI fixture did not reject and is retained as FAILED_TEST_FIXTURE; its state was not a capture PASS.\n\n'
    'Focused point-source attribution and full CLI source/DLL freezing have different scopes; see summary.json. '
    'Synthetic failure fixtures are labelled explicitly. These are not the missing original Wang failed update, '
    'a coupled Soil2 particle, a full slope curve, or scientific validation. No clamps/tolerance changes.\n', encoding='utf-8')
entries = [dict(path=p.relative_to(DEST).as_posix(), bytes=p.stat().st_size,
                sha256=hashlib.sha256(p.read_bytes()).hexdigest())
           for p in sorted(DEST.rglob('*')) if p.is_file()]
(DEST / 'evidence-manifest.json').write_text(json.dumps({'entries': entries}, indent=2) + '\n', encoding='utf-8')
assert all(hashlib.sha256((DEST / entry['path']).read_bytes()).hexdigest() == entry['sha256'] for entry in entries)
print(json.dumps({'verifiedArtifacts': len(entries), 'destination': str(DEST)}))
