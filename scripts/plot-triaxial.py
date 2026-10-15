#!/usr/bin/env python3
"""Plot actual native triaxial particles next to their recorded stress-strain curve.

No forward constitutive response or particle displacement is generated here.
Requires numpy, Pillow, matplotlib, and ffmpeg only when --video is selected.
"""
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
from matplotlib.colors import Normalize
import numpy as np

reader_spec = importlib.util.spec_from_file_location('vtk_reader', Path(__file__).with_name('compare-reference-video.py'))
reader = importlib.util.module_from_spec(reader_spec)
reader_spec.loader.exec_module(reader)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, help='Final PNG (default RUN/triaxial-result.png)')
    parser.add_argument('--video', action='store_true')
    parser.add_argument('--fps', type=int, default=15)
    args = parser.parse_args()
    if not 1 <= args.fps <= 60:
        parser.error('fps must be between 1 and 60')
    run = args.run_dir.resolve()
    csv_path = run / 'stress-strain.csv'
    with csv_path.open(newline='', encoding='utf-8-sig') as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError('No recorded triaxial frames')
    platen_strains = np.array([float(r['axial_strain_pct']) for r in rows])
    strain_column = ('particle_extents_axial_strain_pct'
                     if 'particle_extents_axial_strain_pct' in rows[0] else 'axial_strain_pct')
    strains = np.array([float(r[strain_column]) for r in rows])
    stresses = np.array([float(r['deviatoric_stress_kpa']) for r in rows])
    if not np.isfinite(strains).all() or not np.isfinite(stresses).all():
        raise ValueError('Nonfinite stress-strain data')
    config = json.loads((run / 'effective-config.json').read_text(encoding='utf-8-sig'))
    mode = config.get('mode', 'mpm')
    if mode not in ('mpm', 'homogeneous'):
        raise ValueError('Unknown simulation mode')
    states = []
    for row in rows:
        vtk = run / f"particles_{int(row['frame']):04d}.vtk"
        points, fields = reader.read_particle_vtk(vtk)
        if 'plastic-strain' not in fields:
            raise ValueError(f'Missing plastic strain field in {vtk}')
        states.append((vtk, points, fields))
    p0, f0 = states[0][1:]
    cx, cz = p0[:, 0].mean(), p0[:, 2].mean()
    bottom = (p0[:, 1] - f0['size_y'] / 2).min()
    diameter, height = float(config.get('diameterMm', 70)), float(config.get('heightMm', 140))
    plastic_max = max(float(s[2]['plastic-strain'].max()) * 100 for s in states)
    norm = Normalize(0, max(plastic_max, 0.01))
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.titleweight': 'bold'})
    fig = plt.figure(figsize=(13.6, 7.2), facecolor='#f7f9fc')
    ax = fig.add_axes([0.025, 0.14, 0.43, 0.69], projection='3d')
    curve = fig.add_axes([0.57, 0.20, 0.39, 0.58], facecolor='white')
    mode_title = 'Native 3D MPM' if mode == 'mpm' else 'Native constitutive point - homogeneous cylinder'
    fig.text(0.045, 0.95, 'TRIAXIAL CLAY  |  Ø70 × 140 mm', fontsize=19, weight='bold', color='#10273f')
    fig.text(0.045, 0.906, f'{mode_title}  |  assumed material parameters; laboratory fit not performed', color='#52667b', fontsize=11)
    fig.text(0.045, 0.047, 'Geometry and colour: recorded VTK particles   |   Curve: recorded stress-strain.csv', fontsize=9, color='#52667b')
    status = fig.text(0.57, 0.83, '', fontsize=10, color='#10273f')
    scatter = ax.scatter([], [], [], c=[], cmap='YlOrBr', norm=norm, s=17, alpha=.95, edgecolors='none')
    bar = fig.colorbar(scatter, ax=ax, shrink=.5, pad=.02, aspect=22)
    bar.set_label('Regangan plastis native (%)', fontsize=9)
    curve.grid(color='#e3e9f0', linewidth=.8)
    curve.spines[['top', 'right']].set_visible(False)
    curve.set_xlabel('Regangan aksial (%)')
    curve.set_ylabel('Tegangan deviatorik q (kPa)')
    curve.set_xlim(min(0, strains.min()), max(strains.max(), platen_strains.max(), .01) * 1.02)
    ymin, ymax = min(0, stresses.min()), stresses.max()
    curve.set_ylim(ymin - max((ymax-ymin)*.04, .2), ymax + max((ymax-ymin)*.14, 1))
    line, = curve.plot([], [], color='#047f9d', lw=2.5,
                       label='Spesimen: tinggi domain partikel' if mode == 'mpm' else 'Native constitutive response')
    comparison, = curve.plot([], [], color='#8798a9', lw=1.5, ls='--', label='Platen: displacement perintah')
    if mode != 'mpm':
        comparison.set_visible(False)
    marker, = curve.plot([], [], 'o', color='#e88925', ms=7)
    curve.legend(loc='lower right', frameon=False, fontsize=8,
                 handles=[line, comparison] if mode == 'mpm' else [line])
    ax.set_xlabel('x (mm)', labelpad=8)
    ax.set_ylabel('z (mm)', labelpad=8)
    ax.set_zlabel('Height y (mm)', labelpad=8)
    radial = max(diameter * .65, max(float(np.abs(s[1][:, 0] - cx).max()) * 1000 for s in states) * 1.15)
    ax.set_xlim(-radial, radial)
    ax.set_ylim(-radial, radial)
    ticks = np.arange(-40, 41, 20) if diameter == 70 else np.linspace(-diameter/2, diameter/2, 5)
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.set_zlim(-2, height * 1.03)
    ax.set_box_aspect((diameter, diameter, height))
    ax.view_init(elev=17, azim=-55)
    ax.set_facecolor('#f7f9fc')
    ax.set_title('Recorded specimen state', fontsize=11, pad=10)
    frame_dir = run / 'visualization-frames'
    if args.video:
        frame_dir.mkdir(exist_ok=True)
    chosen = range(len(rows)) if args.video else [len(rows)-1]
    for index in chosen:
        _, points, fields = states[index]
        scatter._offsets3d = ((points[:, 0]-cx)*1000, (points[:, 2]-cz)*1000, (points[:, 1]-bottom)*1000)
        scatter.set_array(fields['plastic-strain'] * 100)
        line.set_data(strains[:index+1], stresses[:index+1])
        comparison.set_data(platen_strains[:index+1], stresses[:index+1])
        marker.set_data([strains[index]], [stresses[index]])
        row = rows[index]
        strain_text = (f'Spesimen {strains[index]:.2f}% / platen {platen_strains[index]:.2f}%'
                       if mode == 'mpm' else f'Axial strain {strains[index]:.2f}%')
        status.set_text(f"{strain_text}   |   q = {stresses[index]:.2f} kPa\nCell target {float(config.get('cellPressurePa', 50000))/1000:g} kPa   |   {len(points):,} material points")
        if args.video:
            fig.savefig(frame_dir / f'frame_{index:04d}.png', dpi=120)
    output = args.output or run / 'triaxial-result.png'
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150)
    plt.close(fig)
    result = {'kind': 'scientific visualization of saved native outputs', 'simulationMode': mode,
              'primaryStrainColumn': strain_column, 'platenStrainShownSeparately': mode == 'mpm',
              'forwardModelComputedByRenderer': False, 'csv': str(csv_path), 'csvSha256': sha(csv_path),
              'png': str(output.resolve()), 'pngSha256': sha(output), 'frames': len(rows),
              'matplotlib': matplotlib.__version__,
              'vtkInputs': [{'file': str(v), 'sha256': sha(v)} for v, _, _ in states]}
    if args.video:
        ffmpeg = shutil.which('ffmpeg')
        if not ffmpeg:
            raise RuntimeError('ffmpeg not found')
        video = run / 'triaxial-simulation.mp4'
        subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-framerate', str(args.fps),
                        '-start_number', '0', '-i', str(frame_dir/'frame_%04d.png'),
                        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(video)], check=True)
        result['video'] = str(video)
        result['videoSha256'] = sha(video)
        result['playbackFps'] = args.fps
    (run/'visualization-provenance.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k != 'vtkInputs'}, indent=2))

if __name__ == '__main__':
    main()
