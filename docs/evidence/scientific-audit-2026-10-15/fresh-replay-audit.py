from pathlib import Path
import csv
import hashlib
import json
import runpy
import numpy as np

root = Path('D:/MPM')
out = root / 'output/scientific-audit-2026-10-15'
run = out / 'fresh-replay-4s'
read = runpy.run_path(str(root / 'scripts/compare-reference-video.py'), run_name='audit_reader')['read_particle_vtk']
metadata = json.loads((run / 'reference-metadata.json').read_text())
rows = list(csv.DictReader((run / 'timesteps.csv').open(newline='')))
physical = [r for r in rows if r['phase'] != 'settle']
assert metadata['complete'] and metadata['physicalTime'] == 4 and len(physical) == 2
records = []
for name in ('initial.vtk', 'equilibrium.vtk', 'sim_00001.vtk', 'sim_00002.vtk'):
    path = run / 'vtk' / name
    points, fields = read(path)
    assert len(points) == 4155 and len(fields) == 36
    assert (fields['damage'] >= 0).all() and (fields['damage'] <= 1).all()
    base = fields['index'] == 1
    assert int(base.sum()) == 496 and float(fields['damage'][base].max()) == 0
    maximum = int(fields['damage'].argmax())
    records.append({'file': name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                    'particles': len(points), 'scalarFields': len(fields),
                    'mass': float(fields['mass'].sum()), 'maxDamage': float(fields['damage'][maximum]),
                    'maxDamagePosition': points[maximum].tolist(),
                    'massWeightedDamage': float(np.dot(fields['mass'], fields['damage']) / fields['mass'].sum()),
                    'maxProtectedBaseDamage': float(fields['damage'][base].max()), 'allFieldsFinite': True})
newp, newf = read(run / 'vtk/sim_00002.vtk')
oldp, oldf = read(root / 'output/reference-reproduction-2026-10-15/dp-physical-pilot/vtk/sim_00002.vtk')
result = {
    'kind': 'Fresh Windows-native production CLI, bounded 4-second replay',
    'loadedEntry': 'docs/evidence/joss-collapse-2026-10-15/sources/run-fast.lisp',
    'entryRole': 'Only compiler/cache policy then cl-mpm-studio:main; no constructor, particle or environment-function replacements',
    'config': 'fresh-replay-4s-config.json',
    'changesFromPublished40sConfig': {'simulationTime': 4, 'maxSteps': 2},
    'equilibrationSteps': metadata['equilibrationSteps'],
    'termination': metadata['termination'], 'complete': metadata['complete'],
    'integrationTime': metadata['physicalTime'], 'frames': metadata['frames'],
    'massConstantAllFourSnapshots': len(set(r['mass'] for r in records)) == 1,
    'snapshots': records,
    'comparisonToHistoricalPilotAt4s': {
        'maxPositionDifferenceMetres': float(np.abs(newp - oldp).max()),
        'maxDamageDifference': float(np.abs(newf['damage'] - oldf['damage']).max()),
        'firstDamageStillLowerRegion': bool(newp[newf['damage'].argmax(), 1] < 4),
        'bitIdenticalClaim': False,
    },
    'scope': 'Supports native fresh-start initiation without historical hooks; not a full 40s replay, physical validation or kernel correction',
}
(out / 'fresh-replay-audit.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
