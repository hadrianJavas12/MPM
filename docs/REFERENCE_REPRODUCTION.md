# Joss Bay reference case

The requested target is the cliff shape, progressive crack, collapse and debris
run-out shown in the supplied paper/video. The user clarified that numerical
identity is not required and asked to build from the existing
`examples/chalk/joss.lisp`. Downloading the original research dataset is not a
requirement for this task.

The new `joss-bay` scenario adapts the author example into a bounded CLI/library
runner. It uses the existing CL-MPM solver and a dedicated reference particle
class. The ordinary `studio-cliff` scenario remains available with its existing
defaults. Reference code is experimental: complete-run and reference-comparison
results must be recorded separately from short integration checks. The latest
user priority is actual simulation results; new reference UI controls are deferred.
Their draft is preserved in `output/reference-reproduction-2026-10-14/ui-draft.patch`.

**Latest result and acceptance, 2026-10-15:** the user accepted the actual native
DP pilot's lower-face damage, collapse and run-out as the requested visual result
and asked for a commit. No further calibration is requested. The accepted 40 s
shape still loses more cliff and runs out farther than the supplied video's
221.14 s final image; numerical agreement and scientific validation remain
unproved. The later 40 kPa candidate completed at 221.14 s without collapse.
See [the diagnosis and measured limits](JOSS_DAMAGE_DIAGNOSIS_2026-10-15.md) and
[the preserved acceptance evidence](evidence/joss-collapse-2026-10-15/README.md).

The recovered Antigravity conversation **Clone and Run CL-MPM** confirms that
the native Windows chalk example preceded the UI. Its remembered red cliff base
followed a switch from damage to Von Mises stress coloring; it does not establish
basal fracture. See [ANTIGRAVITY_NATIVE_HISTORY.md](ANTIGRAVITY_NATIVE_HISTORY.md).

The subsequently supplied WhatsApp clip is a separate Joss-shaped case with
an explicit damage0–1 colorbar, visible lower-face damage colors at15.87 s and
red at19.83 s. It corrects the inference that the user's remembered red base
necessarily meant stress. Its exact source run and chronology remain unproved;
the earlier `D:\model\run_joss_simulation.lisp` and matching renderer are leads.
The history report preserves extracted-frame evidence and these limits.

## Sources and parameter decisions

