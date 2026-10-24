# Native unnotched MC gravity study

Implementation checkpoint, 24 October 2026. See the
[journal-method decision](UNNOTCHED_LANDSLIDE_METHOD_SELECTION.md) and
[frozen study contract](../../research/references/unnotched-mc-ssr/contract.json).

## Experiment and limits

Two independent cases use the existing perfect-plastic, Cauchy-strength MC
material at SRF1 and1.40. Only cohesion and tan(friction) are reduced. SRF1.40
is a critical-bracket trial, not a guaranteed unstable control.

The initial polygon is `(0,0),(32,0),(12,10),(0,10)`m, with empty grid to80m
horizontally and15m vertically. This is a GL D1-inspired adaptation; full Xie
Figure7 geometry has not been visually verified. There is no notch, excavation,
weak seed, driver or hidden wall release. Zero initial stress/velocity and
active plasticity are retained throughout a smoothstep gravity ramp0–2s, then
constant gravity to6s. Actual `sim-gravity` changes; no reporting reset erases
ramp motion. Numerics:1m cells,2MPs/axis,USF/FLIP,dt-scale0.2,one worker,
mass-scale1,no damping/F-bar/splitting/removal. This is a coarse explicit
mechanism study, not the implicit B-spline/F-bar/36PPC paper calculation.

Left/right x rollers, fixed x/y grid bottom and free top are explicit. A fixed
bottom is not Coulomb bed contact. Floor penetration, boundary proximity,
ramp inertia, grid/PPC/dt sensitivity and locking limit quantitative runout
or factor-of-safety claims. Gravity work varies during the ramp; a naive
constant-gravity energy sum is not a closed energy budget.

## Ownership and execution

The existing material and solver are unchanged. Six short files under
`scenarios/gravity-slope/` own configuration, geometry, measurements, advancement
and compatibility. The cases contain component assignments. The scenario
inherits only an existing read-only free-force residual diagnostic; it does
not build the Wang actuator or run its procedure.

First run the focused native gate in a fresh directory:

```powershell
cd D:\MPM
.\windows\cl-mpm.cmd tests\benchmarks\gravity-slope-controls.lisp output\unnotched-gravity-2026-10-24\native-controls-001
```

This freezes the driver, both actual cases, contract, project sources and mapped
DLL before project loading. It checks reduction, polygon/BC/ramp and exactly
two genuine MPM updates with independent saved VTK/CSV readback. It does not
establish slope failure. Preserve failed attempts; saved-output checks can be
repaired without repeating solver updates.

Only after gates and a measured runtime pilot, launch a fresh trial:

```powershell
.\scripts\start-gravity-slope.ps1 -Case cases/benchmarks/gravity-slope-mc-srf-1.lisp -OutputDirectory output/unnotched-gravity-2026-10-24/srf1-001 -MaxWallHours 3
.\scripts\start-gravity-slope.ps1 -Case cases/benchmarks/gravity-slope-mc-srf-1p4.lisp -OutputDirectory output/unnotched-gravity-2026-10-24/srf1p4-001 -MaxWallHours 3
```

Run the pair sequentially for comparable single-worker cost; these commands
are documentation, not automatic launches. The thin alias reuses the existing
CIM launcher while preserving its old Wang default. A separate native monitor
records actual exit, deadline and process identities; completion is labelled
`NATIVE_COMPLETE_REVIEW_PENDING`. WMI remains in a user session; logoff/sleep/
reboot survival is unproven. Snapshots are evidence, not full restart state.

Native output: `manifest.json`, `history.csv`, `particles.csv` and actual
`vtk/particles_####.vtk`. Per-ID CSV includes initial positions, F9/J, physical
stress6, mass/volume, velocity, history/strength and boundary observations. IDs
are captured vector indices, with particle identity/order/count/mass checks.

## Verification chronology

At the implementation checkpoint, native input/output gates, runtime pilot and
paired physical results are **NOT_RUN**. Separate process-monitor fixtures
exercise supervision with zero MPM updates. Static syntax is not native proof.
Later dated findings must retain that distinction and all negative evidence.

Physical review uses the predeclared fixed cohort, connected moving mass and
sustained motion convention, inspecting scale1 geometry/plastic localisation.
Report initial-to-final and post-ramp response separately, and toe crossing as
a separate runout gate. Solver completion, plastic colour or one fast particle
does not prove a landslide. No automatic scientific PASS is produced.
