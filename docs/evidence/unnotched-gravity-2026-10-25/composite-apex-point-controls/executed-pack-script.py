"""Package terminal new-model point controls: read/copy/hash/ZIP only.

Preparation is not execution. Invoke only after root reports native terminal.
Repeat --attempt for any retained failed and corrected attempts; no native or
analysis command is invoked, and an existing packet is never overwritten.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'output/unnotched-gravity-2026-10-25'
PLAN = ROOT / 'research/notes/unnotched-landslide-2026-10-24/PERFECT_MC_APEX_PLAN.md'
REVIEW = PLAN.with_name('PERFECT_MC_APEX_REVIEW.md')
PLAN_SHA = 'e21ba6e29a85890ae4ae56f0b24df0d644111f5c9b2e6d18d9fd6bc7a510d3c3'
STRICT_SOURCE = 'source/materials/models/plastic/mohr-coulomb-evolution/projection.lisp'
STRICT_SHA = 'e26b736914a8fa2cc3f4eb7f6619c1331e787f72d365d5bb7c0a5b3f4d8ceda1'


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def record(path, root=None):
    payload = Path(path).read_bytes()
    return {'path': Path(path).relative_to(root).as_posix() if root else str(path),
            'sha256': hashlib.sha256(payload).hexdigest(), 'bytes': len(payload)}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n',
                    encoding='utf-8', newline='\n')


def copy(source, destination):
    if destination.exists():
        raise RuntimeError(f'Refuse overwrite: {destination}')
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    if source.read_bytes() != destination.read_bytes():
        raise RuntimeError(f'Copy differs: {source}')


def terminal_exit(name):
    candidates = [RAW / (name + ending) for ending in ('.exit.json', '-exit.json')]
    found = [path for path in candidates if path.is_file()]
    if len(found) != 1:
        raise RuntimeError(f'Exactly one root terminal exit record required: {name}')
    value = read_json(found[0])
    if not isinstance(value.get('exitCode'), int):
        raise RuntimeError(f'No actual integer native exit code: {found[0]}')
    return found[0], value


def prepare_attempt(name):
    if Path(name).name != name or not name.startswith('composite-apex-point-'):
        raise RuntimeError('Only named new-model point-gate attempts are in scope')
    attempt = RAW / name
    exit_path, exit_value = terminal_exit(name)
    manifest_path = attempt / 'source/source-manifest.json'
    manifest = read_json(manifest_path)
    rows = manifest['files']
    expected = {row['path']: row for row in rows}
    if len(expected) != len(rows) or not expected:
        raise RuntimeError(f'Empty or duplicate source manifest: {name}')
    for relative, row in expected.items():
        path = (attempt / relative).resolve()
        if not path.is_relative_to((attempt / 'source').resolve()):
            raise RuntimeError(f'Source escapes snapshot: {relative}')
        actual = record(path)
        if (actual['sha256'], actual['bytes']) != (row['sha256'], row['bytes']):
            raise RuntimeError(f'Executed snapshot bytes changed: {name}/{relative}')
    if expected[STRICT_SOURCE]['sha256'] != STRICT_SHA:
        raise RuntimeError('Original strict projector changed unexpectedly')
    proofs = {}
    for phase in ('before', 'after'):
        proof_path = attempt / f'source-proof-{phase}.json'
        if not proof_path.exists():
            proofs[phase] = {'status': 'NOT_RETAINED',
                             'scope': 'Missing source proof is disclosed; no proof or PASS invented'}
            continue
        proof = read_json(proof_path)['files']
        if {row['path']: row['sha256'] for row in proof} != {
                path: row['sha256'] for path, row in expected.items()}:
            raise RuntimeError(f'Actual {phase} source hash proof differs: {name}')
        proofs[phase] = {'status': 'PASS', 'sourceFiles': len(proof)}
    runtime = {}
    for phase in ('before', 'after'):
        path = attempt / f'source-provenance-{phase}.json'
        if not path.exists():
            runtime[phase] = {'status': 'NOT_RETAINED'}
            continue
        value = read_json(path)
        backend = value['nativeBackend']
        if not (value['sourceSnapshotExactLoadedBytes'] and value['copiedByteEqualityBeforeLoad']):
            raise RuntimeError(f'Actual runtime source provenance is false: {name}/{phase}')
        if set(value['copiedFiles']) != set(expected):
            raise RuntimeError(f'Runtime source set differs: {name}/{phase}')
        if (backend['sha256'] != expected['source/libs/kirchoff.dll']['sha256']
                or backend['verifiedBy'] != 'GetModuleHandleW/GetModuleFileNameW'):
            raise RuntimeError(f'Mapped DLL differs: {name}/{phase}')
        runtime[phase] = {'status': 'PASS', 'nativeBackend': backend}
    result_path = attempt / 'result.json'
    result = read_json(result_path) if result_path.exists() else None
    passed = bool(result and result.get('passed') is True and exit_value['exitCode'] == 0)
    if passed:
        if result.get('failedGroups') or result.get('physicalUpdateAttempts') != 0:
            raise RuntimeError(f'PASS result contradicts failure/update fields: {name}')
        if result.get('oldOriginalFailureReplayCalls') != 0:
            raise RuntimeError('New model controls unexpectedly claim old-model replay')
        if not all(proofs[p]['status'] == runtime[p]['status'] == 'PASS' for p in ('before', 'after')):
            raise RuntimeError('Cannot package a PASS claim without full before/after source/runtime proof')
    adjacent = {path.name: path for path in sorted(RAW.iterdir())
                if path.is_file() and (path.name.startswith(name + '.') or path.name.startswith(name + '-'))}
    if exit_path.name not in adjacent or not any(path.suffix == '.log' for path in adjacent.values()):
        raise RuntimeError('Actual terminal invocation log/exit missing')
    return {'name': name, 'attempt': attempt, 'manifest': manifest_path, 'expected': expected,
            'exit': exit_value, 'result': result, 'passed': passed,
            'proofs': proofs, 'runtime': runtime, 'adjacent': adjacent}


def archive_attempt(prepared, packet):
    name, attempt = prepared['name'], prepared['attempt']
    target = packet / name
    target.mkdir(parents=True)
    members = {relative: attempt / relative for relative in prepared['expected']}
    members['source/source-manifest.json'] = prepared['manifest']
    for path in sorted(attempt.rglob('*')):
        if not path.is_file() or path.is_relative_to(attempt / 'source'):
            continue
        if '__pycache__' in path.parts or path.suffix == '.pyc':
            continue
        members[path.relative_to(attempt).as_posix()] = path
    for filename, path in prepared['adjacent'].items():
        members['adjacent/' + filename] = path
        copy(path, target / 'adjacent' / filename)
    archive = target / 'executed-source-output-runtime.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipped:
        for relative, path in sorted(members.items()):
            zipped.write(path, relative)
    decoded = []
    with zipfile.ZipFile(archive) as zipped:
        if zipped.testzip() is not None or sorted(zipped.namelist()) != sorted(members):
            raise RuntimeError(f'ZIP CRC/member mismatch: {name}')
        for relative, path in sorted(members.items()):
            payload = zipped.read(relative)
            if payload != path.read_bytes():
                raise RuntimeError(f'Decoded member differs: {name}/{relative}')
            decoded.append({'path': relative, 'bytes': len(payload),
                            'sha256': hashlib.sha256(payload).hexdigest()})
    for path in sorted(attempt.glob('*')):
        if path.is_file():
            copy(path, target / path.name)
    copy(prepared['manifest'], target / 'source/source-manifest.json')
    copy(attempt / 'source/case.lisp', target / 'source/case.lisp')
    return {'attempt': name, 'status': 'POINT_GATE_PASS' if prepared['passed'] else 'RETAINED_TERMINAL_FAILURE',
            'nativeExit': prepared['exit'], 'sourceFiles': len(prepared['expected']),
            'sourceProofs': prepared['proofs'], 'nativeRuntimeProof': prepared['runtime'],
            'result': prepared['result'], 'archive': record(archive, packet),
            'crcPass': True, 'decodedBytesMatchOriginals': True, 'members': decoded}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', action='append', help='Terminal attempt name; repeat to retain failures')
    parser.add_argument('--packet', default='composite-apex-point-controls')
    args = parser.parse_args()
    names = args.attempt or ['composite-apex-point-001']
    if len(names) != len(set(names)) or Path(args.packet).name != args.packet:
        raise RuntimeError('Duplicate attempts or unsafe packet name')
    packet = ROOT / 'docs/evidence/unnotched-gravity-2026-10-25' / args.packet
    if packet.exists():
        raise RuntimeError('Packet must be fresh; no evidence overwrite')
    if record(PLAN)['sha256'] != PLAN_SHA or PLAN_SHA not in REVIEW.read_text(encoding='utf-8-sig'):
        raise RuntimeError('Root-approved plan/review hash binding changed')
    prepared = [prepare_attempt(name) for name in names]
    packet.mkdir(parents=True)
    (packet / '.gitattributes').write_bytes(b'* -text\n*.zip binary\n')
    copy(Path(__file__), packet / 'executed-pack-script.py')
    copy(PLAN, packet / 'design/PERFECT_MC_APEX_PLAN.md')
    copy(REVIEW, packet / 'design/PERFECT_MC_APEX_REVIEW.md')
    archives = [archive_attempt(attempt, packet) for attempt in prepared]
    write_json(packet / 'archive-member-verification.json', {
        'archives': archives, 'totalExecutedSourceEntries': sum(row['sourceFiles'] for row in archives),
        'totalDecodedMembers': sum(len(row['members']) for row in archives),
        'allCrcAndDecodedPayloadChecksPassed': True})
    write_json(packet / 'summary.json', {
        'schema': 'cl-mpm.composite-apex-point-controls.evidence.v1',
        'createdUtc': datetime.now(timezone.utc).isoformat(),
        'status': 'ALL_RETAINED_POINT_GATES_PASS' if all(row['passed'] for row in prepared)
                  else 'TERMINAL_FAILURES_RETAINED',
        'attempts': [{'attempt': row['attempt'], 'status': row['status'], 'nativeExit': row['nativeExit'],
                      'result': row['result'], 'sourceFiles': row['sourceFiles']} for row in archives],
        'approvedDesignSha256': PLAN_SHA, 'unchangedStrictProjectorSha256': STRICT_SHA,
        'landslideVerified': False, 'scientificallyValidated': False,
        'scope': 'New separately declared perfect-Cauchy composite-apex point controls only. '
                 'Strict original failure remains evidence; default compatibility and bounded MPM output are separate gates.',
        'provenanceLimits': 'Executed immutable snapshot bytes are authoritative. '
                            'No claim that later working files equal every earlier attempt; no full slope or whole-failure-capsule rollback.',
        'packagingOperations': 'Read/copy/hash/ZIP/CRC/decode verification only; no tests, replay, solver or saved-data analysis executed.'})
    (packet / 'README.md').write_text(
        '# Optional perfect MC composite apex: point controls\n\n'
        'This packet preserves actual terminal new-model native point gates, their complete immutable executed '
        'sources/DLL/case/capsule, available before/after source/runtime proofs, actual result and adjacent invocation '
        'logs/exits. Any retained compile or group failure remains a failure. The summary reproduces actual result '
        'fields; packaging does not execute or replace tests. Every archive member was CRC-tested and decoded '
        'byte for byte against its original. Missing proof is disclosed and cannot support a PASS claim.\n\n'
        'The approved hash-bound design adds an explicit volumetric apex flow to a separate optional model. '
        'It preserves the strict default and delegates the uncertified cap band without fallback. This is '
        'neither unchanged strict MC nor fracture modelling, paper agreement or demonstrated landslide. '
        'Default regressions, native output and full slope evidence belong to separate packets.\n\n'
        'The artifact index excludes itself; local * -text preserves copied bytes. Verify staged Git blobs '
        'and force-add any intended ignored evidence before committing.\n', encoding='utf-8', newline='\n')
    artifacts = [record(path, packet) for path in sorted(packet.rglob('*')) if path.is_file()]
    write_json(packet / 'artifact-index.json', {'schema': 'cl-mpm.evidence.artifact-index.v1',
        'artifacts': artifacts, 'note': 'Index excludes itself; raw bytes preserved by * -text.'})
    for row in artifacts:
        if record(packet / row['path'], packet) != row:
            raise RuntimeError(f'Final indexed artifact differs: {row["path"]}')
    print(json.dumps({'packet': str(packet), 'indexedArtifacts': len(artifacts),
                     'executedSourceEntries': sum(row['sourceFiles'] for row in archives),
                     'decodedZipMembers': sum(len(row['members']) for row in archives),
                     'attempts': [{k: row[k] for k in ('attempt', 'status', 'sourceFiles')} for row in archives]}, indent=2))


if __name__ == '__main__':
    main()
