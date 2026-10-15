"""Read-only independent audit of the accepted historical solver artifacts.

Does not import the project's VTK reader or execute Lisp. Writes only to this
ignored audit directory. A consistent artifact is not proof of physical truth.
"""
from pathlib import Path
import csv, gzip, hashlib, json, math, re
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
RUN = ROOT / 'output/reference-reproduction-2026-10-15/dp-physical-pilot'
BUNDLE = ROOT / 'docs/evidence/joss-collapse-2026-10-15'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def parse(path):
    """Independent byte cursor parser: NumPy only decodes IEEE BE payloads."""
    data = path.read_bytes()
    cursor = 0
    def line():
        nonlocal cursor
        end = data.index(b'\n', cursor)
        out = data[cursor:end].rstrip(b'\r').decode('ascii')
        cursor = end + 1
        return out
    def payload(n):
        nonlocal cursor
        arr = np.frombuffer(data[cursor:cursor + n * 8], dtype='>f8').astype(float)
        assert len(arr) == n and np.isfinite(arr).all(), path
        cursor += n * 8
        assert line() == ''
        return arr
    assert line().startswith('# vtk DataFile Version ')
    title = line()
    assert line() == 'BINARY' and line() == 'DATASET UNSTRUCTURED_GRID'
    header = line().split()
    assert header[0] == 'POINTS' and header[2] == 'double'
    n = int(header[1])
    points = payload(n * 3).reshape(n, 3)
    assert line() == f'POINT_DATA {n}'
    fields = {}
    while cursor < len(data):
        header = line().split()
        if not header:
            continue
        assert len(header) == 4 and header[0] == 'SCALARS' and header[2:] == ['double', '1']
        assert line() == 'LOOKUP_TABLE default' and header[1] not in fields
        fields[header[1]] = payload(n)
    return points, fields

