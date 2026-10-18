# Automated unnotched slope sweep: H versus HS (headless)

This experiment is kept on `feat/unnotched-slope-angle-sweep`. It does **not**
modify the original M5 cases, Studio, material mathematics, or `main`.

## What it does

`scripts/sweep_unnotched_slope.py` generates a **pair of native CL-MPM cases**
for each requested inclination: identical height, shelf, foundation, geometry,
gravity, constitutive pre-peak parameters, discretization, and time-stepping,
except that H stays on the peak friction/cohesion plateau while HS softens to
residual strength. **No toe notch** (`:notch-height 0d0`).

## Exact reference baseline

This sweep now inherits its parameters from the latest **M5 Urmi Long-Duration**
pair: `cases/cliff/cliff-urmi-long-mc-h.lisp` and
`cases/cliff/cliff-urmi-long-mc-hs.lisp`. The references are preserved intact.

| Component | Urmi Long baseline / sweep default |
| --- | --- |
| Slope height + foundation | 12 m + 4 m |
| Plateau / shelf aspect | 4.0 (48 m) |
| Runout aspect | 4.5 (54 m) |
| Total horizontal domain | 102 m |
| Inclination | Sweep 45°, 55°, 65°, 75°, 85°; replaces 72° |
| Toe notch | Removed (height=depth=0); original used 2.5 m × 2.5 m |
| Grid size | 0.5 m |
| Material points per cell axis | 2 |
| Elastic gravity settling | 220 updates |
| Dynamic simulation | 80 frames × 40 substeps = 3,200 updates |
| CFL scale | 0.35 |
| Constitutive law | `make-urmi-evolution-law`, H plateau vs HS exponential–linear |
| Urmi softening shape | beta = -5, 8 post-peak segments |
| Material | E = 5.25 MPa, nu = 0.2, rho = 1917.07 kg/m³ |
| Cohesion initial/peak/post-rupture/residual | 5/7/4/2 kPa |
| Friction angle initial/peak/post-rupture/residual | 15/20/16/13 degrees |
| Native worker threads per case | Default 2 for a 16 GB laptop; original M5 used 12 |

The script retains parameter overrides for controlled follow-up studies.
For the default experiment, only **angle, removed notch, and available CPU
worker threads** differ from the M5 Urmi Long pair. Equal step counts do
not guarantee equal physical end time because the CFL estimate is dynamic.

Default angles: **45, 55, 65, 75, 85 degrees** (10 solver runs).

For every angle the runner uses the existing two-stage MPM cliff implementation:
high-damping elastic gravity initialization, then low-damping elastoplastic
updates. Cases are executed with the repository's source-snapshot-protected
Windows `scripts/run-case.lisp` interface.

**One video only** is created automatically on success:
`output/slope-angle-sweep-urmi-long/all_angles_H_vs_HS.mp4`.

The video shows **all angles concurrently**, one row per angle, H on the left,
HS on the right. Particles are drawn using the actual saved VTK geometry with
a **shared fixed viewport and fixed plastic-strain color scale**. Each panel
shows its own physical simulation time and summary values. Frame synchronization
means equal *solver output/update indices*, not equal physical times.
No plots or stress-strain charts are produced.

## Run on Windows (PowerShell)

From your local clone and Windows installation:

```powershell
cd D:\MPM
git fetch origin
git switch feat/unnotched-slope-angle-sweep
git pull --ff-only
```

Check native dependencies: the existing `windows\cl-mpm.cmd` must work, and
Python needs `numpy` and `Pillow`, while `ffmpeg` must be on `PATH`.
If your analysis virtual environment is available, use its Python. Otherwise:

```powershell
py -3 -m pip install numpy pillow
ffmpeg -version
py -3 -m unittest discover -s tests -p "test_slope_angle_sweep.py"
```

Run the batch and render the single video **automatically**:

```powershell
py -3 scripts\sweep_unnotched_slope.py
```

Open the final video:

```powershell
Invoke-Item .\output\slope-angle-sweep-urmi-long\all_angles_H_vs_HS.mp4
```

Other useful commands:

```powershell
# Quick plan preview: generate case files WITHOUT running MPM.
py -3 scripts\sweep_unnotched_slope.py --dry-run --output output\preview-sweep

# Only 3 slopes: 6 native simulations. Always use a new output folder for new settings.
py -3 scripts\sweep_unnotched_slope.py --angles 45 60 75 --frames 50 --output output\sweep-3-angle

# Optional two concurrent native simulations, if enough CPU and memory.
py -3 scripts\sweep_unnotched_slope.py --parallel 2 --output output\sweep-parallel

# Re-encode the video from complete saved VTKs WITHOUT rerunning the solver.
py -3 scripts\sweep_unnotched_slope.py --render-only
```

For a ROG Flow X13 Ryzen 9 / 16 GB RAM, begin with `--parallel 2` or use
`--parallel 1` if memory runs short. The
`--workers` parameter controls threads *per solver*, independently from
`--parallel`. Default is 2 native threads per solver process.

## Output

```text
output/slope-angle-sweep-urmi-long/
  plan.json                 immutable sweep parameters
  cases/                   generated case files for each slope/model
  runs/slope_45_h/         native VTKs, CSV, manifests, frozen source snapshot
  runs/slope_45_hs/
  ...                      one pair for each angle
  runs/slope_85_hs/
  runs/slope_45_h.log      captured CLI logs (one log per case)
  comparison.csv           final numerical values only, NOT charts
  ffmpeg.log               encoder errors, if any
  all_angles_H_vs_HS.mp4   ONE tiled montage: all models and angles
```

Rerunning with the same `plan.json` skips cases that have complete manifests,
a complete CSV frame sequence, and all VTK frame files. An incomplete run is
**preserved without deletion** and will stop the batch; investigate its
`.log` and choose a fresh `--output` for a new attempt.
Rendering is withheld until **all** required simulations are complete.
No video frames are fabricated if a native simulation fails.

Changing the sweep parameters in the same output folder is rejected to
prevent mixing different experiments.

## Scope and cautions

- `:slope` is the inclined free-face angle to the horizontal; no toe notch.
- Existing schema restricts `:slope` to 45–90 degrees. This sweep deliberately
  respects that contract instead of silently modifying the Studio shared schema.
- All default material evolution parameters and long-duration geometry match the
  final **M5 Urmi Long** reference except the swept angle, removed notch, and
  reduced compute workers. They are **not** calibrated to an arbitrary field
  slope; the runs are exploratory.
- A visibly motionless frame or small final displacement is **not** proof of
  stability; a moving frame is not in itself a factor-of-safety calculation.
- A fixed output horizon can miss delayed failure; refine duration, angle
  increment, mesh, particle count, and equilibrium checking before making
  scientific claims. Local softening is mesh-dependent.
- This branch only **implements the batch and renderer**. The actual Windows
  solver runs and MP4 must be executed on the user's machine. The Python
  contract tests do not replace native MPM validation.
