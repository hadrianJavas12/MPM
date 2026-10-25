"""FIRST synthetic reviewer control invocation from persistent copied bytes."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
output = root / 'output/mc-composite-apex-2026-10-26/analysis-controls-001'
assert not output.exists()
files = ['tests/analysis/test_gravity_composite_apex_review.py',
         'scripts/review-gravity-composite-apex.py', 'scripts/review-gravity-slope.py',
         'scripts/plot_m5_cliff_comparison.py',
         'research/references/unnotched-mc-ssr/composite-apex-srf1p6-contract.json']
records = []
for name in files:
    original, copied = root / name, output / 'source' / name
    copied.parent.mkdir(parents=True, exist_ok=True)
    payload = original.read_bytes()
    copied.write_bytes(payload)
    records.append({'path': name, 'sha256': hashlib.sha256(payload).hexdigest(), 'bytes': len(payload)})
(output / 'source-before.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
command = [sys.executable, str(output / 'source' / files[0])]
(output / 'command.json').write_text(json.dumps(command, indent=2) + '\n', encoding='utf-8')
result = subprocess.run(command, cwd=root, capture_output=True, text=True)
(output / 'stdout.log').write_text(result.stdout, encoding='utf-8')
(output / 'stderr.log').write_text(result.stderr, encoding='utf-8')
for row in records:
    assert hashlib.sha256((output / 'source' / row['path']).read_bytes()).hexdigest() == row['sha256']
    assert hashlib.sha256((root / row['path']).read_bytes()).hexdigest() == row['sha256']
(output / 'result.json').write_text(json.dumps({'exitCode': result.returncode,
    'copiedSourcesUnchanged': True, 'currentSourcesMatch': True, 'sourceCount': len(records),
    'nativeCalls': 0, 'scope': 'Synthetic reviewer helper controls only; no full CLI/native/actual-state audit/render'}) + '\n', encoding='utf-8')
print(result.stderr)
sys.exit(result.returncode)