- User PDF: `D:\model\Referensi\1-s2.0-S0266352X25005579-main.pdf`, Sutcliffe
  et al., *Modelling cliff collapse and run-out with the material point method*,
  Computers and Geotechnics 189 (2026) 107608,
  [DOI 10.1016/j.compgeo.2025.107608](https://doi.org/10.1016/j.compgeo.2025.107608).
- User video: `D:\model\Referensi\video.mp4`, H.264, 1280x720, 30 fps, 184 frames,
  playback duration 6.133333 s. Playback time is not the simulator's physical time.
- Author example: [examples/chalk/joss.lisp](../examples/chalk/joss.lisp).
- Detailed page/figure audit:
  `output/reference-reproduction-2026-10-14/paper-spec.md`.

The source example contains experimental branches and differs from the published
baseline: active setup uses Gf=4.8 J/m2, a length scale tied to mesh size, oversize
transition 0.999 and 0.1 transition criteria. It constructs a 15 m cliff over a 2 m
base and includes 6.8 m of upper vertical face. Its phase runner and geometry are
the implementation starting point, while the paper supplies a named reference
configuration. Loading the whole example also introduces interactive globals
and plotting; the Studio path isolates the required construction and phases.

The paper disagrees with itself on Young's modulus: section 6.1 (p.14) says 1 GPa,
Table 5 (p.16) says 100 MPa. Both are exposed explicitly:

| Profile | Configuration file | Basis |
| --- | --- | --- |
| Joss prose | `studio/reference/joss-bay-prose.json` | Prose and consistency with the reported plastic oversize |
| Joss table | `studio/reference/joss-bay-table.json` | Literal table modulus; other listed inputs retained |
| Video candidate | `studio/reference/joss-bay-video-candidate.json` | Explicit inference from the active author example's Gf=4.8 J/m2 and the video/Fig.16 timing pattern; unverified |

The profiles are also served by `GET /api/reference-presets` from
`studio/reference-presets.json`. Provenance says `validated=false` and
`exactMatchProven=false`; the table variant is a sensitivity case rather than a
resolved erratum.

The video candidate is a separate CLI configuration, not in the API/UI profile
catalogue. It retains E=1 GPa and R=0.5 m, reduces Gf to 4.8 J/m2, recomputes
ductility to 53.59975506 with Eq.(44), and targets the video's final displayed
time 221.14 s. The author example uses this lower Gf and Fig.16 shows full-height
fracture at 130.50 s; the video first labels collapse at 124.93 s. These are clues,
not proof of the video's material configuration. Inherited plastic cohesion
1,965,600 Pa is retained and its oversize is not silently recalibrated. Interpret
this candidate only after elastic equilibrium actually converges. The 48 J/m2
profiles remain separate baselines.

Shared reference values:

| Quantity | Value | Source |
| --- | --- | --- |
| Cliff/base height |15.5 m /1 m | Fig. 12 and section 6.1,pp.14-15 |
| Back and beach extent |15.5 m each | Back lengthH is in the paper; beach extent follows example/video |
| Face | Lower78degrees, upper vertical segment6.8 m | Paper angle; upper height from author example/video |
| Toe notch |45 degree ramp,0.5 m depth | Paper p.15 assumed notch |
| Mesh/MPs |h=1/6 m;3MPs per axis=9 per2Dcell;four boundary bisections | Paper p.15; h is rounded0.166/0.167 in the paper |
| Density / Poisson ratio |1700 kg/m3 /0.24 | Table 5 |
| Plastic c/phi/psi |1,965,600 Pa /50 degrees /0 degrees | Table 5:26x75.6 kPa |
| Damage cohesion/friction |26,000 Pa /50 degrees | Table 5 |
| Gf / nominal R |48J/m2 /0.5 m | Table 5,Fig. 13 |
| Damage delay/exponent |10 s /2 | Table 5; assumed rather than measured creep calibration |
| Residual degradation |Tensile1, compression0, shear0.51 | Table 5; these are degradation parameters, not remaining stiffness fractions |
| Accelerate mass scale |10,000 | Section6.2 |
| Transition threshold |0.01 for both criteria | Algorithm1,p.11 |
| Physical output/check intervals |Accelerate1s, collapse0.1 s | Section6.2,p.16 |

The tensile initiation stress is derived through the engine's cohesion-to-tensile
conversion: 18,926.452 Pa. Eq.(44) gives
`eta=2*Gf*E/(R*sigma_t^2)`; the helper is called with its explicit `k=1`, since
the helper default `k=2` is a different estimate. The resulting ductilities are
535.99755 (prose) and 53.59976 (table). With `d_p=0.99`, Eq.(57),

```text
omega=0.5*(eta-1)*W0(2*exp(2/(eta-1))/((1-d_p)*(eta-1)))
```

gives 75.64918 for the 1 GPa variant, matching the printed 75.6 oversize after
rounding. This is an inference supporting the prose profile; it is not proof
of the original run configuration. Explicit plastic cohesion is retained in
both profiles so the inherited constructor cannot silently replace it.

For the reference material, initiation stress and ductility are derived from
damage cohesion/friction, Gf, R and E at construction. The redundant generic
`initiationStress`/`ductility` entries in a JSON profile are not independent
reference controls; editing only those entries does not override the derived law.

## Geometry and material path

`studio/lisp/reference-joss.lisp` constructs the two-segment face and 45 degree
notch while preserving the 1 m foundation. Boundary-intersecting particle domains
are bisected up to the configured limit and re-tested. MP domains use det(F)
updates, following the paper's debris discussion. The profile selects the
dedicated `joss-reference-chalk` material: a custom editor method cannot be
combined with this reference scenario, and API/export/runner reject that pair.

The source audit found friction angle conventions and constructor-derived
cohesion/residual properties that need explicit handling. Reference methods
pass the damage criterion its expected angular unit and restore the prescribed
plastic cohesion/friction/dilatancy and degradation ratios after construction.
These overrides are confined to the reference classes.

The current reference damage drive is the author Joss **Drucker–Prager**
criterion evaluated with the stored radian friction angle. A strict frozen-state
comparison found lower-region nonlocal drive 50.409 kPa with DP versus 16.076 kPa
with the preceding MC criterion, below the correct 18.926 kPa initiation stress
for MC. This explains the prior missed lower-face initiation in that prepared
state; it does not prove the reference parameters or full failure sequence.
The index-1 elastic foundation/beach retains damage and plasticity disabled.

Paper Fig. 12 does not dimension the upper-face kink height or beach width.
The chosen 6.8 m upper segment and beach aspect 1 are attributed to the author
example/video rather than invented as exact paper values. The current reference
implementation also follows the author's F-bar choice; the paper discusses
F-bar variants and later instability separately. Inspect actual VTK geometry,
particle mass and final finite state before interpreting the collapse.

## Simulation phases and output

Initial self-weight equilibrium runs with physical mass and both plasticity and
damage evolution off. Only a converged state starts the fracture clock. The
bounded setup reports an error if its equilibrium criteria fail before
`settleMaxSteps`; it does not silently use an unconverged initial state.

The current default uses the author's native cut-cell aggregation. Its diagnostics
combine physical bulk nodal energy/work with aggregate constrained kinetic
energy and displacement/external-work terms. OOBF uses independent projected
`E^T(internal+external)` and `E^T external` L2 norms, excluding damping and
dependent exterior degrees of freedom. The earlier nonaggregate diagnostic
weights nodal quantities by mapped volume `V/h^2`. Neither is claimed to reproduce
the paper's ambiguous Eq.(67) literally; metadata names the actual convention.
Reference damping
uses `beta_crit=(pi/2)*sqrt(E/(rho*h^2))`. The core applies `-damping*M*v` while
the paper applies `-2*beta*M*v`, so the configured core coefficient is twice
the selected beta. Initial relaxation uses `beta=0.1*beta_crit`; later phases
use `beta=1e-4*beta_crit`. Both conventions are recorded in result metadata.

After equilibrium, the physical fracture clock resets to 0, damping becomes
`1e-4*beta_crit`, and plasticity/damage are enabled in the cliff while remaining
disabled in the foundation/beach. The runner advances with a
CFL-limited dt to the next physical interval:

1. **Accelerate:** mass scale 10,000; change to collapse when energy/work or OOBF
   exceeds 0.01.
2. **Collapse:** mass scale 1; return to accelerate only when both measures are
   below 0.01. Returning resets accumulated work and particle velocities.

The ordinary Studio `substeps` loop is not the reference time integrator.
`simulationTime` is the target physical duration; `maxSteps` caps recorded
frames. A frame cap can stop a run before the requested duration. Read
`reference-metadata.json`: `complete=true` only means the requested duration was
reached, and `scientificValidation` remains `unverified`.

Outputs include mesh/initial/equilibrium and per-frame VTK, PNG frames,
`timesteps.csv`, `transitions.csv`, and `reference-metadata.json`. CSV records
physical time, preparation time, phase, mass scale, kinetic energy, work, energy ratio, OOBF,
total mass, mass-weighted damage and particle count. Output counts may change
through particle splitting; particle count alone is not conserved mass.

## Running and comparison

From the configured repository root:

```bat
windows\cl-mpm.cmd studio\lisp\run.lisp studio\reference\joss-bay-prose.json output\joss-prose
windows\cl-mpm.cmd studio\lisp\run.lisp studio\reference\joss-bay-table.json output\joss-table
windows\cl-mpm.cmd studio\lisp\run.lisp studio\reference\joss-bay-video-candidate.json output\joss-video-candidate
```

Reference runs use the built-in dedicated material and need no arbitrary-Lisp
opt-in. The schema is the shared API/Lisp/export specification. The prepared
profile labels and API are available for later UI integration; the current
deliverable is the CLI/library path and captured simulation results.

The bounded integration smoke is:

```bat
windows\cl-mpm.cmd scripts\joss-reference-smoke.lisp
```

It deliberately uses coarse 1 m mesh, short physical time and looser initial
convergence. It checks geometry/mass, units/material construction, finite state,
adaptive-state decisions and rejection of failed equilibrium; it does not show
the published collapse.

`scripts/compare-reference-video.py` compares a particle VTK against an extracted
reference-video frame using a calibrated world-to-pixel map, occupancy IoU,
rightmost material above the foundation and a top-plateau row. Supply the actual
simulator and reference-title time explicitly:

```bat
python scripts\compare-reference-video.py --vtk output\reference-reproduction-2026-10-14\fine-geometry\initial.vtk --reference-frame output\reference-reproduction-2026-10-14\video-frames\frame_001.png --reference-time 0 --simulation-time 0 --output output\reference-reproduction-2026-10-14\initial-comparison.json
```

This checks initial geometry at time 0. For deformed states, select the VTK by
its recorded simulator time and a reference frame by its displayed title time.
Use the bundled Python if system Python lacks NumPy/Pillow. The tool does not
OCR time labels or infer time from VTK. IoU measures approximate image geometry,
not numerical/physical accuracy; damage colors are not compared because the
video colorbar is adaptive. Ellipse footprints ignore particle rotation; run-out
edges are threshold/outlier sensitive and the plateau is a row-based proxy.

## Verification state and limits

The latest completed integration evidence is
`output/reference-reproduction-2026-10-15/validation/validation-summary.json`:
`npm run check` passed, Node tests passed 36/36 with no skips including three
actual Windows SBCL contracts, and one native reference smoke produced four
finite VTKs/two PNGs with zero damage in 124 protected base MPs. Its 179-step
preparation and 0.02 s frame-limited result are integration checks. The one-step
failed-equilibrium guard also passed.

The strict aggregate frozen-state probe converged in 1658 updates, with energy
ratio 5.068e-9 and OOBF 9.9667e-5. The subsequent **actual DP physical pilot**
reached 40 s/174 frames, with lower-face damage in the first saved damaged frame
at t=4 s (max 0.333589, upper region 0), finite fields and constant mass
425664.0625 kg/m across 4155 MPs. Its final mass-weighted damage is 0.493673.
There is actual collapse/run-out, **visually accepted by the user**. The
quantitative image comparison remains a mismatch:
comparison against the main reference's final 221.14 s image gives occupancy
IoU 0.699825, run-out edge +7.8 m and plateau edge −5.2 m. This is a shape
comparison at different times, not an accuracy percentage or timing agreement.
Evidence: `output/reference-reproduction-2026-10-15/dp-physical-pilot/`.
The [accepted video](evidence/joss-collapse-2026-10-15/accepted-collapse.mp4) and
[final image](evidence/joss-collapse-2026-10-15/accepted-collapse-t40.png) are
preserved with configs, CSVs, metadata, audits, source provenance and validation
logs in [the commit evidence bundle](evidence/joss-collapse-2026-10-15/README.md).
The captured pilot used a saved strict-equilibrium warm start; the bundle
distinguishes that historical continuation from a fresh production CLI replay.

The single `strength-40k-run` candidate completed **221.14 s / 111 frames**,
using 40 kPa damage
initiation, derived cohesion 54949.548389 Pa/ductility 12, unchanged Gf 4.8 J/m²
and delay 10 s. Final maximum damage is **0.49062952033**, mass-weighted damage
**0.008064637675**; its final phase is accelerate and it did **not** collapse.
The raw request was a 5000-frame cap; schema normalization made the effective
cap 2000, and the duration target was reached before it. This is unverified calibration
motivated by the measured lower/upper DP drives, not literal paper parameters.
Its [final damage image](evidence/joss-collapse-2026-10-15/latest-40k-t221.png)
is preserved separately from the accepted pilot's collapse. The continuation
heartbeat `mpm-lanjut-setelah-reset` is confirmed **PAUSED** after acceptance;
no further simulation or calibration is requested.

Earlier evidence below is retained as history. The nonconverging physical-mass
pilot was interrupted after more than 37000 settling updates; the corrected
nonaggregate equilibrium then converged at 3898 updates. The later raw low-Gf
trajectory stopped at t=111 s with localized upper-face damage, without the
target collapse. That old candidate is no longer running.

| Captured check | Result | Evidence under `output/reference-reproduction-2026-10-14/` |
| --- | --- | --- |
| Node/SBCL contracts | 36 passed, 0 failed/skipped | `node-tests.log` |
| Ordinary elastic smoke | Passed, 100 particles/50 updates | `standard-smoke.log` |
| Built-in/custom delegate smoke | Passed, zero position/stress difference and finite VTK | `custom-smoke.log` |
| Coarse reference smoke | Finite short integration; unfinished frame cap | `joss-reference-smoke.log`, `joss-smoke-output-verification.json` |
| Fine initial geometry | 82,351 MPs, mass 425,920.5054 kg/m, finite VTK, zero initial damage | `fine-geometry/geometry-summary.json`, `fine-geometry/initial.vtk`, `fine-geometry/initial-data-plot.png` |
| Corrected strict equilibrium | Converged at update 3,898; F-bar on, no damage | `diagnose-corrected.log`, `diagnose-corrected/equilibrium.vtk` |
| Reference cache parity | Two updates, 37 point/scalar fields, exact zero difference for 4,155 MPs | `fast-parity.json`; this does not establish a speed improvement |

Full-resolution initial geometry/finite VTK was generated independently;
the attempted gnuplot PNG hit the five-second completion timeout. A separate
scientific render of the initial VTK is geometry evidence, not a time-history
simulation. The newer native checks and physical pilot are recorded above.
Previous custom-delegate export
parity in [the Windows report](windows-verification-2026-10-14.md) tests a
different scenario and does not validate this new reference path.

The user accepted the actual DP pilot's visual damage/collapse/run-out and
requested a commit recording successful collapse. The result has finite output
and explicit time/phase records.
Exact source-data identity, physical calibration, mesh convergence and matching
every video pixel are separate claims. The original author dataset remains an
optional future quantitative reference; it is not being required or downloaded
for the user's clarified target.
