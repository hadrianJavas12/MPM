# Experimental creep toward slope failure

This is a separate total-stress clay demonstration on
`codex/slope-creep-landslide`, derived from the Wang geometry implementation.
It is not the Wang Soil1 Mohr-Coulomb benchmark and does not repair that model's
recorded integration failure. The completed gravity-only runs have no crest
actuator or imposed displacement: motion follows constant self-weight and a
time-dependent material law. A later unilateral-pusher experiment is in
development, separately identified below; it has not yet been tested or launched.

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
| Completed gravity-only holds | 1 s pilot / 30 s / 120 s observations |

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

**30s observation completed19:39 WIB**, sourcea9c3e30, same preset material/mesh,
output `output/slope-creep-2026-10-22/hold-30s-001/`. Native/audit/render exit0;
61VTKs,915MPs, zero mass drift, minJ0.97840. Crest descent260.8326mm, maximum
displacement298.1695mm, kappa_max0.0582425. Sources/raw data/proofs/media and
review are retained with16 verified hashes under
`docs/evidence/slope-creep-2026-10-22/hold-30s-001/`.

**The creep-to-landslide target is not verified.** The particle overview shows
distributed creep and toe/base strain concentration without a detached sliding
mass/run-out. Crest secant rates decline9.91mm/s (0–5s) to8.34mm/s (20–30s);
local velocity peaks are transient. The minimum strength reaches residual at5.5s,
but strength loss alone does not prove accelerating slope failure.

The subsequently authorized 120 s observation and mechanism review are recorded
below. No strength/viscosity tuning was used to obtain the longer result.
Do not rerun finished tests or outputs.

## User-authorized120s extension

After the30s review the user requested more duration and clarified that speed
and displacement can become greater than the earlier0.005m/s /0.1m references.
The current self-weight scenario applies neither those caps nor artificial
minimum particle velocities/displacements: motion remains a computed response.

`cases/benchmarks/clay-creep-slope-120s.lisp` changes duration to120s and outputs
to241states, preserving0.5s cadence. Actual Windows configuration compilation
atcfc65e9 verified that **all other compiled values are identical**. The5 hashed
control artifacts are retained in `duration-120-config-check/`.

```powershell
.\scripts\run-slope-creep.ps1 `
  -Case cases/benchmarks/clay-creep-slope-120s.lisp `
  -OutputDirectory D:\MPM\output\creep-120s-FRESH -MaxWallHours 4
```

Actual job: source **cfc65e9**, launched **21:38 WIB on 2026-10-22**,
`output/slope-creep-2026-10-22/hold-120s-001/`, wrapper 4680. Native exit 0 and
complete=true at **22:31 WIB**; audit/render exit 0 at **22:33 WIB**.
There is no valid restart checkpoint, so the longer job starts from the same
initial conditions and recomputes0–30s. VTK alone lacks complete restart state.
The self-contained preset avoids live nested-case loads outside frozen provenance.

The completed strict comparison against the preserved first 30 s baseline used:

```powershell
.\toolchain\analysis-venv\Scripts\python.exe scripts\compare-creep-prefix.py `
  --reference output\slope-creep-2026-10-22\hold-30s-001 `
  --candidate output\slope-creep-2026-10-22\hold-120s-001 `
  --output output\slope-creep-2026-10-22\hold-120s-001\prefix-comparison.json
