"""Prepare pre-launch bytes, then package ONE separately captured live proof.

No launcher or process query is invoked by this Python helper. Root must approve
the launch, run the generated PowerShell proof ONCE, then select --capture.
"""
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'output/mc-composite-apex-2026-10-26'
NAME = 'srf1p6-composite-001'
RUN = RAW / NAME
STAGE = RAW / (NAME + '-launch-preparation')
PACKET = ROOT / 'docs/evidence/unnotched-gravity-2026-10-26' / (NAME + '-launch')
CASE = ROOT / 'cases/benchmarks/gravity-slope-mc-composite-apex-srf-1p6.lisp'
CONTRACT = ROOT / 'research/references/unnotched-mc-ssr/composite-apex-srf1p6-contract.json'
NATIVE_GATE = RAW / 'scenario-controls-001'
SAVED_GATE = RAW / 'scenario-controls-003'
FRAMEWORK_GATE = RAW / 'framework-output-002'
HELPER = ROOT / '.tmp/pack-gravity-completed-002.py'
CAPTURE_REFERENCE = ROOT / '.tmp/capture-gravity-srf1p6-processes.ps1'
GATE_CASE = NATIVE_GATE / 'source/inputs/cases/gravity-slope-mc-composite-apex-srf-1p6.lisp'