rows = list(csv.DictReader((RUN / 'timesteps.csv').open(newline='')))
physical = [r for r in rows if r['phase'] != 'settle']
assert len(rows) == 175 and len(physical) == 174
assert [int(r['step']) for r in physical] == list(range(1, 175))
records = []
previous = None
refpoints, reffields = parse(RUN / 'vtk/equilibrium.vtk')
origin = refpoints[:, :2] - np.column_stack((reffields['disp_x'], reffields['disp_y']))
ref_mass = reffields['mass']
identifiers = {k: reffields[k] for k in ('mass', 'index', 'unique-id', 'split-depth')}
all_fields = list(reffields)
continuity = []
for row in physical:
    path = RUN / 'vtk' / f"sim_{int(row['step']):05d}.vtk"
    points, fields = parse(path)
    assert list(fields) == all_fields
    assert len(points) == 4155
    assert (fields['mass'] > 0).all() and (fields['volume'] > 0).all()
    assert (fields['size_x'] > 0).all() and (fields['size_y'] > 0).all()
    assert ((fields['damage'] >= 0) & (fields['damage'] <= 1)).all()
    assert all(np.array_equal(fields[k], identifiers[k]) for k in identifiers)
    mass = float(fields['mass'].sum())
    massdamage = float(fields['mass'] @ fields['damage'])
    assert math.isclose(mass, float(row['mass']), abs_tol=1e-7)
    assert math.isclose(massdamage, float(row['massDamage']), abs_tol=6e-8)
    displacement = np.column_stack((fields['disp_x'], fields['disp_y']))
    origin_error = float(abs(points[:, :2] - displacement - origin).max())
    base = fields['index'] == 1
    outside = (points[:, 0] < 0) | (points[:, 0] >= 31) | (points[:, 1] < 0) | (points[:, 1] >= 17.3333333333)
    domain_outside = (points[:, 0] - fields['size_x'] / 2 < 0) | (points[:, 0] + fields['size_x'] / 2 > 31) | (points[:, 1] - fields['size_y'] / 2 < 0) | (points[:, 1] + fields['size_y'] / 2 > 17.3333333333)
    rec = {'step': int(row['step']), 'time': float(row['time']), 'phase': row['phase'],
           'mass_scale': float(row['massScale']), 'particles': len(points),
           'scalar_arrays': len(fields), 'all_fields_finite': True, 'sha256': sha(path),
           'mass': mass, 'material_volume': float(fields['volume'].sum()),
           'min_particle_volume': float(fields['volume'].min()), 'max_particle_volume': float(fields['volume'].max()),
           'damage_max': float(fields['damage'].max()), 'mass_weighted_damage': massdamage / mass,
           'base_particles': int(base.sum()), 'base_damage_max': float(fields['damage'][base].max()),
           'base_plastic_strain_max': float(abs(fields['plastic-strain'][base]).max()),
           'position_min': points.min(0).tolist(), 'position_max': points.max(0).tolist(),
           'axis_aligned_domain_min': [float(np.min(points[:,0]-fields['size_x']/2)), float(np.min(points[:,1]-fields['size_y']/2))],
           'axis_aligned_domain_max': [float(np.max(points[:,0]+fields['size_x']/2)), float(np.max(points[:,1]+fields['size_y']/2))],
           'centre_of_mass': (fields['mass'] @ points / mass).tolist(),
           'particle_centres_outside_31m_window': int(outside.sum()),
           'axis_aligned_domains_extending_outside_31m_window': int(domain_outside.sum()),
           'mass_fraction_of_centres_outside_window': float(fields['mass'][outside].sum() / mass),
           'max_displacement_origin_error_m': origin_error}
    if previous:
        prevp, prevf, prevrow = previous
        delta = np.linalg.norm(points[:, :2] - prevp[:, :2], axis=1)
        reduction = fields['damage'] - prevf['damage']
        dt = float(row['time']) - float(prevrow['time'])
        assert dt > 0
        continuity.append({'step': int(row['step']), 'time': float(row['time']), 'dt': dt,
                           'max_particle_displacement_m': float(delta.max()),
                           'median_particle_displacement_m': float(np.median(delta)),
                           'max_damage_decrease': max(0., float(-reduction.min())),
                           'particles_with_damage_decrease_beyond_1e-12': int((reduction < -1e-12).sum())})
    previous = points, fields, row
    records.append(rec)

manifest = json.loads((BUNDLE / 'manifest.json').read_text())
manifest_checks = []
for name, entry in manifest['files'].items():
    path = BUNDLE / name
    check = {'file': name, 'bundle_sha256_matches': sha(path) == entry['sha256'],
             'bytes_match': path.stat().st_size == entry['bytes']}
    source = ROOT / entry['source']
    check['original_source_exists'] = source.exists()
    if 'uncompressedSha256' in entry:
        digest = hashlib.sha256(gzip.decompress(path.read_bytes())).hexdigest()
        check['uncompressed_sha256_matches'] = digest == entry['uncompressedSha256']
        check['uncompressed_equals_original'] = source.exists() and digest == sha(source)
    else:
        check['bundle_equals_original'] = source.exists() and sha(source) == sha(path)
    manifest_checks.append(check)

log = (BUNDLE / 'sources/criterion-probe.log').read_text()
matches = re.findall(r'Step (\d+)/1000; physical time ([\d.]+) s; (\w+)', log)
log_csv_consistent = len(matches) == len(physical) and all(int(a) == int(r['step']) and abs(float(b) - float(r['time'])) < 5e-7 and c == r['phase'] for (a,b,c), r in zip(matches,physical))
transitions = list(csv.DictReader((RUN / 'transitions.csv').open(newline='')))
transition_checks = []
for r in transitions[1:]:
    row = next(x for x in physical if abs(float(x['time']) - float(r['time'])) < 1e-9)
    transition_checks.append({'time': float(r['time']), 'from': r['from'], 'to': r['to'],
                              'matches_recorded_phase': row['phase'] == r['from'],
                              'epsilon_matches': row['energyRatio'] == r['energyRatio'],
                              'oobf_matches': row['oobf'] == r['oobf']})

