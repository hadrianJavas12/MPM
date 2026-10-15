"""Regenerate accepted particle plots and compare the decoded accepted video."""
from pathlib import Path
import argparse, csv, importlib.util, json, math, subprocess
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
RUN = ROOT / 'output/reference-reproduction-2026-10-15/dp-physical-pilot'
spec = importlib.util.spec_from_file_location('audited_renderer', ROOT / 'scripts/render-particle-vtk.py')
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)
regenerated = OUT / 'forensic-renders'
regenerated.mkdir(exist_ok=True)
rows = [r for r in csv.DictReader((RUN / 'timesteps.csv').open(newline='')) if r['phase'] != 'settle']
checks = []
for row in rows:
    step = int(row['step'])
    path = regenerated / f'frame_{step:05d}.png'
    args = argparse.Namespace(vtk=RUN / 'vtk' / f'sim_{step:05d}.vtk',
                              output=path, title='DP diagnostic: excessive collapse, uncalibrated',
                              time=float(row['time']), phase=row['phase'], particle_shape='rectangle',
                              xmax=31., ymax=17.3333333333)
    renderer.render(args)
    original = RUN / 'rendered' / path.name
    expected = np.asarray(Image.open(original).convert('RGB'))
    actual = np.asarray(Image.open(path).convert('RGB'))
    checks.append({'step': step, 'pixels_identical': bool(np.array_equal(actual, expected)),
                   'differing_pixels': int(np.any(actual != expected, axis=2).sum())})

standalone_checks = []
for name, step, shape in [('damage-t4.png',2,'ellipse'), ('damage-t40.png',174,'rectangle')]:
    a = np.asarray(Image.open(RUN / name).convert('RGB'))
    standalone = regenerated / name
    row = rows[step - 1]
    renderer.render(argparse.Namespace(vtk=RUN / 'vtk' / f'sim_{step:05d}.vtk', output=standalone,
                                      title='Native DP physical pilot: computed damage', time=float(row['time']),
                                      phase=row['phase'], particle_shape=shape, xmax=31., ymax=17.3333333333))
    b = np.asarray(Image.open(standalone).convert('RGB'))
    standalone_checks.append({'image': name, 'step': step,
                               'particle_shape': shape,
                               'data_plot_and_legend_pixels_identical_below_y90': bool(np.array_equal(a[90:], b[90:]))})

video = RUN / 'native-dp-diagnostic.mp4'
probe = subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries',
                        'stream=codec_name,width,height,r_frame_rate,nb_frames,duration','-of','json',str(video)],
                        check=True,capture_output=True,text=True)
metadata = json.loads(probe.stdout)
process = subprocess.Popen(['ffmpeg','-v','error','-i',str(video),'-f','rawvideo','-pix_fmt','rgb24','pipe:1'],
                           stdout=subprocess.PIPE,stderr=subprocess.PIPE)
nbytes = 1280*720*3
video_checks = []
frame = 0
while True:
    raw = process.stdout.read(nbytes)
    if not raw:
        break
    assert len(raw) == nbytes
    decoded = np.frombuffer(raw, dtype=np.uint8).reshape(720,1280,3).astype(np.int16)
    source = RUN / 'rendered' / f'frame_{frame:05d}.png'
    expected = np.asarray(Image.open(source).convert('RGB')).astype(np.int16)
    delta = decoded - expected
    mse = float(np.mean(delta.astype(float)**2))
    # Lossy video cannot be byte-equal to PNG; compare RGB appearance and data plot.
    video_checks.append({'video_frame': frame, 'png': source.name,
                         'mean_abs_rgb_error_0_255': float(np.abs(delta).mean()),
                         'geometry_mean_abs_rgb_error_0_255': float(np.abs(delta[96:661,72:1080]).mean()),
                         'psnr_db': 10*math.log10(255**2/mse) if mse else None})
    frame += 1
assert process.wait() == 0, process.stderr.read()
assert frame == 175
result = {'method': 'Regeneration uses current audited renderer and supplied CSV times; independent VTK parse recorded separately. H264 comparison is decoded RGB error against each correspondingly numbered PNG.',
          'input_files_modified': False, 'regenerated_frames': len(checks),
          'all_174_pngs_pixel_identical': all(x['pixels_identical'] for x in checks),
          'standalone_data_plots': standalone_checks, 'video': metadata,
          'decoded_video_frames': frame,
          'max_video_mean_abs_rgb_error': max(x['mean_abs_rgb_error_0_255'] for x in video_checks),
          'max_video_geometry_mean_abs_rgb_error': max(x['geometry_mean_abs_rgb_error_0_255'] for x in video_checks),
          'min_video_psnr_db': min(x['psnr_db'] for x in video_checks if x['psnr_db'] is not None),
          'frames': checks, 'video_frames': video_checks,
          'limitations': ['Renderer missing-damage fallback exists at line24 but is unused: every accepted VTK explicitly contains damage.',
                          'Renderer labels time/phase from external arguments or CSV; VTK does not carry a clock.',
                          'Regeneration corroborates plotted saved data, not numerical/scientific validity.',
                          'Rectangles use axis-aligned size_x/y; material rotations are not reconstructed.']}
(OUT / 'forensic-visual-audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('frames','video_frames')},indent=2))
