"""Inspect actual free-creep MPM data; never alter completion or fabricate histories."""
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def read_history(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return [{k: float(v.lower().replace('d', 'e')) for k, v in row.items()}
                for row in csv.DictReader(stream)]


def inspect(run):
    manifest = json.loads((run / 'manifest.json').read_text(encoding='utf-8-sig'))
    rows = read_history(run / 'creep-history.csv')
    if not rows or not all(np.isfinite(list(row.values())).all() for row in rows):
        raise ValueError('Empty/nonfinite native history')
    reader = Path(__file__).with_name('plot_m5_cliff_comparison.py')
    spec = importlib.util.spec_from_file_location('native_cliff_reader', reader)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    snapshots, hashes = [], []
    previous = -1.0
    for index, row in enumerate(rows):
        if row['frame'] != index or row['time_s'] <= previous:
            raise ValueError('Native frames/times are not contiguous and increasing')
        previous = row['time_s']
        path = run / 'vtk' / f'particles_{index:04d}.vtk'
        points, fields = module.read_cliff_vtk(path)
        if not np.isfinite(points).all() or not all(np.isfinite(v).all() for v in fields.values()):
            raise ValueError('Nonfinite saved VTK')
        if len(points) != manifest['particleCount'] or row['particle_count'] != len(points):
            raise ValueError('Particle count changed')
        if not np.isclose(fields['mass'].sum(), manifest['initialMassKgPerM'], rtol=1e-11, atol=1e-8):
            raise ValueError('VTK mass conservation failure')
        if abs(row['mass_error_fraction']) > 1e-12 or row['min_J'] <= 0:
            raise ValueError('Invalid mass or deformation Jacobian')
        if row['max_creep_kappa'] < 0 or row['max_creep_rate_per_s'] < 0:
            raise ValueError('Negative accumulated creep/rate')
        if not np.isclose(np.max(fields['creep-kappa']), row['max_creep_kappa'], rtol=1e-8, atol=1e-12):
            raise ValueError('VTK/history creep state differs')
        snapshots.append((points, fields))
        hashes.append({'path': str(path.relative_to(run)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    if np.any(np.diff([row['max_creep_kappa'] for row in rows]) < -1e-12):
        raise ValueError('Accumulated creep decreased')
    if manifest.get('complete'):
        if not manifest.get('gravityConverged') or not manifest.get('reportingResetPreservedState'):
            raise ValueError('Native completion lacks gravity/reset checks')
        if len(rows) != manifest['config']['frames'] or not np.isclose(rows[-1]['time_s'], manifest['config']['duration'], atol=1e-9, rtol=1e-10):
            raise ValueError('Native completion precedes requested duration/frames')
    audit = {'passedConsistencyChecks': True, 'nativeComplete': bool(manifest.get('complete')),
             'scope': 'Saved native output consistency, not calibrated landslide validation',
             'constantSelfWeight': manifest['loading'], 'frames': len(rows),
             'physicalTimeS': rows[-1]['time_s'], 'maxDisplacementM': rows[-1]['max_displacement_m'],
             'maxSpeedMPerS': rows[-1]['max_speed_m_per_s'],
             'maxCreepKappa': rows[-1]['max_creep_kappa'],
             'creepObserved': rows[-1]['max_creep_kappa'] > 0,
             'strengthLossObserved': rows[-1]['min_yield_kirchhoff_pa'] < manifest['config']['yieldPeakPa'] - 1e-6,
             'scientificValidation': False, 'landslideVerified': False, 'vtk': hashes}
    loading = read_history(run / 'loading-history.csv') if (run / 'loading-history.csv').exists() else []
    if manifest['config'].get('loadingKind') == 'crest-pusher' and not loading:
        raise ValueError('Driven case lacks native contact history')
    if loading:
        if len(loading) != len(rows):
            raise ValueError('Loading/material frame counts differ')
        for row, contact in zip(rows, loading):
            if not np.isfinite(list(contact.values())).all() or not np.isclose(row['time_s'], contact['time_s'], atol=1e-11, rtol=1e-10):
                raise ValueError('Nonfinite or inconsistent loading record')
            if not np.isclose(contact['commanded_settlement_m'], contact['time_s'] * manifest['config']['pusherVelocity'], atol=1e-11, rtol=1e-10):
                raise ValueError('Pusher command differs from declared velocity')
            reaction = contact['reaction_upward_N_per_m']
            if reaction < 0 or not np.isclose(reaction, contact['mapped_reaction_upward_N_per_m'], atol=1e-6, rtol=1e-9):
                raise ValueError('Tensile pusher reaction or force mapping mismatch')
            if min(contact['active_contacts'], contact['separated_contacts'], contact['max_compression_gap_m'], contact['max_separation_gap_m']) < 0:
                raise ValueError('Invalid unilateral contact diagnostic')
            if contact['time_s'] > 0 and contact['active_contacts'] + contact['separated_contacts'] != manifest['pusherContactCount']:
                raise ValueError('Tracked contact count changed')
        audit['unilateralContactHistoryConsistent'] = True
        audit['pusherVelocityMPerS'] = manifest['config']['pusherVelocity']
        audit['soilOutranPusherObserved'] = any(c['measured_patch_settlement_m'] > c['commanded_settlement_m'] + 1e-9 for c in loading)
        audit['zeroLoadFrameObserved'] = any(c['reaction_upward_N_per_m'] == 0 and c['time_s'] > 0 for c in loading)
    return manifest, rows, snapshots, audit


def overview(manifest, rows, snapshots, index, path):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.4), constrained_layout=True)
    points, fields = snapshots[index]
    upper = max(float(np.max(s[1]['creep-kappa'])) for s in snapshots)
    dots = axes[0].scatter(points[:, 0], points[:, 1], c=fields['creep-kappa'],
                           vmin=0, vmax=max(upper, 1e-12), cmap='magma', s=8)
    fig.colorbar(dots, ax=axes[0], label='Accumulated equivalent creep strain')
    config = manifest['config']
    axes[0].set(xlabel='x (m)', ylabel='y (m)', aspect='equal',
                xlim=(0, config['width']), ylim=(0, config['baseHeight'] + config['height'] + config['meshSize']),
                title=f'Actual particles, t={rows[index]["time_s"]:.3g} s')
    history = rows[:index + 1]
    axes[1].plot([r['time_s'] for r in history], [r['crest_settlement_m'] * 1000 for r in history], label='Mean crest descent')
    axes[1].plot([r['time_s'] for r in history], [r['max_displacement_m'] * 1000 for r in history], label='Maximum displacement')
    driven = config.get('loadingKind') == 'crest-pusher'
    command = config.get('pusherVelocity', 0) * rows[-1]['time_s'] * 1000
    if driven:
        axes[1].plot([r['time_s'] for r in history], [r['time_s'] * config['pusherVelocity'] * 1000 for r in history], '--', label='Pusher command (not a soil cap)')
    axes[1].set(xlabel='Actual hold time (s)', ylabel='Displacement (mm)', title='Sustained self-weight; free motion',
                xlim=(0, rows[-1]['time_s']), ylim=(min(0, min(r['crest_settlement_m'] * 1000 for r in rows)),
                    max(1e-6, command, max(r['max_displacement_m'] * 1000 for r in rows)) * 1.05))
    if driven:
        axes[1].set_title('Gravity plus one-way pusher; free separation')
    axes[1].grid(alpha=.25)
    axes[1].legend(fontsize=8)
    completion = 'native complete' if manifest.get('complete') else 'INCOMPLETE'
    fig.suptitle(f'Experimental clay creep | {completion} | no displacement amplification\n'
                 'Assumed J2 Perzyna + local softening; no lab calibration or Wang2017 equivalence', fontsize=11)
    fig.savefig(path, dpi=140)
    plt.close(fig)


def diagnostic_curves(rows, path):
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), constrained_layout=True)
    times = [r['time_s'] for r in rows]
    for key, label in [('max_speed_m_per_s', 'Maximum'), ('crest_mean_speed_m_per_s', 'Crest mean')]:
        axes[0].plot(times, [r[key] for r in rows], label=label)
    axes[0].set(ylabel='Speed (m/s)', title='Measured motion')
    axes[0].legend()
    axes[1].plot(times, [r['max_creep_kappa'] for r in rows], label='Maximum creep strain')
    axes[1].plot(times, [r['mean_creep_kappa'] for r in rows], label='Mean creep strain')
    axes[1].set(ylabel='Equivalent creep strain', title='Native material evolution')
    axes[1].legend(fontsize=8)
    axes[2].plot(times, [r['min_yield_kirchhoff_pa'] / 1000 for r in rows])
    axes[2].set(ylabel='Minimum q_y (kPa, Kirchhoff)', title='Strain-driven strength loss')
    for ax in axes:
        ax.set_xlabel('Actual hold time (s)')
        ax.grid(alpha=.25)
    fig.savefig(path, dpi=140)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--video', action='store_true')
    args = parser.parse_args()
    run = args.run_dir.resolve()
    manifest, rows, snapshots, audit = inspect(run)
    overview(manifest, rows, snapshots, len(rows)-1, run / 'creep-overview.png')
    diagnostic_curves(rows, run / 'creep-diagnostics.png')
    if args.video:
        executable = shutil.which('ffmpeg')
        if not executable:
            raise RuntimeError('ffmpeg is required for video')
        folder = run / 'rendered-frames'
        folder.mkdir(exist_ok=True)
        for index in range(len(rows)):
            overview(manifest, rows, snapshots, index, folder / f'frame_{index:05d}.png')
        subprocess.run([executable, '-v', 'error', '-y', '-framerate', '4', '-i', str(folder / 'frame_%05d.png'),
                        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(run / 'slope-creep.mp4')], check=True)
    (run / 'output-audit.json').write_text(json.dumps(audit, indent=2) + '\n')
    print(json.dumps({k: v for k, v in audit.items() if k != 'vtk'}, indent=2))
    return 0 if manifest.get('complete') else 2


if __name__ == '__main__':
    raise SystemExit(main())
