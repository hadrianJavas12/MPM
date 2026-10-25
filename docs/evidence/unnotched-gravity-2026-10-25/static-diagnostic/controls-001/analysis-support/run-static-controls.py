"""Retain the exact new Python controls/backend and run the controls once."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import numpy as np

root = Path(__file__).resolve().parents[1]
out = root / 'output/unnotched-statics-2026-10-25/controls-001'
out.mkdir(parents=True, exist_ok=False)
support = out / 'analysis-support'
support.mkdir()
files = [root / 'scripts/analysis/slope_stability.py',
         root / 'tests/analysis/test_slope_stability.py', Path(__file__)]
records = []
for path in files:
    payload = path.read_bytes()
    target = support / path.name
    shutil.copyfile(path, target)
    assert target.read_bytes() == payload
    records.append(dict(path=str(path), copied=target.name, bytes=len(payload),
                        sha256=hashlib.sha256(payload).hexdigest()))
(out / 'pre-execution.json').write_text(json.dumps(records, indent=2)+'\n', encoding='utf-8')
command = [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests/analysis',
           '-p', 'test_slope_stability.py', '-v']
with (out / 'controls.log').open('w', encoding='utf-8') as stream:
    result = subprocess.run(command, cwd=root, stdout=stream, stderr=subprocess.STDOUT)
unchanged = all(hashlib.sha256(Path(r['path']).read_bytes()).hexdigest() == r['sha256'] for r in records)
report = dict(exitCode=result.returncode, sourceBeforeAfterMatch=unchanged,
              command=command, python=sys.version, numpy=np.__version__, mpmStepsExecuted=0,
              scope='New independent static-equilibrium Python controls; unchanged workspace test/backend bytes retained before execution; no native MPM or full family search')
(out / 'result.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
print(json.dumps(report))
sys.exit(result.returncode if unchanged else 2)