summary = {'audit_kind': 'independent saved-artifact integrity and continuity; no solver runs',
           'read_only_inputs': True, 'physical_frames': len(records), 'all_36_fields_finite': True,
           'all_particle_counts_equal_4155': True, 'per_particle_mass_index_uniqueid_splitdepth_unchanged': True,
           'unique_id_limitation': 'Most unique-id values are -1: array correspondence is strongly consistent but is not an independent globally unique identity proof.',
           'total_mass': records[0]['mass'], 'mass_constant': len({r['mass'] for r in records}) == 1,
           'volume_range_m2': [min(r['material_volume'] for r in records), max(r['material_volume'] for r in records)],
           'damage_monotone_every_particle': all(r['max_damage_decrease'] <= 1e-12 for r in continuity),
           'max_damage_reduction': max(r['max_damage_decrease'] for r in continuity),
           'max_displacement_origin_error_m': max(r['max_displacement_origin_error_m'] for r in records),
           'base_count_constant_496': all(r['base_particles'] == 496 for r in records),
           'base_damage_zero_all_frames': all(r['base_damage_max'] == 0 for r in records),
           'base_plastic_strain_zero_all_frames': all(r['base_plastic_strain_max'] == 0 for r in records),
           'max_centres_outside_window': max(r['particle_centres_outside_31m_window'] for r in records),
           'max_domains_extending_outside_window': max(r['axis_aligned_domains_extending_outside_31m_window'] for r in records),
           'all_frame_domain_bounds': [min(r['axis_aligned_domain_min'][0] for r in records), max(r['axis_aligned_domain_max'][0] for r in records), min(r['axis_aligned_domain_min'][1] for r in records), max(r['axis_aligned_domain_max'][1] for r in records)],
           'first_damage': next(r for r in records if r['damage_max'] > 0),
           'first': records[0], 'last': records[-1], 'log_csv_consistent': log_csv_consistent,
           'transitions_consistent': all(all(r[k] for k in ('matches_recorded_phase','epsilon_matches','oobf_matches')) for r in transition_checks),
           'manifest_all_pass': all(all(v for k,v in r.items() if k != 'file') for r in manifest_checks),
           'limitations': ['Artifact consistency cannot independently prove which cached FASL bytes were executing.',
                           'VTK has no native clock; time is corroborated by source/log/CSV only.',
                           'Snapshots omit grid, material history and full integrator state; no exact replay asserted.',
                           'Finite fields and positive volume do not establish mesh convergence, energy conservation, fracture validity, or scientific accuracy.',
                           'No derivative or energy-balance test is inferred from sparse saved frames.']}
result = {'summary': summary, 'manifest': manifest_checks, 'transitions': transition_checks,
          'frames': records, 'adjacent_frame_continuity': continuity}
probe_points, probe_fields = parse(ROOT / 'output/reference-reproduction-2026-10-15/criterion-probe/equilibrium.vtk')
pilot_initial, initial_fields = parse(RUN / 'vtk/initial.vtk')
result['warm_start_readback'] = {
    'probe_equilibrium_to_pilot_initial_max_position_difference_m': float(abs(probe_points - pilot_initial).max()),
    'changed_fields_between_probe_and_pilot_initial': {
        key: float(abs(probe_fields[key] - initial_fields[key]).max())
        for key in probe_fields if not np.array_equal(probe_fields[key], initial_fields[key])},
    'pilot_initial_to_elastic_recheck_max_position_difference_m': float(abs(pilot_initial-refpoints).max()),
    'damage_zero_in_all_three_preparation_snapshots': all(float(f['damage'].max()) == 0 for f in (probe_fields, initial_fields, reffields)),
    'interpretation': 'Accepted initial.vtk is warm state after 1658 probe updates, with only the base material index changed in saved fields; equilibrium.vtk is the single extra elastic recheck.'}
(OUT / 'forensic-artifacts-audit.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
print(json.dumps(summary, indent=2))
