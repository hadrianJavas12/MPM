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
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle
import numpy as np

reader_spec = importlib.util.spec_from_file_location('vtk_reader', Path(__file__).with_name('compare-reference-video.py'))
reader = importlib.util.module_from_spec(reader_spec)
reader_spec.loader.exec_module(reader)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def comparison_plot(candidate, baseline, context):
    """Overlay saved curves; the 3D reference is explicitly contextual only."""
    sources = [('2D sebelum refactoring', baseline, '#10273f', '-', 3.0),
               ('2D sesudah refactoring', candidate, '#dd8019', '--', 2.0)]
    if context is not None:
        sources.append(('3D benchmark lama (konteks)', context, '#047f9d', ':', 2.0))
    fig, axes = plt.subplots(1, 2, figsize=(13.6, 6.2), facecolor='#f7f9fc')
    fig.suptitle('REGRESI TRIAXIAL  |  Kurva native sebelum dan sesudah refactoring',
                 fontsize=16, weight='bold', color='#10273f', y=.96)
    fig.text(.05, .875, 'Kesetaraan diuji pada kasus 2D yang sama; 3D adalah konteks dengan kondisi kinematik berbeda.',
             fontsize=10, color='#52667b')
    provenance = {'method': 'Original CSV samples overlaid directly, without interpolation or fitting',
                  'rendererSourceSha256': sha(Path(__file__).resolve()),
                  'threeDimensionalCurveIsContextOnly': True, 'inputs': []}
    for label, directory, color, style, width in sources:
        directory = directory.resolve()
        csv_path = directory / 'stress-strain.csv'
        config_path = directory / 'effective-config.json'
        configuration = json.loads(config_path.read_text(encoding='utf-8-sig'))
        dimensions = int(configuration.get('spatialDimensions', 3))
        expected = 3 if directory == (context.resolve() if context else None) else 2
        if dimensions != expected:
            raise ValueError(f'Comparison requires 2D before/after and optional 3D context: {directory}')
        with csv_path.open(newline='', encoding='utf-8-sig') as stream:
            records = list(csv.DictReader(stream))
        x = np.array([float(row['particle_extents_axial_strain_pct']) for row in records])
        for axis, column in zip(axes, ('q_j2_kpa', 'deviatoric_stress_kpa')):
            y = np.array([float(row[column]) for row in records])
            if not (np.isfinite(x).all() and np.isfinite(y).all()):
                raise ValueError(f'Nonfinite recorded comparison curve: {csv_path}')
            axis.plot(x, y, label=label, color=color, ls=style, lw=width)
        provenance['inputs'].append({'label': label, 'csv': str(csv_path), 'csvSha256': sha(csv_path),
                                     'configSha256': sha(config_path), 'samples': len(records),
                                     'spatialDimensions': dimensions})
    for axis, title in zip(axes, ('Invariant q J2', 'Proyeksi q triaxial')):
        axis.set_title(title, color='#10273f', pad=14)
        axis.set_xlabel('Regangan aksial spesimen (%)')
        axis.set_ylabel('Tegangan deviatorik (kPa)')
        axis.grid(color='#e3e9f0')
        axis.spines[['top', 'right']].set_visible(False)
        axis.legend(frameon=False, fontsize=8, loc='lower right')
        axis.set_xlim(left=0)
        axis.set_ylim(bottom=0)
    fig.text(.05, .035, 'Sumber: stress-strain.csv aktual. Parameter clay asumsi; bukan validasi laboratorium.',
             fontsize=9, color='#52667b')
    fig.subplots_adjust(left=.07, right=.97, bottom=.15, top=.76, wspace=.25)
    destination = candidate / 'triaxial-refactor-comparison.png'
    fig.savefig(destination, dpi=150)
    plt.close(fig)
    provenance.update(png=str(destination.resolve()), pngSha256=sha(destination))
    (candidate / 'comparison-visualization-provenance.json').write_text(
        json.dumps(provenance, indent=2) + '\n', encoding='utf-8')
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, help='Final PNG (default RUN/triaxial-result.png)')
    parser.add_argument('--video', action='store_true')
    parser.add_argument('--fps', type=int, default=15)
    parser.add_argument('--baseline-run-dir', type=Path, help='Optional completed 2D pre-refactor run for curve overlay')
    parser.add_argument('--context-run-dir', type=Path, help='Optional old 3D run, labeled contextual only; requires baseline')
    args = parser.parse_args()
    if not 1 <= args.fps <= 60:
        parser.error('fps must be between 1 and 60')
    if args.context_run_dir and not args.baseline_run_dir:
        parser.error('--context-run-dir requires --baseline-run-dir')
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
    projected_stresses = np.array([float(r['deviatoric_stress_kpa']) for r in rows])
    config = json.loads((run / 'effective-config.json').read_text(encoding='utf-8-sig'))
    plane_strain = int(config.get('spatialDimensions', 3)) == 2
    stress_column = 'q_j2_kpa' if plane_strain else 'deviatoric_stress_kpa'
    stresses = np.array([float(r[stress_column]) for r in rows])
    if not (np.isfinite(strains).all() and np.isfinite(stresses).all()
            and np.isfinite(projected_stresses).all()):
        raise ValueError('Nonfinite stress-strain data')
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
    ax = (fig.add_axes([0.06, 0.16, 0.34, 0.66]) if plane_strain
          else fig.add_axes([0.025, 0.14, 0.43, 0.69], projection='3d'))
    curve = fig.add_axes([0.57, 0.20, 0.39, 0.58], facecolor='white')
    mode_title = ('Native 2D MPM - plane strain, unit thickness' if plane_strain
                  else 'Native 3D MPM' if mode == 'mpm'
                  else 'Native constitutive point - homogeneous cylinder')
    geometry_title = (f'{diameter:g} × {height:g} mm rectangle' if plane_strain
                       else f'Ø{diameter:g} × {height:g} mm')
    fig.text(0.045, 0.95, f'TRIAXIAL CLAY  |  {geometry_title}', fontsize=19, weight='bold', color='#10273f')
    fig.text(0.045, 0.906, f'{mode_title}  |  assumed material parameters; laboratory fit not performed', color='#52667b', fontsize=11)
    fig.text(0.045, 0.047, 'Geometry and colour: recorded VTK particles   |   Curve: recorded stress-strain.csv', fontsize=9, color='#52667b')
    status = fig.text(0.57, 0.83, '', fontsize=10, color='#10273f')
    if plane_strain:
        scatter = PatchCollection([], cmap='YlOrBr', norm=norm, edgecolors='white', linewidths=.2)
        ax.add_collection(scatter)
        bar = fig.colorbar(scatter, cax=fig.add_axes([.445, .29, .012, .34]))
    else:
        scatter = ax.scatter([], [], [], c=[], cmap='YlOrBr', norm=norm, s=17, alpha=.95, edgecolors='none')
        bar = fig.colorbar(scatter, ax=ax, shrink=.5, pad=.02, aspect=22)
    bar.set_label('Regangan plastis native (%)', fontsize=9)
    curve.grid(color='#e3e9f0', linewidth=.8)
    curve.spines[['top', 'right']].set_visible(False)
    curve.set_xlabel('Regangan aksial (%)')
    curve.set_ylabel('Tegangan deviatorik (kPa)' if plane_strain else 'Tegangan deviatorik q (kPa)')
    curve.set_xlim(min(0, strains.min()), max(strains.max(), platen_strains.max(), .01) * 1.02)
    ymin, ymax = min(0, stresses.min()), stresses.max()
    curve.set_ylim(ymin - max((ymax-ymin)*.04, .2), ymax + max((ymax-ymin)*.14, 1))
    line, = curve.plot([], [], color='#047f9d', lw=2.5,
                       label='q J2: strain spesimen' if plane_strain
                       else 'Spesimen: tinggi domain partikel' if mode == 'mpm' else 'Native constitutive response')
    comparison, = curve.plot([], [], color='#8798a9', lw=1.5, ls='--', label='Platen: displacement perintah')
    if mode != 'mpm':
        comparison.set_visible(False)
    marker, = curve.plot([], [], 'o', color='#e88925', ms=7)
    projected_line = None
    if plane_strain:
        projected_line, = curve.plot([], [], color='#b76b12', lw=1.5,
                                      label='q proyeksi triaxial: strain spesimen')
    curve.legend(loc='lower right', frameon=False, fontsize=8,
                 handles=([line, projected_line, comparison] if plane_strain
                          else [line, comparison] if mode == 'mpm' else [line]))
    ax.set_xlabel('x (mm)', labelpad=8)
    ax.set_ylabel('Height y (mm)' if plane_strain else 'z (mm)', labelpad=8)
    radial = max(diameter * .65, max(float(np.abs(s[1][:, 0] - cx).max()) * 1000 for s in states) * 1.15)
    ax.set_xlim(-radial, radial)
    ticks = np.arange(-40, 41, 20) if diameter == 70 else np.linspace(-diameter/2, diameter/2, 5)
    ax.set_xticks(ticks)
    if plane_strain:
        ax.set_ylim(-2, height * 1.03)
        ax.set_aspect('equal', adjustable='box')
        ax.grid(color='#e3e9f0', linewidth=.5)
    else:
        ax.set_zlabel('Height y (mm)', labelpad=8)
        ax.set_ylim(-radial, radial)
        ax.set_yticks(ticks)
        ax.set_zlim(-2, height * 1.03)
        ax.set_box_aspect((diameter, diameter, height))
        ax.view_init(elev=17, azim=-55)
    ax.set_facecolor('#f7f9fc')
    ax.set_title('Recorded particle domains (x-y)' if plane_strain else 'Recorded specimen state', fontsize=11, pad=10)
    frame_dir = run / 'visualization-frames'
    if args.video:
        frame_dir.mkdir(exist_ok=True)
    chosen = range(len(rows)) if args.video else [len(rows)-1]
    for index in chosen:
        _, points, fields = states[index]
        if plane_strain:
            scatter.set_paths([Rectangle(((p[0] - cx - sx / 2) * 1000,
                                          (p[1] - bottom - sy / 2) * 1000),
                                         sx * 1000, sy * 1000)
                               for p, sx, sy in zip(points, fields['size_x'], fields['size_y'])])
        else:
            scatter._offsets3d = ((points[:, 0]-cx)*1000, (points[:, 2]-cz)*1000, (points[:, 1]-bottom)*1000)
        scatter.set_array(fields['plastic-strain'] * 100)
        line.set_data(strains[:index+1], stresses[:index+1])
        comparison.set_data(platen_strains[:index+1], stresses[:index+1])
        if projected_line is not None:
            projected_line.set_data(strains[:index+1], projected_stresses[:index+1])
        marker.set_data([strains[index]], [stresses[index]])
        row = rows[index]
        strain_text = (f'Spesimen {strains[index]:.2f}% / platen {platen_strains[index]:.2f}%'
                       if mode == 'mpm' else f'Axial strain {strains[index]:.2f}%')
        stress_text = (f'q J2 = {stresses[index]:.2f} / q proyeksi = {projected_stresses[index]:.2f} kPa'
                       if plane_strain else f'q = {stresses[index]:.2f} kPa')
        status.set_text(f"{strain_text}   |   t native = {float(row['time_s']):.3f} s\n{stress_text}   |   {len(points):,} material points")
        if args.video:
            fig.savefig(frame_dir / f'frame_{index:04d}.png', dpi=120)
    output = args.output or run / 'triaxial-result.png'
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150)
    plt.close(fig)
    result = {'kind': 'scientific visualization of saved native outputs', 'simulationMode': mode,
              'rendererSourceSha256': sha(Path(__file__).resolve()),
              'spatialDimensions': 2 if plane_strain else 3,
              'geometryInterpretation': ('plane strain rectangle, unit out-of-plane thickness, not axisymmetric'
                                        if plane_strain else '3D cylinder'),
              'primaryStressColumn': stress_column,
              'primaryStrainColumn': strain_column, 'platenStrainShownSeparately': mode == 'mpm',
              'forwardModelComputedByRenderer': False, 'csv': str(csv_path), 'csvSha256': sha(csv_path),
              'png': str(output.resolve()), 'pngSha256': sha(output), 'frames': len(rows),
              'nativeSimulationDurationS': float(rows[-1]['time_s']),
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
        result['playbackSeconds'] = len(rows) / args.fps
    (run/'visualization-provenance.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    if args.baseline_run_dir:
        result['comparisonPng'] = str(comparison_plot(run, args.baseline_run_dir, args.context_run_dir).resolve())
    print(json.dumps({k:v for k,v in result.items() if k != 'vtkInputs'}, indent=2))

if __name__ == '__main__':
    main()
