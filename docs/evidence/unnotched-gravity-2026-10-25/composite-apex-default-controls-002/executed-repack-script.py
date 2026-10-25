"""Repackage two completed native controls, without tests or verifier changes."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'output/mc-composite-apex-2026-10-25'
ORIGINAL = RAW / 'default-compatibility-evidence-001'
PRESERVED_COPY = RAW / 'default-initial-root-copy-001'
FAILURE = RAW / 'default-compatibility-evidence-001-root-failure.json'
REPACK_FAILURE = RAW / 'default-controls-repack-001-failure.json'
REPACK_PARTIAL = RAW / 'default-controls-repack-partial-001'
PACKET = ROOT / 'docs/evidence/unnotched-gravity-2026-10-25/composite-apex-default-controls-002'
RUNS = {'default-strict34-001': 287, 'default-output-001': 289}


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def record(path, root=None):
    payload = path.read_bytes()
    return {'path': path.relative_to(root).as_posix() if root else str(path),
            'bytes': len(payload), 'sha256': digest(payload)}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n',
                    encoding='utf-8', newline='\n')


def copy(source, target):
    if target.exists():
        raise RuntimeError(f'Refuse overwrite: {target}')
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    if source.read_bytes() != target.read_bytes():
        raise RuntimeError(f'Copy mismatch: {source}')


def verify_original():
    index = read(ORIGINAL / 'artifact-index.json')
    for row in index['artifacts']:
        path = (ORIGINAL / row['path']).resolve()
        assert path.is_relative_to(ORIGINAL.resolve())
        actual = record(path, ORIGINAL)
        assert actual['bytes'] == row['bytes'] and actual['sha256'] == row['sha256'], row['path']
    assert (PRESERVED_COPY / 'artifact-index.json').read_bytes() == (ORIGINAL / 'artifact-index.json').read_bytes()
    for row in index['artifacts']:
        assert (PRESERVED_COPY / row['path']).read_bytes() == (ORIGINAL / row['path']).read_bytes(), row['path']
    failure = read(FAILURE)
    assert failure['status'] == 'FAILED_PACKAGING_LAYOUT_ASSERTION'
    summary = read(ORIGINAL / 'summary.json')
    assert summary['status'] == 'PASS' and summary['frozenSourceCounts'] == RUNS
    assert summary['existingStrictGroupsPassed'] == 34 and summary['boundedGroupsPassed'] == 4
    assert summary['genuineMpmUpdates'] == 2 and summary['boundedMaterialCallsAccepted'] == 1760
    comparison = read(ORIGINAL / 'exact-byte-comparison.json')
    assert comparison['status'] == 'PASS' and len(comparison['comparedFiles']) == 5
    assert all(row['byteIdentical'] and row['baseline'] == row['current'] for row in comparison['comparedFiles'])
    for name, count in RUNS.items():
        assert read(RAW / (name + '-exit.json'))['exitCode'] == 0
        proof = read(RAW / name / 'post-run-source-runtime-verification.json')
        assert proof['status'] == 'PASS' and proof['sourceCount'] == count
        assert (RAW / name / 'result.json').read_bytes() == (ORIGINAL / name / 'result.json').read_bytes()
        assert (RAW / name / 'post-run-source-runtime-verification.json').read_bytes() == (
            ORIGINAL / name / 'post-run-source-runtime-verification.json').read_bytes()
    archives = list(ORIGINAL.glob('*.zip'))
    assert len(archives) == 1
    return summary, archives[0]


def archive_run(old, name, count):
    selected = {}
    for original_name in old.namelist():
        if original_name.startswith(name + '/'):
            relative = original_name[len(name) + 1:]
            original_disk = RAW / name / relative
        elif original_name.startswith('adjacent/' + name):
            relative = original_name
            original_disk = RAW / PurePosixPath(original_name).name
        else:
            continue
        assert '..' not in PurePosixPath(relative).parts and not relative.startswith('/')
        assert relative not in selected
        payload = old.read(original_name)
        assert payload == original_disk.read_bytes(), original_name
        selected[relative] = (original_name, payload)
    manifests = [name for name in selected if name.endswith('source/source-manifest.json')]
    assert manifests == ['source/source-manifest.json'], manifests
    manifest = json.loads(selected[manifests[0]][1])
    assert len(manifest['files']) == count
    for row in manifest['files']:
        payload = selected[row['path']][1]
        assert len(payload) == row['bytes'] and digest(payload) == row['sha256']
    archive = PACKET / name / 'executed-source-output-runtime.zip'
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as new:
        for relative, (_, payload) in sorted(selected.items()):
            new.writestr(relative, payload)
    members = []
    with zipfile.ZipFile(archive) as new:
        assert new.testzip() is None
        assert sorted(new.namelist()) == sorted(selected)
        assert len([n for n in new.namelist() if n.endswith('source/source-manifest.json')]) == 1
        for relative, (original_name, payload) in sorted(selected.items()):
            decoded = new.read(relative)
            assert decoded == payload == old.read(original_name)
            members.append({'path': relative, 'originalArchiveMember': original_name,
                            'bytes': len(decoded), 'sha256': digest(decoded)})
    return {'run': name, 'archive': record(archive, PACKET), 'sourceFiles': count,
            'decodedMembers': len(members), 'crcPass': True,
            'decodedBytesMatchOriginalArchiveAndRaw': True, 'members': members}


def main():
    assert not PACKET.exists(), 'Fresh packet required; preserve existing evidence'
    summary, original_zip = verify_original()
    original_index_before = record(ORIGINAL / 'artifact-index.json')
    preserved_index_before = record(PRESERVED_COPY / 'artifact-index.json')
    PACKET.mkdir(parents=True)
    (PACKET / '.gitattributes').write_bytes(b'* -text\n*.zip binary\n')
    copy(Path(__file__), PACKET / 'executed-repack-script.py')
    # Keep actual control/support files byte-identical. Old package metadata is
    # explicitly labelled provenance, never presented as this new packet index.
    renamed = {'README.md': 'packaging-failure/original-README.md',
               'summary.json': 'packaging-failure/original-summary.json',
               'artifact-index.json': 'packaging-failure/original-artifact-index.json',
               'archive-member-verification.json': 'packaging-failure/original-archive-member-verification.json',
               'executed-pack-script.py': 'packaging-failure/original-executed-pack-script.py',
               'executed-copy-hash-zip-helpers.py': 'packaging-failure/original-copy-hash-zip-helpers.py'}
    for source in sorted(ORIGINAL.rglob('*')):
        if not source.is_file() or source.suffix == '.zip' or source.name == '.gitattributes':
            continue
        relative = source.relative_to(ORIGINAL).as_posix()
        copy(source, PACKET / renamed.get(relative, relative))
    copy(FAILURE, PACKET / 'packaging-failure/root-layout-failure.json')
    copy(REPACK_FAILURE, PACKET / 'packaging-failure/repack-001-filesystem-failure.json')
    copy(REPACK_PARTIAL / 'executed-repack-script.py',
         PACKET / 'packaging-failure/repack-001-executed-helper.py')
    with zipfile.ZipFile(original_zip) as old:
        assert old.testzip() is None
        assert len(set(old.namelist())) == len(old.namelist())
        archives = [archive_run(old, name, count) for name, count in RUNS.items()]
        retained = [member['originalArchiveMember'] for archive in archives for member in archive['members']]
        assert len(retained) == len(set(retained)) == len(old.namelist())
        assert sorted(retained) == sorted(old.namelist()), 'Every original archived member must be retained exactly once'
    write(PACKET / 'archive-member-verification.json', {
        'archives': archives, 'totalExecutedSourceEntries': sum(RUNS.values()),
        'totalDecodedMembers': sum(row['decodedMembers'] for row in archives),
        'eachZipHasExactlyOneCompleteSourceManifest': True,
        'allCrcAndDecodedPayloadChecksPassed': True})
    write(PACKET / 'packaging-failure/provenance.json', {
        'originalPacket': str(ORIGINAL), 'originalPacketIndex': original_index_before,
        'originalCombinedArchiveRetainedInPlace': record(original_zip),
        'initialRootCopyPreserved': str(PRESERVED_COPY), 'initialRootCopyIndex': preserved_index_before,
        'initialRootCopyByteIdenticalToOriginalPacket': True,
        'rootFailureRecord': record(FAILURE),
        'firstRepackHelperFailure': record(REPACK_FAILURE),
        'firstRepackPartialRetainedInPlace': str(REPACK_PARTIAL),
        'failureClassification': 'Packaging layout did not satisfy the unchanged one-manifest-per-ZIP verifier; native results and bytes did not fail',
        'remedy': 'Two complete per-run ZIPs; original combined ZIP remains untouched under output, referenced by hash rather than copied into this corrected packet',
        'unchangedVerifier': record(ROOT / '.tmp/verify-indexed-evidence.py'),
        'newRootVerification': 'NOT_RUN_BY_PACKAGER: root owns verifier/staging'})
    corrected = dict(summary)
    corrected.update({'createdUtc': datetime.now(timezone.utc).isoformat(),
        'packetLayout': 'Two complete source/output/runtime ZIPs, one per executed native control',
        'packagingFailureRetained': 'packaging-failure/root-layout-failure.json',
        'originalNativeResultsUnchanged': True,
        'newNativeOrNumericalExecutions': 0,
        'packagingOperations': 'Read/copy/hash/ZIP/CRC/all-member decoded byte verification only; no tests, solver, replay, comparison or renderer rerun'})
    write(PACKET / 'summary.json', corrected)
    (PACKET / 'README.md').write_text(
        '# Default dispatch compatibility: corrected evidence layout\n\n'
        'The actual native results are unchanged: 34 existing strict groups and four bounded output groups '
        'passed on ac767e1; two genuine USF updates accepted 1760 material calls. Three VTK states and two CSVs '
        'were already compared byte for byte to the retained strict baseline. No test, solver, replay, numerical '
        'comparison, renderer or scientific audit was repeated for this packet.\n\n'
        'The initial packet placed both complete run manifests in one ZIP. Root\'s existing verifier correctly '
        'rejected that layout with its one-manifest-per-ZIP assertion. This is a packaging failure, not a native '
        'test or byte mismatch. The original packet and failed root copy remain untouched under output; their '
        'indices, original archive hash, original packaging code/metadata and actual root failure record are '
        'retained or referenced in packaging-failure/. The original combined ZIP is not copied into this packet.\n\n'
        'The first repack helper stopped before its first ZIP write because its archive parent directory had '
        'already been copied with the result files. That helper and partial packet were preserved under output; '
        'the observed filesystem failure and exact helper are included here. Allowing that already existing '
        'parent directory changes packaging only and repeats no native or numerical work.\n\n'
        'Each corrected ZIP contains exactly one complete executed source manifest and payload, with the same '
        'actual raw outputs, runtime/DLL proofs, logs, commands and exits. All 612 original archive members are '
        'partitioned exactly once, CRC-tested and decoded against both the original ZIP and immutable raw '
        'files. Source counts are 287 and 289. No missing standalone old34 hash proof is invented; its actual '
        'source manifest/runtime provenance and existing post-run verification remain authoritative.\n\n'
        'Default optional composite loading remains false. Copying optional sources into a snapshot is not '
        'loading that model. This packet demonstrates default compatibility within the retained controls, '
        'not a complete slope run, landslide, calibrated runout or scientific validation. Root owns independent '
        'verification and staging with the unchanged verifier.\n', encoding='utf-8', newline='\n')
    assert record(ORIGINAL / 'artifact-index.json') == original_index_before
    assert record(PRESERVED_COPY / 'artifact-index.json') == preserved_index_before
    artifacts = [record(path, PACKET) for path in sorted(PACKET.rglob('*')) if path.is_file()]
    write(PACKET / 'artifact-index.json', {'schema': 'cl-mpm.evidence.artifact-index.v1',
        'artifacts': artifacts, 'note': 'Index excludes itself; two one-run ZIPs satisfy the existing verifier shape; * -text preserves copied bytes.'})
    for row in artifacts:
        assert record(PACKET / row['path'], PACKET) == row
    print(json.dumps({'packet': str(PACKET), 'indexedArtifacts': len(artifacts),
        'archives': len(archives), 'executedSourceEntries': sum(RUNS.values()),
        'decodedZipMembers': sum(row['decodedMembers'] for row in archives),
        'perRun': [{'run': row['run'], 'sources': row['sourceFiles'], 'members': row['decodedMembers']} for row in archives],
        'originalPacketsUntouched': True, 'status': 'PACKAGED_FOR_ROOT_VERIFICATION'}, indent=2))


if __name__ == '__main__':
    main()
