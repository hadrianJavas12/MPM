# Saved-result diagnosis: unnotched SRF1.6 composite-apex trial

26 October 2026, Asia/Jakarta. Read-only synthesis of the existing native
manifest/history, FIRST successful frozen `variant-review-002/review.json`,
its existing scale1 PNG, and the already completed static/coarse/fine notes.
No solver, capsule, audit, rendering, literature search or numerical aggregation
was repeated. Proposed work below is **NOT_RUN**.

## Finding

The saved response is **transient elastoplastic downslope deformation that
arrests, including lateral spreading and settlement**. It is not verified
continuing sliding/run-out, and calling it natural material creep is unsupported.
This perfect rate-independent model has no constitutive creep/viscosity,
pore-pressure evolution or damage/strength-softening law. Nonzero small terminal
velocities alone cannot establish creep or a coherent moving mass.

Native source `354273763ad43f3efc48163c7d2d245d977d3402` completes 6s,
7,740 updates, 61 states and 880 MPs. Native integrity/variant/source287/DLL
checks pass. Both fixed-metre motion windows are NOT_DETECTED, with zero
mass beyond x32.5m. This is a valid negative numerical result within its
declared scope, not scientific validation or proof that the physical slope
cannot fail.

## Direct observations from existing outputs

The fixed initial upper cohort contains 576 MPs, mass293678.269338kg/m.
Whole-run centroid displacement at6s is (+63.987,-36.197)mm; the2–6s increment
is (+44.893,-21.262)mm. These are real finite displacements, not just colour
changes. However, the displacement levels off and velocity changes sign:

| Saved time | Cohort dx from0 | Cohort mean vx | Native kinetic energy |
| --- | ---: | ---: | ---: |
| 2.0s, gravity ramp ends | 19.094mm | +0.0498213m/s | 951.6448J/m |
| 2.2s | 29.512mm | +0.0542061m/s | 1093.3866J/m |
| 3.0s | 61.401mm | +0.0190687m/s | 129.0284J/m |
| 3.3s | 64.017mm | -0.00125770m/s | 0.613560J/m |
| 4.0s | 63.958mm | +0.00134545m/s | 0.514917J/m |
| 6.0s | 63.987mm | -0.000339551m/s | 0.134765J/m |

The later sign-changing motion and nearly fixed displacement, after the early
post-ramp acceleration, support arrest/ringing rather than sustained secular
sliding. Plastic dissipation and numerical transfer may remove energy even
with damping=0; these saved diagnostics do not close an energy balance.
The final maximum speed0.0080684m/s is an extremum, not the cohort velocity.
Its RMS speed is0.000905961m/s and terminal velocity coherence0.37912.

At6s maximum displacement is0.182791m, maximum accumulated kappa0.05454545
and minimum J0.99672215. The existing scale1 PNG shows lower-face/toe plastic
localisation and a continuous outline, with no separated mass/runout. Kappa
is plastic history, not damage; here it does not reduce the already constant
c6250Pa/friction angle. The predeclared displacement-based moving-component
fractions remain zero, so a speed-only moving fraction is not an alternative
success criterion.

The added apex mode actually activates: saved1.8s has2 last-active MPs,
2.2s has24, and3.0s has62. Maximum cumulative plastic volume is0.001252879
at3s and0.001470018 at4,5 and6s; those last three snapshots have zero
last-active MPs. Thus the extension resolves the strict model's excluded
tensile-apex domain and permits additional plastic volume, but does not
generate continuing global instability. Last q is not a sparse-frame volume
increment. No conclusion about every unsaved substep follows.

Mass remains448675.133710kg/m. There is no saved center exit or floor
penetration. Minimum particle-domain margin across the review is approximately
-8.525micrometres, despite positive center margins. Full particle-domain/kernel
support containment and a calibrated runout bed are consequently not certified.

## What remains unresolved

