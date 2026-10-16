"""Completion-only M0 evidence collector. Never starts a native simulation."""
import hashlib, importlib.util, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'output/material-contract-2026-10-16'
OLD = ROOT / 'output/framework-refactor-2026-10-15'
DEST = ROOT / 'docs/evidence/material-contract-2026-10-16'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def log_text(path):
    raw = path.read_bytes()
    return raw.decode('utf-16' if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig')

def count(path, expression):
    match = re.search(expression, log_text(path))
    if not match:
        raise SystemExit('Missing test result: ' + str(path))
    return int(match.group(1))

node_log = BASE / 'node-tests.log'
if count(node_log, r'fail\s+(\d+)') or count(node_log, r'skipped\s+(\d+)'):
    raise SystemExit('Node suite failed/skipped; preserve logs')
checks = {
    'nodePassed': count(node_log, r'pass\s+(\d+)'), 'nodeSkipped': 0,
    'componentContractsPassed': count(BASE / 'framework-components.log', r'CHECKS:\s*(\d+) passed'),
    'materialDiagnosticsContractsPassed': count(ROOT / '.tmp/material-diagnostics-contracts-006.log', r'CONTRACTS:\s*(\d+) passed'),
    'configurationContractsPassed': count(ROOT / 'output/config-contract-2026-10-16.log', r'CONTRACTS:\s*(\d+) passed')}
if count(BASE / 'framework-components.log', r'passed,\s*(\d+) failed'):
    raise SystemExit('Component contracts failed; preserve logs')
if 'TRIAXIAL COMPONENT CONTRACTS PASSED' not in log_text(BASE / 'triaxial-components.log'):
    raise SystemExit('Legacy callback contracts did not pass')

for name in ('triaxial-2d-after', 'triaxial-3d-before', 'triaxial-3d-after'):
    status, metadata = BASE / (name + '-status.json'), BASE / name / 'manifest.json'
    if not status.exists() or not metadata.exists():
        raise SystemExit('INCOMPLETE: ' + name + '; do not start another run')
    if read(status)['exitCode'] != 0 or read(metadata).get('complete') is not True:
        raise SystemExit('FAILED/INCOMPLETE: inspect ' + name + '; no evidence overwritten')

runs = {'2d-before': OLD / 'triaxial-2d-before-mps2',
        '2d-after': BASE / 'triaxial-2d-after',
        '3d-before': BASE / 'triaxial-3d-before',
        '3d-after': BASE / 'triaxial-3d-after'}
comparisons = {}
for dimension in ('2d', '3d'):
    target = BASE / ('triaxial-' + dimension + '-before-after-comparison.json')
    if not target.exists():
        completed = subprocess.run([sys.executable, str(ROOT / 'scripts/compare-framework-runs.py'),
            '--baseline', str(runs[dimension + '-before']), '--candidate', str(runs[dimension + '-after']),
            '--output', str(target)], capture_output=True, text=True)
        if completed.returncode not in (0, 1) or not target.exists():
            raise SystemExit('Comparator error: ' + completed.stderr[-2000:])
    comparisons[dimension] = read(target)
for label in ('3d-before', '3d-after'):
    if not (runs[label] / 'audit.json').exists():
        completed = subprocess.run([sys.executable, str(ROOT / 'scripts/audit-triaxial.py'),
            '--run-dir', str(runs[label])], capture_output=True, text=True)
        (BASE / (label + '-audit.log')).write_text(completed.stdout + completed.stderr, encoding='utf8')
        if completed.returncode:
            raise SystemExit('Audit failed: retain ' + label + '-audit.log and investigate')

spec = importlib.util.spec_from_file_location('evidence', ROOT / '.tmp/pack-framework-evidence.py')
lib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)
lib.DEST, lib.BASE, lib.rows = DEST, BASE, []
DEST.mkdir(parents=True, exist_ok=True)
lib.put_bytes('.gitattributes', b'* -text -whitespace\n*.gz binary\n*.png binary\n*.mp4 binary\n')
results = {label: lib.run_evidence(label, run) for label, run in runs.items()}
for dimension in ('2d', '3d'):
    lib.zipped_file('verification/triaxial-' + dimension + '-comparison.json.gz',
                    BASE / ('triaxial-' + dimension + '-before-after-comparison.json'))