def helpers():
    spec = importlib.util.spec_from_file_location('_launch_copy_hash_zip_only', HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # Definitions only; guarded main never runs.
    module.PACKET = PACKET
    return module


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def git(*arguments):
    return subprocess.run(['git', *arguments], cwd=ROOT, check=True, capture_output=True).stdout


def verify_index(path, h):
    index = h.read_json(path)
    for row in index['artifacts']:
        source = (path.parent / row['path']).resolve()
        require(source.is_relative_to(path.parent.resolve()), 'Gate artifact escapes packet')
        actual = h.record(source)
        require(actual['sha256'] == row['sha256'] and actual['bytes'] == row['bytes'], 'Gate artifact bytes differ')


def numerical_member(path):
    return (path.startswith(('source/src/', 'source/materials/', 'source/scenarios/', 'source/framework/'))
            or path.endswith('.asd') or path == 'source/libs/kirchoff.dll'
            or path in ('source/run-case.lisp', 'source/scripts/lisp/native-source-snapshot.lisp'))


def checkpoint_text_binding(source, commit, h):
    """Retain checkout bytes; accept only proven Git CRLF/LF equivalence."""
    relative = source.relative_to(ROOT).as_posix()
    blob = git('show', commit + ':' + relative)
    payload = source.read_bytes()
    blob_id = git('rev-parse', commit + ':' + relative).decode().strip()
    filtered_id = git('hash-object', '--path=' + relative, relative).decode().strip()
    raw_equal = blob == payload
    if not raw_equal:
        # Text and byte-normalization checks prevent accepting arbitrary Git
        # filters or content changes merely because hash-object matches.
        blob.decode('utf-8')
        payload.decode('utf-8')
        require(b'\x00' not in blob and b'\x00' not in payload
                and blob.replace(b'\r\n', b'\n') == payload.replace(b'\r\n', b'\n')
                and filtered_id == blob_id,
                'Pre-launch text differs beyond Git-proven line endings: ' + relative)
    require(filtered_id == blob_id, 'Git hash-object --path differs from checkpoint: ' + relative)
    return {'repositoryPath': relative, 'sourceCommit': commit, 'headGitBlobSha': blob_id,
            'gitHashObjectWithPathSha': filtered_id, 'headBlobSha256': hashlib.sha256(blob).hexdigest(),
            'headBlobBytes': len(blob), 'worktreeBytes': len(payload),
            'worktreeSha256': h.record(source)['sha256'], 'rawGitBlobEqualsWorktree': raw_equal,
            'crlfLfEquivalenceAccepted': not raw_equal,
            'scope': 'Exact runtime copies retain worktree bytes. Git blob identity and line-ending equivalence are recorded separately, never claimed byte-identical when false.'}


def process_source():
    old = CAPTURE_REFERENCE.read_text(encoding='utf-8-sig')
    old_run = 'output/unnotched-gravity-2026-10-25/srf1p6-001'
    require(old.count(old_run) == 1, 'Reference process helper shape changed')
    body = old.replace(old_run, RUN.relative_to(ROOT).as_posix(), 1).splitlines()
    require(body[0] == "$ErrorActionPreference='Stop'" and body[1].startswith('$taskRun='),
            'Unexpected reference helper header')
    return ('# Generated before launch; ONE new-run live query, exact original creation clocks.\n'
        + body[0] + '\n' + body[1] + '\n'
        + '$taskProof=$taskRun+"-live-process-verification.json"\n'
        + '$taskFailure=$taskRun+"-live-proof-failure.json"\n'
        + 'if((Test-Path -LiteralPath $taskProof) -or (Test-Path -LiteralPath $taskFailure)) { throw "Preserve the first actual live capture; no repeated query." }\n'
        + 'try {\n' + '\n'.join(body[2:]) + '\n} catch {\n'
        + '  [ordered]@{status="FAILED_LIVE_CAPTURE";capturedUtc=[DateTime]::UtcNow.ToString("o");error=$_.Exception.Message;scope="Actual single live capture failed; no process identity or completion invented"} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $taskFailure -Encoding utf8\n'
        + '  throw\n}\n')


def prepare(args, h):
    require(not RUN.exists() and not STAGE.exists(), 'Preparation must be fresh and precede the native run')
    require(not Path(str(RUN) + '-launch.json').exists(), 'Launch already exists; cannot claim pre-launch freezing')
    require(args.gate_index is not None, '--prepare requires the committed gate artifact-index')
    gate_index = args.gate_index.resolve()
    require(gate_index.is_relative_to((ROOT / 'docs/evidence').resolve()), 'Gate index must be workspace evidence')
    commit = git('rev-parse', 'HEAD').decode().strip()
    branch = git('branch', '--show-current').decode().strip()
    require(branch != 'main', 'Do not prepare this experiment on main')
    verify_index(gate_index, h)
    require(git('show', commit + ':' + gate_index.relative_to(ROOT).as_posix()) == gate_index.read_bytes(),
            'Archive checkpoint must commit the exact gate index before preparation')
    gate = h.read_json(NATIVE_GATE / 'result.json')
    saved = h.read_json(SAVED_GATE / 'result.json')
    framework = h.read_json(FRAMEWORK_GATE / 'result.json')
    require({'strict-default', 'optional-input', 'reject-hidden-inputs', 'short-output'} <= set(gate['passedGroups'])
            and gate['physicalUpdatesExecuted'] == 2
            and gate['materialCallsAccepted'] == gate['materialCallsAttempted'] == 1760,
            'Native construction/input/two-update gate is incomplete')
    require(saved['passed'] is True and {'saved-output', 'read-only'} <= set(saved['passedGroups'])
            and saved['physicalUpdatesExecuted'] == 0, 'Saved-only gate003 must pass first')
    require(framework['passed'] is True and framework['physicalUpdatesExecuted'] == 2,
            'Optional framework output002 must pass first')
    require(CASE.read_bytes() == GATE_CASE.read_bytes(), 'New full case differs from executed native gate input')
    contract = h.read_json(CONTRACT)
    config = h.read_json(NATIVE_GATE / 'observations/manifest.json')['config']
    expected = dict(config)
    expected.update(duration=contract['numerics']['durationS'],
        gravityRampDuration=contract['gravity']['rampDurationS'],
        frames=contract['numerics']['frames'], maxUpdates=contract['numerics']['maxUpdates'])
    require(expected['strengthReductionFactor'] == 1.6 and expected['duration'] == 6
            and expected['frames'] == 61 and expected['gravityRampDuration'] == 2,
            'Unexpected preregistered full experiment')
    files = [(CASE, 'case.lisp'), (CONTRACT, 'protocol/' + CONTRACT.name),
             (ROOT / 'scripts/review-gravity-composite-apex.py', 'analysis/review-gravity-composite-apex.py'),
             (ROOT / 'scripts/review-gravity-slope.py', 'analysis/review-gravity-slope.py'),
             (ROOT / 'scripts/plot_m5_cliff_comparison.py', 'analysis/plot_m5_cliff_comparison.py')]
    for name in ('PERFECT_MC_APEX_PLAN.md', 'PERFECT_MC_APEX_REVIEW.md'):
        files.append((ROOT / 'research/notes/unnotched-landslide-2026-10-24' / name, 'protocol/' + name))
    checkpoint_bindings = [checkpoint_text_binding(source, commit, h) for source, _ in files]
    STAGE.mkdir(parents=True)
    records = []
    for source, relative in files + [(Path(__file__), 'capture-helper.py'), (HELPER, 'copy-hash-zip-helpers.py'),
                                    (CAPTURE_REFERENCE, 'proof-support/reference-exact-clock-helper.ps1')]:
        target = STAGE / relative
        h.copy(source, target)
        records.append({**h.record(target, STAGE), 'originalPath': str(source)})
    capture = STAGE / 'proof-support/capture-processes.ps1'
    capture.write_text(process_source(), encoding='utf-8', newline='\n')
    records.append({**h.record(capture, STAGE), 'originalPath': 'Generated from exact-clock reference before launch'})
    h.write_json(STAGE / 'expected-full-configuration.json', expected)
    h.write_json(STAGE / 'prelaunch-snapshot.json', {
        'status': 'PREPARED_NOT_LAUNCHED', 'preparedUtc': datetime.now(timezone.utc).isoformat(),
        'sourceCommit': commit, 'branch': branch, 'run': str(RUN), 'case': str(CASE),
        'maxWallHours': 1, 'budgetScope': 'Provisional one-hour wall budget; not physical duration or a runtime guarantee',
        'gateArtifactIndex': h.record(gate_index), 'gateIndexRawGitBlobBytesEqual': True,
        'checkpointTextBindings': checkpoint_bindings, 'frozenFiles': records,
        'nativeGate': str(NATIVE_GATE), 'savedOnlyGate': str(SAVED_GATE),
        'frameworkGate': str(FRAMEWORK_GATE), 'expectedPhysicalDurationS': 6, 'expectedFrames': 61,
        'scope': 'No launcher/native/test/replay/research/process query. Root must explicitly authorize launch and one generated live proof.'})
    print(json.dumps({'stage': str(STAGE), 'sourceCommit': commit, 'preparedFiles': len(records),
        'next': 'After root-authorized launch only, run proof-support/capture-processes.ps1 ONCE, then this helper --capture'}, indent=2))


def capture(h):
    require(not PACKET.exists(), 'Launch packet must be fresh; preserve previous attempt')
    prep = h.read_json(STAGE / 'prelaunch-snapshot.json')
    require(Path(__file__).read_bytes() == (STAGE / 'capture-helper.py').read_bytes()
            and HELPER.read_bytes() == (STAGE / 'copy-hash-zip-helpers.py').read_bytes(),
            'Collector/helper changed after pre-launch freezing')
    for row in prep['frozenFiles']:
        actual = h.record(STAGE / row['path'], STAGE)
        require(actual['sha256'] == row['sha256'] and actual['bytes'] == row['bytes'], 'Pre-launch bytes changed')
    status = h.read_json(Path(str(RUN) + '-status.json'))
    launch = h.read_json(Path(str(RUN) + '-launch.json'))
    worker = h.read_json(Path(str(RUN) + '-detached/worker-start.json'))
    live = h.read_json(Path(str(RUN) + '-live-process-verification.json'))
    require(status['sourceCommit'] == launch['sourceCommit'] == live['sourceCommit'] == prep['sourceCommit'],
            'Actual native launch differs from prepared checkpoint')
    require(launch['maxWallHours'] == prep['maxWallHours'] == 1, 'Wall budget differs from prepared plan')
    started = datetime.fromisoformat(launch['startedUtc'].replace('Z', '+00:00'))
    deadline = datetime.fromisoformat(launch['wallDeadlineUtc'].replace('Z', '+00:00'))
    require((deadline - started).total_seconds() == 3600, 'Recorded wall deadline differs from one-hour budget')
    require(started > datetime.fromisoformat(prep['preparedUtc']), 'Preparation did not precede native launch')
    require(Path(launch['case']).resolve() == CASE.resolve()
            and launch['caseSha256'].lower() == h.record(STAGE / 'case.lisp')['sha256'],
            'Actual launch request case/path differs from frozen plan')
    roles = {row['role']: row for row in live['processes']}
    require(len(live['processes']) == len(roles) == 4
            and set(roles) == {'wrapper', 'nativeCommand', 'sbcl', 'detachedWorker'}, 'Incomplete live role proof')
    for role in ('wrapper', 'nativeCommand', 'sbcl'):
        expected, actual = status['processIdentity'][role], roles[role]
        require(actual['identityMatched'] is True and actual['creationClock'] == 'System.Diagnostics.Process'
                and actual['pid'] == expected['pid'] and actual['sessionId'] == expected['sessionId']
                and actual['creationUtc'] == expected['createdUtc'], 'Exact native process identity differs')
    detached = roles['detachedWorker']
    require(detached['identityMatched'] is True and detached['creationClock'] == 'Win32_Process'
            and detached['pid'] == worker['processId'] and detached['sessionId'] == worker['sessionId']
            and detached['creationUtc'] == worker['creationUtc'], 'Exact worker CIM identity differs')
    require(roles['wrapper']['parentPid'] == detached['pid']
            and roles['nativeCommand']['parentPid'] == roles['wrapper']['pid']
            and roles['sbcl']['parentPid'] == roles['nativeCommand']['pid'], 'Actual parent chain differs')
    spec = importlib.util.spec_from_file_location('_frozen_launch_runtime_schema', STAGE / 'analysis/review-gravity-composite-apex.py')
    review = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(review)
    proof = review.verify_native_sources(RUN)  # Source/runtime metadata only; no saved-state or material analysis.
    source_rows = h.read_json(RUN / 'source/source-manifest.json')['files']
    rows = {row['path']: row for row in source_rows}
    gate_rows = {row['path']: row for row in h.read_json(NATIVE_GATE / 'source/source-manifest.json')['files']}
    current_numerics = {key for key in rows if numerical_member(key)}
    gate_numerics = {key for key in gate_rows if numerical_member(key)}
    require(current_numerics == gate_numerics, 'Numerical source set changed since native gate')
    require(all(rows[key]['sha256'] == gate_rows[key]['sha256'] for key in current_numerics),
            'Numerical source bytes changed since native gate')
    require((RUN / 'source/case.lisp').read_bytes() == (STAGE / 'case.lisp').read_bytes() == GATE_CASE.read_bytes(),
            'Executed full case differs from prepared/gated case')
    captured = h.read_json(RUN / 'manifest.json')
    expected = h.read_json(STAGE / 'expected-full-configuration.json')
    require(captured['config'] == expected and captured['particleCount'] == 880, 'Full input configuration differs from gated/prepared plan')
    require(captured.get('materialVariant') == 'perfect-mc-composite-apex'
            and captured.get('notchCount') == captured.get('driverCount') == 0
            and captured.get('massScale') == 1 and captured.get('damping') == 0, 'Wrong actual material/loading metadata')
    PACKET.mkdir(parents=True)
    (PACKET / '.gitattributes').write_bytes(b'* -text\n*.zip binary\n')
    h.copy(Path(__file__), PACKET / 'executed-capture-helper.py')
    for name, source in h.tree_files(STAGE).items():
        h.copy(source, PACKET / 'prelaunch' / name)
    for name in ('manifest.json', 'source-provenance.json'):
        h.copy(RUN / name, PACKET / name)
    h.copy(RUN / 'source/source-manifest.json', PACKET / 'metadata/native-source-manifest-index.json')
    members = {row['path']: RUN / row['path'] for row in source_rows}
    members['source/source-manifest.json'] = RUN / 'source/source-manifest.json'
    archive = h.archive('complete-native-source-at-launch', members)
    for source in sorted(RAW.glob(NAME + '*')):
        if source.is_file():
            h.copy(source, PACKET / 'runtime' / source.name)
    for name, source in h.tree_files(Path(str(RUN) + '-detached')).items():
        h.copy(source, PACKET / 'detached' / name)
    h.write_json(PACKET / 'archive-member-verification.json', {'archives': [archive],
        'nativeSourceEntries': len(source_rows), 'allCrcAndDecodedPayloadChecksPassed': True})
    h.write_json(PACKET / 'summary.json', {
        'status': 'LAUNCH_PROOF_ONLY', 'createdUtc': datetime.now(timezone.utc).isoformat(),
        'nativeSourceCommit': prep['sourceCommit'], 'actualSourceFiles': len(source_rows),
        'preparedBeforeLaunch': started > datetime.fromisoformat(prep['preparedUtc']),
        'startedUtc': launch['startedUtc'], 'wallDeadlineUtc': launch['wallDeadlineUtc'], 'maxWallHours': 1,
        'actualRuntimeProof': proof, 'actualLiveProof': live, 'numericalFilesMatchingNativeGate': len(current_numerics),
        'fullConfigurationMatchesGateExceptDeclaredFourTinyOverrides': True,
        'actualCapturedState': {key: captured.get(key) for key in ('status', 'phase', 'complete', 'timeS', 'updates', 'savedFrames')},
        'landslideVerified': False, 'scientificallyValidated': False,
        'limits': 'Stored live proof is timestamp-specific; capture file moments are not atomic. User-session worker has no proved sleep/logoff/reboot immunity. Launch proof is not completion or a physical result.',
        'operations': 'Read/copy/hash/ZIP/CRC only after the separately authorized single exact-clock capture. No launcher, process re-query, native/test/replay/saved-state analysis or renderer invoked by this Python helper.'})
    (PACKET / 'README.md').write_text('# Optional composite SRF1.6: launch evidence\n\n'
        'The case, declared variant contract, reviewer/base/reader and exact-clock capture source were frozen '
        'after the committed gate archive and before root-authorized launch. Actual full configuration matches '
        'the native tiny gate apart from duration/ramp/frame count/update cap; all numerical sources and DLL '
        'match that gate. The one-source-manifest ZIP carries every actual native source payload. '
        'Exact worktree/runtime bytes are authoritative; per-file checkpoint bindings separately record raw '
        'Git byte equality, Git blob SHA and Git hash-object --path. A raw mismatch is permitted only for '
        'UTF-8 CRLF/LF-equivalent text whose filtered Git hash equals HEAD; it is never called byte-identical. '
        'The committed gate artifact-index still requires exact raw Git bytes.\n\n'
        'Stored PID/session/creation-clock/parent proof is a single timestamp observation, not a current-process '
        'or survival guarantee. Native Process clocks and the worker CIM clock are compared separately. '
        'The Python collector performs no process query or launch. This packet proves no slope failure, '
        'runout, paper agreement or scientific validation.\n', encoding='utf-8', newline='\n')
    artifacts = [h.record(path, PACKET) for path in sorted(PACKET.rglob('*')) if path.is_file()]
    h.write_json(PACKET / 'artifact-index.json', {'schema': 'cl-mpm.evidence.artifact-index.v1',
        'artifacts': artifacts, 'note': 'Index excludes itself; direct native-source-manifest-index is metadata only; complete payload is in the verified ZIP.'})
    for row in artifacts:
        require(h.record(PACKET / row['path'], PACKET) == row, 'Final indexed bytes changed')
    print(json.dumps({'packet': str(PACKET), 'indexedArtifacts': len(artifacts),
        'sourceFilesVerified': len(source_rows), 'zipMembers': archive['decodedMembers'],
        'status': 'LAUNCH_PROOF_ONLY', 'processesRequeriedByPython': False}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--prepare', action='store_true')
    modes.add_argument('--capture', action='store_true')
    parser.add_argument('--gate-index', type=Path)
    args = parser.parse_args()
    h = helpers()
    if args.prepare:
        prepare(args, h)
    else:
        capture(h)


if __name__ == '__main__':
    main()