The fixed bottom is the **declared physical anchoring condition** of this
D1-inspired adaptation. It must not be released, made frictional, or moved
downward merely to obtain motion. Separately, a finite GIMP/grid interpolation
couples MPs above y=0 to constrained basal nodes over a mesh-dependent support
region. That numerical representation can restrict a thin near-base mechanism;
its magnitude has not yet been measured. This is a testable hypothesis, not
proof of a boundary bug or locking.

The old restricted Bishop minimum has arc clearance only0.0840671m above
the base, entryx9.75m/exitx31.390625m. This is below both h1m and h0.5m,
and below either first-row particle-center height0.25m/0.125m. Its formal
F1.383870236 includes six negative slice normals, minimum about-7.171kPa.
It therefore cannot establish a physical critical factor or require MPM
collapse at1.6. Simply discarding/clamping those normals would not solve the
tension/force-equilibrium problem.

The earlier same-physics h1/h0.5 comparison was strict SRF1.4, not this new
SRF1.6/composite model. It showed more deformation at h0.5 but no coherent
motion. It proves sensitivity, not convergence for either case. Volumetric or
shear locking has not been isolated; nu0.3, zero regular dilation and Fbar=false
alone do not diagnose it. The Xie Figure7 foundation/polygon is still not
visually verified; its implicit B-spline formulation and reported foundation
must not silently be identified with our220m2 zero-foundation polygon.

## One finite next gate: basal support/kinematic representation first

**Prefer a cheap, non-time-stepping boundary/support diagnostic before another
full h0.5 run.** There is no positive coarse slide to confirm, and halving h
still does not resolve the0.084m static basal clearance. More movie duration,
a larger SRF, a foundation layer or altered strength is not justified by the
observed arrest.

Freeze one small diagnostic protocol and exact analysis sources, then:

1. Read the existing initial geometry/domain sizes and actual frozen GIMP
   kernel/BC definitions for h1 and the already saved h0.5 geometry. Verify the
   same polygon, physical y=0 anchoring and fixed x>2m/y>2m observation region.
   Do not execute a material return or MPM step.
2. For the already retained static minimum only, sample 101 equal-x arc
   locations plus its exact minimum point. Report the physical arc clearance
   and the exact interpolation weight/gradient contributions of y=0 fixed
   nodes in each mesh, with MP-domain/kernel support explicitly distinguished.
   Preserve negative static normals and the existing formal factor; perform
   no new strength/circle search and infer no corrected FoS.
3. Test the same unit tangential slip discontinuity as a **kinematic diagnostic**
   against each constrained interpolation space: report its resolved/smeared
   transition thickness and constrained-node contribution. The displacement
   field is a test input, never exported as a simulated trajectory or proof of
   attainable material flow. Include elementary constant/affine reproduction
   controls before interpreting the result.
4. End with a bounded comparison report. If h0.5 still couples the candidate
   basal mechanism strongly to the fixed-node support, a full h0.5 movie cannot
   settle that hypothesis; first specify the intended physical/reference
   boundary problem. If the representation changes substantially and the
   mechanism is representable without changing the physical anchoring, a new
   **same SRF1.6/same composite-law h0.5 resolution study** is defensible under
   a separate frozen protocol, not labelled confirmation or guaranteed failure.

The kinematic projection does not prove constitutive locking or predict its
collapse factor. It answers a specific lower-cost question before allocating
another long explicit run. The present task remains unmet: no verified
unnotched landslide, field/paper validation or calibrated run-out has occurred.

## Evidence consulted

- This run: `manifest.json`, `history.csv`,
  `variant-review-002/review.json`, `variant-review-002/gravity-slope-review.png`.
- Existing notes: `docs/benchmarks/UNNOTCHED_STATIC_DIAGNOSTIC.md`,
  `docs/benchmarks/UNNOTCHED_MC_GRAVITY.md` (completed same-metre h0.5 comparison),
  `research/notes/unnotched-landslide-2026-10-24/static-reference-audit.md`,
  `post-refinement-study-review.md`, and `strength-reduction-primary.md`.
- No new data aggregation or rerun was necessary for this diagnosis; numerical
  values above are selected existing report/history entries.