for name in ('node-check.log', 'node-tests.log', 'framework-components.log',
             'triaxial-components.log', 'triaxial-2d-after.log', 'triaxial-3d-before.log',
             'triaxial-3d-after.log', '3d-before-audit.log', '3d-after-audit.log'):
    path = BASE / name
    if path.exists():
        lib.zipped_file('logs/' + name + '.gz', path)
for name in ('native-binary-hashes.json', 'before-process.json', 'after-processes.json',
             'triaxial-3d-serial.json', 'triaxial-2d-after-status.json',
             'triaxial-3d-before-status.json', 'triaxial-3d-after-status.json'):
    if (BASE / name).exists():
        lib.put_file('verification/' + name, BASE / name)
for relative in ('.tmp/material-diagnostics-contracts-006.log', 'output/config-contract-2026-10-16.log'):
    lib.zipped_file('logs/' + Path(relative).name + '.gz', ROOT / relative)
for name in ('M0_MATERIAL_CONTRACT_EVIDENCE.json', 'M0_MATERIAL_CONTRACT_AUDIT.md'):
    lib.put_file('verification/' + name, ROOT / 'research/reports' / name)
lib.archive('sources/executed-after-source.tar.gz',
    [(p.relative_to(runs['3d-after'] / 'source').as_posix(), p)
     for p in (runs['3d-after'] / 'source').rglob('*') if p.is_file()]
    + [('case-2d.lisp', runs['2d-after'] / 'source/case.lisp')])
lib.archive('sources/executed-before-3d-source.tar.gz',
    [(p.relative_to(runs['3d-before'] / 'source').as_posix(), p)
     for p in (runs['3d-before'] / 'source').rglob('*') if p.is_file()])
for relative in ('scripts/compare-framework-runs.py', 'scripts/audit-triaxial.py',
                 '.tmp/finalize-material-contract.py'):
    lib.put_file('sources/' + Path(relative).name, ROOT / relative)

joss_paths = sorted((ROOT / 'framework/scenarios/joss').glob('*.lisp'))
joss_paths += [ROOT / 'framework/materials/chalk.lisp', ROOT / 'framework/scenarios/cliff/settings.lisp']
identity = [{'path': p.relative_to(ROOT).as_posix(), 'currentSha256': digest(p),
             'serialSnapshotSha256': digest(OLD / 'joss-serial-after/source' / p.relative_to(ROOT)),
             'identicalBytes': p.read_bytes() == (OLD / 'joss-serial-after/source' / p.relative_to(ROOT)).read_bytes()}
            for p in joss_paths]
lib.put_json('verification/joss-numerical-source-identity.json', {
    'scope': 'Byte comparison of dedicated Joss numerical modules; no new full Joss run on 64f47cc',
    'allIdentical': all(v['identicalBytes'] for v in identity), 'files': identity})
summary = {'dateLocal': '2026-10-16', 'afterExecutedCommit': '64f47cc',
    'before3dCommit': 'c749d32', 'currentVmRegressionPassed': all(v.get('passed') is True for v in comparisons.values()),
    'regressions': {k: {field: v.get(field) for field in
        ('passed', 'baseline_states', 'candidate_states', 'max_position_difference_m', 'failure')}
        for k, v in comparisons.items()}, 'runs': results,
    'joss': {'serialExactPassSnapshot': '41403f4', 'fourWorkerStrictFailureRetained': True,
             'currentNumericalSourcesIdentical': all(v['identicalBytes'] for v in identity)},
    'checks': checks,
    'M0Status': 'PROVISIONAL', 'scientificValidation': False,
    'limits': ['Four-worker repeatability remains an explicit exception',
               'Complete transitive loaded FASL/DLL provenance not established',
               'No experimental calibration, mesh convergence or closed energy budget',
               'M2 isolated prototype is not installed or validated as a full MPM study']}
lib.put_json('validation-summary.json', summary)
(DEST / 'manifest.json').write_text(json.dumps({'entries': lib.rows}, indent=2) + '\n', encoding='utf8')
assert all(digest(DEST / row['path']) == row['sha256'] for row in lib.rows)
print(json.dumps({'destination': str(DEST), 'files': len(lib.rows),
                  'currentVmRegressionPassed': summary['currentVmRegressionPassed'],
                  'regressions': summary['regressions']}, indent=2))
