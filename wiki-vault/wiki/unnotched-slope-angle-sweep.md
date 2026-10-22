# Headless unnotched slope-angle H/HS experiment

**Branch:** `feat/unnotched-slope-angle-sweep`
**Base:** main `9e97e001c2eaf9be81c7b7e39e32fa87f2d6f64b` (2026-10-18).
**Status:** implementation and local-data unit test code committed; real Windows MPM batch and video **NOT_RUN** at this checkpoint.

## Intent and scope

Study angle dependence of progressive failure without artificial toe excavation:
three angle pairs (45, 65, 85 deg), H vs HS, using identical
**M5 Urmi Long-Duration** material law, geometry scale, density, mesh and gravity. All original M5
cases, Studio code and physical constitutive laws are unchanged.

The experiment reuses `cases/cliff/cliff-urmi-long-mc-h.lisp` and
`cases/cliff/cliff-urmi-long-mc-hs.lisp` as scientific baseline,
plus `scenarios/cliff/execute.lisp` two-stage native run, but saves generated
case sources under ignored `output/slope-angle-sweep-urmi-long-6/cases/`.

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

## 2026-10-22 — Long-horizon CFL 0.10 completed in user run

User's isolated 65° HS run reached 300/300 frames = 12,000 MPM updates,
t=10.5674 s; max displacement 12.6932 m, toe runout 11.9153 m,
max kappa 9.3405, minimum friction angle 13°, final kinetic energy
30.307 kJ. Manifest file exists. End-of-log snippet contains no negative-J
error. The 65° HS CFL 0.35 run previously stopped at t=1.6087 s.

**Not yet convergence validated**: independent manifest fields/VTK count and
CFL=0.05 same-physical-time comparisons remain outstanding. Because
settling duration may change with CFL, compare initial states before
inferring timestep-only effects. A constant maximum over several frames
does not imply global mechanical equilibrium. No solver changes made.

## 2026-10-21 CFL probe — 65° HS

A native run at CFL=0.10 and 80×40 updates printed frame 80/80 with
time=2.8406 s, max displacement 7.8735 m, max kappa 7.0056, no inversion
error in the provided log tail. This exceeded the prior CFL=0.35 inversion
at t=1.6087 s, supporting strong time-step sensitivity.
**Not yet a validated remedy**: the physical horizon is much shorter
than the original sweep and no timestep convergence check exists.

Next: verify completed manifest and 81 VTK states; run one 65° HS
case at CFL=0.10 for 300 frames (fresh output) and then evaluate
timestep sensitivity at matched physical time. Keep H/HS material
parameters and safety checks unchanged.

## 2026-10-20 native run checkpoint: Jacobian inversion (IN_PROGRESS)

Laptop completed `45 H` and `85 H`; `45 HS` (frame 35), `65 H`
(frame 47), `65 HS` (frame 12) and `85 HS` (frame 12) all stopped with
`ERROR-DF-NEGATIVE`. This is an invalid negative local deformation-gradient
determinant, not a validated physical failure endpoint.

Instrumented `src/core/stress-update.lisp` to print particle position,
velocity, raw deformation gradient increment, negative determinant; and
`scenarios/cliff/execute.lisp` to print failed frame/substep, actual dt and
physical time. **No solver equations, law coefficients, timestep, or inversion
guards were changed.** Added a source regression test and single-case native
reproduction guide at `docs/UNNOTCHED_SLOPE_SWEEP.md`.

Pending: rerun only failing `slope_65_hs.lisp` into new output directory
and inspect `MPM NUMERICAL_FAILURE` / `CLIFF NUMERICAL_FAILURE` entries.
Native diagnostic execution remains **NOT_RUN** at handover. No new
all-six result or MP4 is claimed.

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
