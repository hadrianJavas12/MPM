# Automated unnotched slope sweep: H versus HS (headless)

This experiment is kept on `feat/unnotched-slope-angle-sweep`. It does **not**
modify the original M5 cases, Studio, material mathematics, or `main`.

## What it does

`scripts/sweep_unnotched_slope.py` generates a **pair of native CL-MPM cases**
for each requested inclination: identical height, shelf, foundation, geometry,
gravity, constitutive pre-peak parameters, discretization, and time-stepping,
except that H stays on the peak friction/cohesion plateau while HS softens to
residual strength. **No toe notch** (`:notch-height 0d0`).

Default angles: **45, 55, 65, 75, 85 degrees** (10 solver runs).

For every angle the runner uses the existing two-stage MPM cliff implementation:
high-damping elastic gravity initialization, then low-damping elastoplastic
updates. Cases are executed with the repository's source-snapshot-protected
Windows `scripts/run-case.lisp` interface.

**One video only** is created automatically on success:
`output/slope-angle-sweep/all_angles_H_vs_HS.mp4`.

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
Invoke-Item .\output\slope-angle-sweep\all_angles_H_vs_HS.mp4
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

Recommended on low-memory laptops: retain `--parallel 1` (default). The
`--workers` parameter controls threads *per solver*, independently from
`--parallel`. Default is 2 native threads per solver process.

## Output

```text
output/slope-angle-sweep/
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
- Parameters match the existing Zhan-style M5 reference, but are **not**
  calibrated to an arbitrary field slope. The runs are exploratory.
- A visibly motionless frame or small final displacement is **not** proof of
  stability; a moving frame is not in itself a factor-of-safety calculation.
- A fixed output horizon can miss delayed failure; refine duration, angle
  increment, mesh, particle count, and equilibrium checking before making
  scientific claims. Local softening is mesh-dependent.
- This branch only **implements the batch and renderer**. The actual Windows
  solver runs and MP4 must be executed on the user's machine. The Python
  contract tests do not replace native MPM validation.
