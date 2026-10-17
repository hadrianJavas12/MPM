"""Prepare/verify an immutable old-source, fresh 4 s Joss baseline; never run SBCL.

Normal execution copies manifest-bound payload bytes into a NEW evidence root,
adds exact path mirrors needed by the old CLI, and writes a separate launcher.
--verify-only verifies that prepared input; it does not launch a simulation.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'output/architecture-migration-2026-10-16/native-freeze/triaxial-short-002'
DEST = ROOT / 'output/architecture-migration-2026-10-16/joss-bounded'
CASE = ROOT / 'tests/cases/joss-serial-integration.lisp'
BOOTSTRAP = ROOT / 'scripts/lisp/run-frozen-joss-baseline.lisp'
OLD_COMMIT = 'a99a4e1d1a8deb17483230ee59d53c07f4a26822'

def sha(value):
    return hashlib.sha256(value).hexdigest()

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

def relative_path(value):
    rel = PurePosixPath(value.replace('\\', '/'))
    if rel.is_absolute() or '..' in rel.parts or '.native-cache' in rel.parts:
        raise RuntimeError('Unsafe/non-payload path: ' + value)
    return rel

def launcher_text(attempt='before-001', bootstrap='run-original-bootstrap.lisp', retry=False):
    launcher = r'''param([Parameter(Mandatory=$true)][string]$ExecutionCheckpoint)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath 'D:/MPM'
$taskRoot = 'D:/MPM/output/architecture-migration-2026-10-16/joss-bounded'
$taskPrefix = Join-Path $taskRoot 'before-001'
if (Test-Path -LiteralPath ($taskPrefix + '-launch.json')) { throw 'Refusing duplicate baseline launch' }
if (Test-Path -LiteralPath $taskPrefix) { throw 'Baseline output must be fresh/nonexistent' }
& 'D:/MPM/toolchain/analysis-venv/Scripts/python.exe' 'D:/MPM/scripts/prepare-joss-bounded-baseline.py' --verify-only
if ($LASTEXITCODE -ne 0) { throw 'Prepared baseline input verification failed' }
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$env:CL_MPM_REFERENCE_PNG = '0'
$taskRecord = [ordered]@{
  startedUtc=[DateTime]::UtcNow.ToString('o'); bootstrapRepositoryCheckpoint=$ExecutionCheckpoint
  numericalSourceBaselineCommit='a99a4e1d1a8deb17483230ee59d53c07f4a26822'
  sourceIdentity='Original manifest-bound payload copied into original-root, then old CLI re-copies/guards/compiles it in this fresh run'
  caseCommitReported='9568b8e'; workers=1; requestedPhysicalTimeS=4; frameCap=10
  openblasThreads=1; ompThreads=1; pngEnabled=$false; wrapperPid=$PID
  scope='Fresh bounded serial initiation control; not full collapse/run-out, not restarted cancelled run'
}
$taskRecord | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath ($taskPrefix + '-launch.json') -Encoding utf8
try {
  $taskCommand = 'call "D:/MPM/windows/cl-mpm.cmd" "' + (Join-Path $taskRoot 'run-original-bootstrap.lisp') + '" "' + (Join-Path $taskRoot 'original-root') + '" "' + (Join-Path $taskRoot 'joss-serial-integration.lisp') + '" "' + $taskPrefix + '"'
  $taskNative = Start-Process -FilePath 'cmd.exe' -ArgumentList @('/d','/c',$taskCommand) -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput ($taskPrefix + '.stdout.log') -RedirectStandardError ($taskPrefix + '.stderr.log')
  $taskRecord.nativeExitCode=$taskNative.ExitCode
  $taskRecord.stdoutPath=$taskPrefix + '.stdout.log'
  $taskRecord.stderrPath=$taskPrefix + '.stderr.log'
  $taskMetadataPath = Join-Path $taskPrefix 'reference-metadata.json'
  if (Test-Path -LiteralPath $taskMetadataPath) {
    $taskMetadata = Get-Content -Raw -LiteralPath $taskMetadataPath | ConvertFrom-Json
    $taskRecord.simulationComplete=$taskMetadata.complete
    $taskRecord.physicalTime=$taskMetadata.physicalTime
    $taskRecord.termination=$taskMetadata.termination
  }
  $taskRecord.endedUtc=[DateTime]::UtcNow.ToString('o')
  $taskRecord | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath ($taskPrefix + '-status.json') -Encoding utf8
  exit $taskRecord.nativeExitCode
} catch {
  $taskRecord.wrapperError=$_.Exception.Message
  $taskRecord.nativeExitCode=$null
  $taskRecord.endedUtc=[DateTime]::UtcNow.ToString('o')
  $taskRecord | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath ($taskPrefix + '-status.json') -Encoding utf8
  throw
}
'''
    launcher = launcher.replace("'before-001'", repr(attempt)).replace('run-original-bootstrap.lisp', bootstrap)
    if retry:
        launcher = launcher.replace(' --verify-only\n', ' --verify-retry\n')
    return launcher

def verify():
    proof = json.loads((DEST / 'preparation.json').read_text(encoding='utf-8'))
    for record in proof['prepared_files']:
        target = DEST / relative_path(record['destination'])
        actual = target.read_bytes()
        if len(actual) != record['bytes'] or sha(actual) != record['sha256']:
            raise RuntimeError('Prepared bytes changed: ' + record['destination'])
    original_manifest = BASE / 'source/source-manifest.json'
    if sha(original_manifest.read_bytes()) != proof['original_manifest_sha256']:
        raise RuntimeError('Original source manifest changed.')
    manifest = json.loads(original_manifest.read_text(encoding='utf-8'))
    for row in manifest['files']:
        value = (BASE / relative_path(row['path'])).read_bytes()
        if len(value) != row['bytes'] or sha(value) != row['sha256']:
            raise RuntimeError('Original evidence payload changed: ' + row['path'])
    return proof

def prepare():
    if DEST.exists() and any(DEST.iterdir()):
        raise RuntimeError('Refusing existing/nonempty bounded baseline root: ' + str(DEST))
    original_manifest = BASE / 'source/source-manifest.json'
    manifest_bytes = original_manifest.read_bytes()
    manifest = json.loads(manifest_bytes)
    old_launch = json.loads((BASE.parent / (BASE.name + '-launch.json')).read_text(encoding='utf-8-sig'))
    if old_launch['sourceCommitAtLaunch'] != OLD_COMMIT:
        raise RuntimeError('Frozen baseline launch attribution differs from the reviewed a99 source.')
    # Read and verify every source before writing any copy; no cache/provenance
    # file is selected simply because it exists under the old source directory.
    selected = []
    for row in manifest['files']:
        rel = relative_path(row['path'])
        if not rel.parts or rel.parts[0] != 'source':
            raise RuntimeError('Unexpected manifest payload root: ' + row['path'])
        value = (BASE / rel).read_bytes()
        if len(value) != row['bytes'] or sha(value) != row['sha256']:
            raise RuntimeError('Frozen source hash mismatch: ' + row['path'])
        selected.append((PurePosixPath(*rel.parts[1:]), value, row))
    if len({rel for rel, _, _ in selected}) != len(selected):
        raise RuntimeError('Duplicate old payload path.')
    case_bytes = CASE.read_bytes()
    for token in (b':workers 1', b':simulation-time 4d0', b':frames 10',
                  b'studio/reference/joss-bay-accepted-collapse.json'):
        if token not in case_bytes:
            raise RuntimeError('Trusted case no longer specifies the approved bounded serial recipe.')
    bootstrap_bytes = BOOTSTRAP.read_bytes()
    DEST.mkdir(parents=True, exist_ok=True)
    prepared = []; mirror_count = 0
    def copy_exact(destination, value, origin, kind):
        target = DEST / relative_path(destination)
        if target.exists():
            raise RuntimeError('Unexpected duplicate destination: ' + destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value)
        if target.read_bytes() != value:
            raise RuntimeError('Copy equality failed: ' + destination)
        prepared.append({'destination': destination, 'origin': origin, 'kind': kind,
                         'bytes': len(value), 'sha256': sha(value)})
    for rel, value, row in selected:
        copy_exact('original-root/' + rel.as_posix(), value, row['path'], 'original-manifest-payload')
    for rel, value, row in selected:
        mirror = None
        if rel.parts[0] == 'inputs':
            mirror = PurePosixPath(*rel.parts[1:]).as_posix()
        elif rel.parts[:2] == ('bootstrap', 'windows'):
            mirror = PurePosixPath(*rel.parts[1:]).as_posix()
        elif rel.as_posix() == 'run-case.lisp':
            mirror = 'scripts/run-case.lisp'
        if mirror:
            copy_exact('original-root/' + mirror, value, row['path'], 'byte-identical-path-mirror')
            mirror_count += 1
    copy_exact('joss-serial-integration.lisp', case_bytes, CASE.relative_to(ROOT).as_posix(),
               'new-trusted-4s-case-reported-commit-9568b8e')
    copy_exact('run-original-bootstrap.lisp', bootstrap_bytes, BOOTSTRAP.relative_to(ROOT).as_posix(),
               'new-launch-adapter-no-numerical-body')
    launcher = launcher_text()

    (DEST / 'run-original.ps1').write_text(launcher, encoding='utf-8')
    copy_exact('original-source-manifest.json', manifest_bytes,
               str(original_manifest.relative_to(ROOT)), 'original-manifest-copy-not-executed-source')
    proof = {'createdUtc': dt.datetime.now(dt.timezone.utc).isoformat(),
             'status': 'PREPARED_NATIVE_NOT_RUN', 'sourceRun': str(BASE.relative_to(ROOT)),
             'numericalSourceBaselineCommit': OLD_COMMIT, 'trustedCaseCommitReported': '9568b8e',
             'original_manifest_sha256': sha(manifest_bytes), 'payload_file_count': len(selected),
             'path_mirror_count': mirror_count, 'prepared_files': prepared,
             'bootstrap': 'Actual main windows/init.lisp first, then bind *cl-mpm-root* to copied original-root and load its old run-case.lisp. Third-party dependencies remain external.',
             'mainWindowsInitSha256AtPreparation': sha((ROOT / 'windows/init.lisp').read_bytes()),
             'helperSha256AtPreparation': sha(Path(__file__).read_bytes()),
             'rendering': 'PNG disabled consistently for bounded comparison; no plot PASS claim.',
             'excluded': ['.native-cache/**', 'old generated provenance/manifests except this separate source-manifest copy'],
             'limits': ['Original manifest has 144 payload records; do not invent a 147-record payload.',
                        'No native command was launched during preparation; fresh-run DLL/private-FASL/source proof remains pending.',
                        'Bounded four-second initiation evidence does not complete full G3 or scientific validation.',
                        'The user-cancelled full Joss run remains stopped; this is a distinct fresh bounded control.']}
    write_json(DEST / 'preparation.json', proof)
    verify()
    return proof


def prepare_retry(attempt='before-002'):
    if not attempt.startswith('before-') or not attempt[7:].isdigit():
        raise RuntimeError('Retry attempt must have the form before-NNN.')
    original = verify()
    retry_launcher = 'run-original-retry.ps1' if attempt == 'before-002' else attempt + '-run.ps1'
    for relative in (attempt + '-preparation.json', attempt + '-bootstrap.lisp',
                     retry_launcher, attempt, attempt + '-launch.json'):
        if (DEST / relative).exists():
            raise RuntimeError('Refusing retry overwrite: ' + relative)
    bootstrap = BOOTSTRAP.read_bytes()
    launcher = launcher_text(attempt, attempt + '-bootstrap.lisp', retry=True)
    launcher = launcher.replace(' --verify-retry\n', ' --verify-retry --attempt ' + attempt + '\n').encode()
    (DEST / (attempt + '-bootstrap.lisp')).write_bytes(bootstrap)
    (DEST / retry_launcher).write_bytes(launcher)
    # The old path guard resolves registry roots even when no Studio system is
    # selected. Supply its empty directory; never substitute source or methods.
    (DEST / 'original-root/studio/lisp').mkdir(parents=True, exist_ok=True)
    proof = {'status': 'PREPARED_NATIVE_NOT_RUN', 'attempt': attempt,
             'createdUtc': dt.datetime.now(dt.timezone.utc).isoformat(),
             'originalPreparationSha256': sha((DEST / 'preparation.json').read_bytes()),
             'numericalSourceBaselineCommit': OLD_COMMIT,
             'payload_file_count': original['payload_file_count'],
             'path_mirror_count': original['path_mirror_count'],
             'prepared_files': [
                 {'destination': attempt + '-bootstrap.lisp', 'bytes': len(bootstrap), 'sha256': sha(bootstrap)},
                 {'destination': retry_launcher, 'bytes': len(launcher), 'sha256': sha(launcher)}],
             'emptyRegistrySupportDirectories': ['original-root/studio/lisp/'],
             'harnessRepair': 'Pass old-root without a trailing command-line backslash; use cmd/Start-Process redirected logs and actual process exit code.',
             'before001': 'Failure/status/empty log and exact bootstrap argument diagnostic are retained unchanged. No old numerical source or physics parameter changed.'}
    write_json(DEST / (attempt + '-preparation.json'), proof)
    return verify_retry(attempt)

def verify_retry(attempt='before-002'):
    original = verify()
    proof = json.loads((DEST / (attempt + '-preparation.json')).read_text(encoding='utf-8'))
    if sha((DEST / 'preparation.json').read_bytes()) != proof['originalPreparationSha256']:
        raise RuntimeError('Original preparation changed after retry capture.')
    for row in proof['prepared_files']:
        value = (DEST / row['destination']).read_bytes()
        if len(value) != row['bytes'] or sha(value) != row['sha256']:
            raise RuntimeError('Retry harness bytes changed: ' + row['destination'])
    return proof

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--verify-only', action='store_true')
    group.add_argument('--prepare-retry', action='store_true')
    group.add_argument('--verify-retry', action='store_true')
    parser.add_argument('--attempt', default='before-002')
    arguments = parser.parse_args()
    if arguments.prepare_retry:
        proof = prepare_retry(arguments.attempt)
    elif arguments.verify_retry:
        proof = verify_retry(arguments.attempt)
    else:
        proof = verify() if arguments.verify_only else prepare()
    print(json.dumps({'status': proof['status'], 'payloadFiles': proof['payload_file_count'],
                      'byteIdenticalMirrors': proof['path_mirror_count'],
                      'proof': str(DEST / (arguments.attempt + '-preparation.json' if arguments.prepare_retry or arguments.verify_retry else 'preparation.json')), 'nativeLaunched': False}))

if __name__ == '__main__':
    main()
