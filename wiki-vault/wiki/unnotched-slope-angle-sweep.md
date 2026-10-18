# Headless unnotched slope-angle H/HS experiment

**Branch:** `feat/unnotched-slope-angle-sweep`
**Base:** main `9e97e001c2eaf9be81c7b7e39e32fa87f2d6f64b` (2026-10-18).
**Status:** implementation and local-data unit test code committed; real Windows MPM batch and video **NOT_RUN** at this checkpoint.

## Intent and scope

Study angle dependence of progressive failure without artificial toe excavation:
five angle pairs (45, 55, 65, 75, 85 deg), H vs HS, using identical
**M5 Urmi Long-Duration** material law, geometry scale, density, mesh and gravity. All original M5
cases, Studio code and physical constitutive laws are unchanged.

The experiment reuses `cases/cliff/cliff-urmi-long-mc-h.lisp` and
`cases/cliff/cliff-urmi-long-mc-hs.lisp` as scientific baseline,
plus `scenarios/cliff/execute.lisp` two-stage native run, but saves generated
case sources under ignored `output/slope-angle-sweep-urmi-long/cases/`.

Batch runner: `scripts/sweep_unnotched_slope.py`.
Composite-only video renderer: `scripts/render_slope_montage.py`.
Tests: `tests/test_slope_angle_sweep.py`.
User execution guide: `docs/UNNOTCHED_SLOPE_SWEEP.md`.

No graphs. One MP4 contains all angles and both material models in a single
synchronous-by-update-grid animation from saved VTK geometry and plastic strain.
Each panel displays its own physical time; the run is not time-warped to imply
equal physical time across cases.

## Operational design

- Default sequential native simulation processes, each with two threads, for
  low-memory Windows laptops. Optional `--parallel 2` for two processes.
- Fail-closed before encoding video unless each pair has manifest
  `complete=true`, full frame-index CSV, and every recorded VTK.
- Frozen native source snapshot per run, logs stored next to run directories.
- Completed cases resume; partially completed cases remain preserved.
- Separate final `comparison.csv` consists of numbers only, not a chart.
- Native physics and full end-to-end ffmpeg integration are not yet validated
  on this branch. GitHub Actions on original main were failing; do not claim CI
  success for this work.

## Scientific caution

Visual failure is not a safety-factor measurement. Stiffness, residual
strength, gravitational stress initialization, duration and mesh controls
can change the inferred transition angle. The Urmi exponential-linear law (`beta=-5`, 8 postpeak segments) uses the
original long-run parameters: 12 m height, 4 m base, 48 m shelf, 54 m
runout, 0.5 m mesh, 220 settle steps, and 80×40 dynamic updates.
Only slope angle, removed notch, and the user-controlled native worker count
change by default; the original long benchmark remains untouched.
The existing local MC softening law is mesh-sensitive; this branch is a reproducible exploratory batch,
not a calibrated prediction. Extend to sub-45-degree slopes only after the
canonical config schema and geometry width are deliberately supported.