```

This checks exact saved prefix/config/cadence preservation, not calibrated
failure. Assess actual motion, rate trends, localization and run-out separately.
Do not infer that more elapsed time necessarily yields a landslide.

**Result: strict PASS**, all 64 baseline VTK files (including mesh/gravity) and
the first 61 CSV states byte-identical, with the same physical configuration
and 0.5 s cadence. The 120 s run has 241 states and 915 MPs, zero mass drift,
all saved history values finite and minimum J 0.97467. Crest settlement is
0.92059 m, maximum displacement 1.17041 m and maximum kappa 0.274855.

| Raw crest settlement interval | Secant rate (mm/s) |
| --- | ---: |
| 30–60 s | 8.079 |
| 60–90 s | 7.314 |
| 90–120 s | 6.600 |

The declining rates and reviewed particle morphology show continuing distributed
creep and toe/base strain concentration, without a detached sliding mass or clear
run-out. **A macroscopic landslide is not verified.** Retained evidence has
18 artifact hashes in
`docs/evidence/slope-creep-2026-10-22/hold-120s-001/`, including native/source
archives, proofs, CSV/VTK, PNG/MP4, prefix comparison and independent review.

The separate `material-capability-analysis.json` is **analytical 0D reasoning**,
not a new full-MPM run or laboratory test. At a fixed Kirchhoff equivalent stress
q, after residual strength, `kappa_dot=(q-Yr)/eta` is constant for constant eta.
Illustrative assumed stresses demonstrate why this law can approach secondary
creep; more duration alone does not promise a failure transition. Coupled geometry
and stress redistribution remain relevant to the actual slope.

## Unilateral crest-pusher experiment — dynamic release pilot passed

The user's later clarification, "tanah boleh meluncur lebih cepat", was
communicated as a **crest driver descending at 0.005 m/s**, with compression-only
contact so that the soil can move faster and separate. This is distinct from the
completed gravity-only case. It introduces no particle velocity floor, imposed
particle position, time-based strength switch or programmed collapse.

The same uncalibrated clay law and geometry are retained. The fixed crest patch
is **x = 7–10 m**. With +Y upward, each tracked point uses
`y_driver = y_reference - v*t` and
`F_y = -epsilon*b*max(y_predicted - y_driver, 0)`.
Here `epsilon = penaltyScale*M/h`, `penaltyScale = 5`, M is the material P-wave
modulus (Pa), h the mesh spacing (m), and b the original tributary width (m).
Thus epsilon has units Pa/m and F_y is force per out-of-plane metre (N/m);
the reported upward actuator reaction is `-sum(F_y)`. Positive penetration
produces downward compression; separation produces zero force. The prescribed
**5 mm/s command belongs to the driver**, while soil motion remains a solver
result and can exceed it. The compression-only principle is also described in
the [official Itasca linear contact documentation](https://docs.itascacg.com/pfc700/common/contactmodel/linear/doc/manual/cmlinear.html);
this implementation does not reproduce that complete contact model.

This is a tracked original-surface approximation: individual reference heights
are rebased after gravity, original tributary widths are retained, and points
leaving the fixed x patch release. There is **no search for newly exposed or
entering surface particles**, no tangential traction, and no general rigid
platen contact validation. Finite penalty compliance permits penetration;
stiffness/timestep sensitivity remains to be assessed.

Actual Windows tests on **ec285c0** passed **6 contact controls** and **3 scenario
controls**, including retained failure CSV and sequence handling. Node check and
all **36 tests** also passed. The contact controls cover analytical compression
and release, force mapping, timestep availability, lateral release and unchanged
particle state. The named 0.02 m/s control manually places soil ahead of the
driver and verifies velocity non-mutation; it does **not** prove dynamic release
during time integration. The completed native pilot supplies that separate
evidence. Gravity-only compatibility also passed its strict pilot comparison.

`loading-history.csv` adds command, measured patch settlement, reaction/mapped
reaction, active/unloaded counts and compression/separation gaps. Reactions and
gaps come from the last predicted contact evaluation; settlement uses the
current particle geometry. Mean settlement exceeding the command is insufficient
to prove that every contact separated. Review counts and reaction together.
Saved contact samples do **not** provide integrated actuator-work validation or
a closed energy balance.

The bounded case requests **1 s and 11 saved states**:

```powershell
Set-Location D:\MPM
.\scripts\run-slope-creep.ps1 `
  -Case cases/benchmarks/clay-creep-pusher-pilot.lisp `
  -OutputDirectory D:\MPM\output\creep-pusher-pilot-FRESH -MaxWallHours 1
```

`cases/benchmarks/clay-creep-pusher-120s.lisp` also exists (120 s, 241 states),
but the full120s pusher case is **NOT_RUN**. The1s case launched **23:22 WIB,
2026-10-22**, source **ec285c0**, in
`output/slope-creep-2026-10-22/pusher-pilot-001/`, wrapper30008,1h wall budget.
It completed **23:27 WIB**, native/audit/render exit0, **1 s / 11 states / 915
MPs**, zero mass drift. Measured patch settlement was **10.07815 mm**, exceeding
the **5 mm driver command**; maximum particle displacement was13.24341mm and
maximum speed0.0520888m/s. At the0.1s sample all6 contacts were active, upward
reaction3616.041N/m and maximum compression gap22.419micrometres. At every saved
sample from0.2 through1.0s, all6 contacts were unloaded/separated with zero
reaction. These samples demonstrate dynamic release during the pilot; they do
not establish zero force at every intermediate timestep.18 artifact hashes
retain native data, source, proof, media, contact CSV/plot and review in
`docs/evidence/slope-creep-2026-10-22/pusher-pilot-001/`.

The separate1s gravity-only compatibility run
(`gravity-compat-001`, wrapper19844, same source) completed native/audit/render
exit0 and **strict PASS:14 VTK files and all11 CSV states byte-identical** to
pilot-002; physical configuration/cadence unchanged.15 artifact hashes are
retained under `docs/evidence/slope-creep-2026-10-22/gravity-compat-001/`.
The19 hashed control artifacts are in
`docs/evidence/slope-creep-2026-10-22/pusher-controls-001/`.
**Contact implementation/dynamic release PASS; landslide NOT_VERIFIED.** No jobs
remain active. The slow driver loses contact as the soil descends faster; this
result alone does not justify automatically starting a longer pusher run or
tuning material parameters. Laboratory calibration, general surface contact,
repair of the former Wang MC failure and reference-paper agreement remain
unverified. Do not repeat completed jobs.
