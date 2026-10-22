# Experimental creep toward slope failure

This is a separate total-stress clay demonstration on
`codex/slope-creep-landslide`, derived from the Wang geometry implementation.
It is not the Wang Soil1 Mohr-Coulomb benchmark and does not repair that model's
recorded integration failure. The crest has no actuator or imposed displacement.
Motion follows constant self-weight and a time-dependent material law.

## Material and time convention

The dedicated material is under `materials/models/viscoplastic/clay-creep/`.
It uses isotropic elastic Hencky strain and J2 Perzyna flow:

\[
q_\tau=\sqrt{3J_2(\tau)},\quad
\dot\kappa=\langle q_\tau-Y(\kappa)\rangle/\eta,\quad
Y(\kappa)=Y_r+(Y_p-Y_r)\max(0,1-\kappa/\kappa_s).
\]

The equivalent viscoplastic strain kappa accumulates with physical time;
strength evolves from that strain, never from a prescribed failure time.
All strength/viscosity parameters refer to **Kirchhoff stress**. Flow is isochoric,
with engineering-Voigt shears handled explicitly. A backward-Euler scalar radial
update handles the residual-strength crossing analytically. Parameter sets with
softening modulus `(Yp-Yr)/kappa_s >= 3G` are rejected rather than silently capped.

This is a declared linear overstress variant of the
[Perzyna family](https://ansyshelp.ansys.com/public/Views/Secured/corp/v242/en/ans_mat/rate.html).
It has no creep below its yield threshold and no Kelvin/primary-creep branch.
It does not reproduce a published three-stage clay law. Time-dependent weakening
can permit accelerating deformation under sustained load; actual slope failure
must be assessed from computed outputs, not assumed from the preset.

| Parameter | Demonstration value |
| --- | --- |
| E; nu; unit weight | 20 MPa; 0.25; 20 kN/m3 |
| Peak/residual pure-shear strength at J=1 | 30 / 6 kPa |
| Kirchhoff J2 yield peak/residual | sqrt(3) times the pure-shear strengths |
| Softening equivalent strain | 0.01 |
| Viscosity eta | 50 MPa s |
| Width; relief; base; crest; angle | 20 m; 10 m; 5 m; 10 m; 60 degrees |
| Grid; particles per direction/cell | 1 m; 2 |
| Physical hold | 1 s pilot / 30 s exploratory run |

These are assumptions, not laboratory calibration. The relief comes from the
earlier provisional geometry. The pressure-independent phi_u=0 material is an
undrained-clay **total-stress idealization**, without pore pressure or fluid
coupling; nu=0.25 permits elastic volume change and does not enforce
incompressibility or establish a laboratory undrained path. Kirchhoff strength
differs from Cauchy strength when J differs from1. Local softening has no length
regularization; mesh-independent localization/run-out is not established.

## Execution and evidence

Initialization equilibrates self-weight elastically with creep disabled, requiring
sustained residual/kinetic tolerances. This represents an instantaneous prestress
initial condition. At hold time0, velocities/reporting displacement are zeroed,
stress/F/history are preserved, creep is enabled and loading damping is zero.
There is no mass/time scaling, displacement amplification or programmed collapse.

```powershell
Set-Location D:\MPM
.\scripts\run-slope-creep.ps1 -OutputDirectory D:\MPM\output\creep-pilot-FRESH -MaxWallHours 1
```

After the pilot passes operational checks and is reviewed:

```powershell
.\scripts\run-slope-creep.ps1 `
  -Case cases/benchmarks/clay-creep-slope.lisp `
  -OutputDirectory D:\MPM\output\creep-30s-FRESH -MaxWallHours 4
```

The Windows wrapper records source commit, frozen CLI source/native proof,
process/exit status, case and analysis hashes, and a native wall budget. It
automatically audits/plots/renders genuine saved VTK/CSV after native completion.
Do not actively poll or duplicate jobs. Native completion is not scientific
validation. The case retains `landslideVerified=false` until evidence is reviewed.

`creep-history.csv` records time, crest displacement/speed, maximum displacement,
speed, kappa/rate, strength, kinetic energy, residual, mass/count and minimum J.
VTKs contain native positions and creep fields. The plots show actual displacement
and physical time. Output histories now use exception-safe closure; failure remains
incomplete and does not delete flushed CSV rows.

Required controls: held stress produces continued creep, held strain relaxes,
hydrostatic/under-threshold loading has no shear creep, softening accelerates
material creep under constant stress, timestep refinement and failure rollback.
Then check native particle conservation, finite positive J/volume, gravity/reset,
and VTK/CSV consistency. For the slope, inspect motion, localization and run-out
plus velocity/strain curves before describing a creep-to-landslide transition.
No failure threshold or simulation trajectory is tuned to force a PASS.

## Verified controls, 2026-10-22

Actual Windows native tests on **33eed96** passed:13 material controls,4 retained
history controls,2 scenario controls (including an expected failed gravity
initialization with CSV and complete=false). Node check and36 tests passed.
PowerShell parsing and Python compilation passed. These checks have different
scope from a successful full slope run; do not rerun them on an unchanged source.

The material tests held q_tau=60kPa for5 physical seconds using accepted native
point updates, including an outer stress-control solve. Constant strength produced
secondary creep; strain softening produced increasing creep rate. The actual CSVs
and plot are retained as material-point evidence, not laboratory or slope results.
Their test parameters are stated in `tests/materials/clay-creep-points.lisp` and
differ from the slope demonstration's viscosity/softening parameters.
Retained evidence: `docs/evidence/slope-creep-2026-10-22/controls/` (19 verified
artifact hashes, including CSV/PNG, exact tests, logs/status and negative manifest).

Pilot001 at04fe2c2 exposed a crest vector/list measurement bug, retained as
FAILED_NATIVE/complete=false with10 evidence hashes in `pilot-001-failure/`.
Sequence-safe reductions fix it at7be4503; the expanded scenario suite passed
3 controls, including vector/list equivalence (5 additional retained hashes).
The material/solver equations were unchanged.

**Actual replacement pilot launched18:24 WIB on2026-10-22 from7be4503**, output
`output/slope-creep-2026-10-22/pilot-002/`; adjacent `-status.json`/`-launch.json`
and native logs identify the job. It completed at18:27 WIB: native/audit/render
exit0,1s/11frames,915 particles, zero mass drift, minJ0.98696. Crest descent was
11.9218mm; maximum displacement13.4915mm and local speed0.053794m/s. Kappa reached
0.00246253; minimum yield fell19.7%.14 verified artifact hashes retain native
source/output/proofs and PNG/MP4 under `docs/evidence/slope-creep-2026-10-22/pilot-002/`.

This establishes an operational pilot and computed creep/strength loss, not a
landslide. Initial activation produces oscillatory velocity/kinetic energy;
max creep rate decreased0.002609→0.002277/s. No accelerating slope failure is yet
verified, and a small kinetic ratio alone cannot establish quasi-staticity.

**30s observation launched19:24 WIB**, sourcea9c3e30, same preset material/mesh,
output `output/slope-creep-2026-10-22/hold-30s-001/`, wrapper50876,4h native budget.
Read the adjacent `-status.json` first. Automated review starts20:00 WIB without
active waiting or repeat tests. Its actual displacement/velocity/localization
must be reviewed before claiming a creep-to-landslide transition.
