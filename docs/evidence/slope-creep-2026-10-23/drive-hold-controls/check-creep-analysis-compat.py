import hashlib
import importlib.util
import json
from pathlib import Path

root = Path('D:/MPM')
path = root / 'scripts/plot-slope-creep.py'
spec = importlib.util.spec_from_file_location('creep_audit', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
checks = []
for name in ('pilot-002', 'pusher-pilot-001'):
    run = root / 'output/slope-creep-2026-10-22' / name
    _, rows, _, audit = module.inspect(run)
    assert audit['passedConsistencyChecks'] and audit['nativeComplete']
    checks.append({'savedRun': name, 'frames': len(rows), 'passed': True,
                   'scope': 'New audit reads actual archived native CSV/VTK; does not rerun solver'})
report = {'analysisSha256': hashlib.sha256(path.read_bytes()).hexdigest(),
          'checks': checks, 'scientificValidation': False}
out = root / 'output/slope-creep-2026-10-23/analysis-compatibility.json'
out.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
