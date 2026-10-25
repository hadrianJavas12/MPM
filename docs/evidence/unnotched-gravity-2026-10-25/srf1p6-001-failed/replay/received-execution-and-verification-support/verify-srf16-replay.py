"""Read-only integrity verification of the one already-completed replay."""
from pathlib import Path
import hashlib
import json

ROOT = Path('D:/MPM')
RUN = ROOT / 'output/unnotched-gravity-2026-10-25/srf1p6-failure-replay-001'
FAILED = ROOT / 'output/unnotched-gravity-2026-10-25/srf1p6-001'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

manifest = read(RUN / 'source/source-manifest.json')['files']
before = read(RUN / 'source-proof-before.json')['files']
after = read(RUN / 'source-proof-after.json')['files']
assert len(manifest) == len(before) == len(after) == 283
maps = [{row['path']: row['sha256'].lower() for row in rows}
        for rows in (manifest, before, after)]
assert maps[0] == maps[1] == maps[2]
for path, digest in maps[0].items():
    assert sha(RUN / path) == digest, path
common = read(RUN / 'failed-source-comparison.json')
assert common['allComparedBytesIdentical'] and len(common['files']) == 281
for row in common['files']:
    assert row['failedSha256'] == row['replaySha256'] == sha(FAILED / row['path'])
provenance = [read(RUN / f'source-provenance-{phase}.json')
              for phase in ('before', 'after')]
expected_dll = '57c4c9a6cedb1ade1202914074dab942afc2f15abb114637619ca3cb5d9f074f'
for proof in provenance:
    assert proof['sourceSnapshotExactLoadedBytes']
    assert proof['copiedByteEqualityBeforeLoad']
    assert proof['nativeBackend']['sha256'] == expected_dll
    assert proof['nativeBackend']['verifiedBy'] == 'GetModuleHandleW/GetModuleFileNameW'
result = read(RUN / 'replay-result.json')
assert result['passed'] and result['expectedRejection']
assert result['actualPrincipalReplayCalls'] == 1 and result['physicalUpdates'] == 0
assert result['productionFunctionsRestored'] and result['capsuleUnchanged']
assert result['capsuleSha256'] == sha(FAILED / 'mc-integration-failure.json')
assert sha(RUN / 'source/case.lisp') == sha(ROOT / '.tmp/gravity-srf16-failure-replay.lisp')
exit_record = read(Path(str(RUN) + '-exit.json'))
assert exit_record['exitCode'] == 0
summary = {
    'status': 'PASS',
    'scope': 'Read-only bytes/runtime/result verification after the sole completed principal replay; no material call or solver execution',
    'frozenFilesVerified': 283,
    'failedRunCommonSourcesByteIdentical': 281,
    'beforeAfterAllFilesIdentical': True,
    'nativeMappedDllSha256': expected_dll,
    'nativeMappedDllVerifiedBeforeAndAfter': True,
    'actualPrincipalReplayCalls': 1,
    'physicalUpdates': 0,
    'expectedRejection': True,
    'wholeParticleRollback': 'NOT_EXECUTED: complete particle/simulation state absent',
    'capsuleSha256': result['capsuleSha256'],
    'executedHelperSha256': sha(RUN / 'source/case.lisp'),
    'verificationScriptSha256': sha(Path(__file__)),
    'resultSha256': sha(RUN / 'replay-result.json'),
    'mathSha256': sha(RUN / 'tensile-apex-math.json'),
}
target = RUN / 'replay-source-verification.json'
assert not target.exists()
target.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, indent=2))
