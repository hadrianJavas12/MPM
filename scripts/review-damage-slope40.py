"""Review actual saved damage-slope40 VTKs; never run or repair a solver."""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.colors import Normalize
from matplotlib.patches import Rectangle

READER = Path(__file__).with_name('compare-reference-video.py')
spec = importlib.util.spec_from_file_location('damage40_vtk', READER)
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check(path):
    points, fields = reader.read_particle_vtk(path)
    for key in ('damage', 'mass', 'volume', 'index', 'size_x', 'size_y'):
        if key not in fields:
            raise ValueError(f'Missing actual native {key}: {path}')
    damage = fields['damage']
    if not ((damage >= 0).all() and (damage <= 1).all() and (fields['volume'] > 0).all()):
        raise ValueError(f'Invalid damage/volume: {path}')
    if not np.isin(fields['index'], (0, 1)).all():
        raise ValueError(f'Unexpected material tags: {path}')
    base = fields['index'] == 1
    if not base.any() or np.any(damage[base] != 0):
        raise ValueError(f'Protected base missing or damaged: {path}')
    mass = fields['mass']
    return points, fields, {
        'file': path.name, 'sha256': digest(path), 'particles': len(points),
        'massPerUnitDepth': float(mass.sum()), 'maxDamage': float(damage.max()),
        'massWeightedDamage': float(np.dot(mass, damage) / mass.sum()),
        'baseMaxDamage': float(damage[base].max()),
        'bodyCentroidM': np.average(points[~base, :2], weights=mass[~base], axis=0).tolist(),
        'bodyMassPastInitialToe': float(mass[(~base) & (points[:, 0] > 23.9175359259421)].sum()),
    }

def draw(points, fields, time, phase, bounds, target):
    fig, ax = plt.subplots(figsize=(14, 5), constrained_layout=True)
    sizes = np.column_stack((fields['size_x'], fields['size_y']))
    patches = [Rectangle(point[:2] - size / 2, *size) for point, size in zip(points, sizes)]
    collection = PatchCollection(patches, cmap='viridis', norm=Normalize(0, 1), linewidth=0)
    collection.set_array(fields['damage'])
    ax.add_collection(collection)
    ax.set(xlim=bounds[:2], ylim=bounds[2:], xlabel='x (m)', ylabel='y (m)', aspect='equal')
    ax.set_title(f'40° unnotched adapted Joss damage slope · t={time:.6g} s · {phase}\n'
                 'Actual native particle domains · staged mass scaling/resets retained · no physical validation')
    ax.grid(alpha=.2)
    fig.colorbar(collection, ax=ax, label='Actual native damage d (0–1)', shrink=.8)
    fig.savefig(target, dpi=100)
    plt.close(fig)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--video', action='store_true')
    args = parser.parse_args()
    run, output = args.run_dir.resolve(), args.output_dir.resolve()
    if output.exists():
        raise ValueError('Use a fresh review output; preserve previous results')
    status = json.loads(Path(str(run) + '-status.json').read_text(encoding='utf-8-sig'))
    if status['status'] == 'NATIVE_RUNNING' or status.get('nativeExitCode') != 0 or not status.get('nativeComplete'):
        raise ValueError('Complete native exit0 required; preserve partial outputs separately')
    metadata = json.loads((run / 'reference-metadata.json').read_text())
    if metadata['complete'] is not True or metadata['termination'] != 'simulation-time':
        raise ValueError('Native metadata is incomplete')
    output.mkdir(parents=True)
    frozen = output / 'analysis'; frozen.mkdir()
    for source in (Path(__file__), READER):
        shutil.copyfile(source, frozen / source.name)
    with (run / 'timesteps.csv').open(encoding='utf-8-sig', newline='') as stream:
        rows = [r for r in csv.DictReader(stream) if r['phase'] != 'settle']
    if len(rows) != metadata['frames'] or not rows:
        raise ValueError('Saved frame count differs from native metadata')
    first = run / 'vtk/equilibrium.vtk'
    _, initial_fields, initial = check(first)
    if np.any(initial_fields['damage'] != 0):
        raise ValueError('Equilibrium must have zero damage')
    states, records = [], []
    for row in rows:
        path = run / 'vtk' / f"sim_{int(row['step']):05d}.vtk"
        points, fields, record = check(path)
        if abs(record['massPerUnitDepth'] / initial['massPerUnitDepth'] - 1) > 1e-9:
            raise ValueError(f'Mass conservation failed: {path}')
        record.update(timeS=float(row['time']), phase=row['phase'], massScale=float(row['massScale']))
        records.append(record); states.append((points, fields))
    times = [r['timeS'] for r in records]
    if any(b <= a for a, b in zip(times, times[1:])) or times[-1] < metadata['requestedSimulationTime']:
        raise ValueError('Invalid time coverage')
    all_min = np.min([p.min(axis=0) for p, _ in states], axis=0)
    all_max = np.max([p.max(axis=0) for p, _ in states], axis=0)
    bounds = (min(0., all_min[0] - .5), max(60., all_max[0] + .5), min(0., all_min[1] - .5), max(12., all_max[1] + .5))
    result = {'scope': 'Saved-state damage/mass/finite/volume/base integrity, not full F/J/energy balance or physical calibration',
              'integrity': 'PASS', 'nativeComplete': True, 'initial': initial, 'records': records,
              'scientificallyValidated': False, 'landslideVerified': False,
              'display': 'Fixed damage0–1; identical x/y metre scale; full recorded bounds; no interpolation/filtering',
              'analysisHashes': {p.name: digest(p) for p in (Path(__file__), READER)}}
    (output / 'review.json').write_text(json.dumps(result, indent=2) + '\n')
    draw(*states[-1], times[-1], records[-1]['phase'], bounds, output / 'damage-final.png')
    if args.video:
        frames = output / 'frames'; frames.mkdir()
        initial_points, initial_fields, _ = check(first)
        draw(initial_points, initial_fields, 0., 'post-equilibrium, before damage', bounds, frames / 'frame_00000.png')
        for i, ((points, fields), record) in enumerate(zip(states, records), start=1):
            draw(points, fields, record['timeS'], record['phase'], bounds, frames / f'frame_{i:05d}.png')
        ffmpeg = shutil.which('ffmpeg')
        if not ffmpeg:
            import imageio_ffmpeg
            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        log = output / 'ffmpeg.log'
        with log.open('w') as stream:
            subprocess.run([ffmpeg, '-nostdin', '-v', 'error', '-framerate', '4', '-i', str(frames / 'frame_%05d.png'),
                            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(output / 'damage-actual.mp4')],
                           check=True, stdout=stream, stderr=subprocess.STDOUT)
            subprocess.run([ffmpeg, '-nostdin', '-v', 'error', '-i', str(output / 'damage-actual.mp4'), '-f', 'null', '-'],
                           check=True, stdout=stream, stderr=subprocess.STDOUT)
        result['video'] = {'frames': len(states) + 1, 'fps': 4, 'fullDecodeExit': 0,
                           'timeConvention': 'One actual saved state per frame; unequal native time intervals labelled explicitly'}
        (output / 'review.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'integrity': 'PASS', 'frames': len(records), 'final': records[-1], 'output': str(output)}))

if __name__ == '__main__':
    main()
