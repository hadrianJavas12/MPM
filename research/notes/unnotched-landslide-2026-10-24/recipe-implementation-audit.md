# Recommended native recipe: unnotched MC gravity slope with declared SSR

Read-only implementation audit, 24 October 2026. Inspected HEAD
`c5cc79c4fdc5b8b2ec3d9319dfd4ff3013910958`, branch
`codex/wang2017-soil2-landslide`. No production edits, solver, tests, replay,
downloads or changed numerical tolerances. See the adjacent primary-literature
notes for source verification and unverified figure dimensions.

## One recommendation

Implement a separate **perfect-plastic Mohr-Coulomb gravity-slope recipe**, with
independent, predeclared strength-reduction trials at SRF1 and SRF1.40. Use the
Griffiths–Lane D1 geometry as an explicitly declared geometric adaptation until
its complete figure is visually verified. This has the lowest implementation
risk because the repository already has the exact MC surface, a Cauchy-strength
option, constant-strength law, transactional state and material diagnostics.
It requires orchestration and output work, not an invented constitutive law.

SSR deliberately changes strength: `c_F=c/F`,
`phi_F=atan(tan(phi)/F)`. It must not be described as spontaneous failure of
unchanged soil, creep, rainfall, or reproduction of Wang2017. It can address the
user's unnotched failure objective with disclosed inputs and actual gravity
dynamics. SRF1.40 is a published critical-bracket trial, not a guarantee that
this explicit discretisation produces sustained sliding or a specified runout.
No automatic factor search or strength reduction in response to an unsatisfactory
movie is proposed.

The alternative Yu/Kasama case needs its DP cone, strain measure, dilation and
smeared-crack law bound first. Wang2016 needs VM/full-plastic-tensor history,
missing unit weight and a verified Coulomb bed. Copying either into current MC
would introduce more material/contact assumptions than this MC route.

## Input contract to freeze before execution

| Input | Proposed value and provenance |
|---|---|
| Material | Native MC, perfect plasticity; E100MPa, nu0.3, c10kPa, phi20deg, psi0, gamma20kN/m3. These are the Xie et al.2023 MC bridge parameters, not Yu DP parameters. Cauchy cohesion explicitly declared. |
| Scale | H10m, slope arctan(1/2)=26.565deg; gamma implies density `20000/9.80665` kg/m3. |
| Geometry adaptation | D1/no foundation, rear crest1.2H and face projection2H as indexed Griffiths–Lane dimensions. With bottom-left origin, the proposed triangle/trapezoid outline is `(0,0),(32,0),(12,10),(0,10)` m. This polygon is a declared adaptation pending fresh visual figure verification; do not label it exact Xie Figure7. |
| Computational domain | Proposed empty extension to x80m and a top air buffer. Extension contains no initial soil; no notch, excavation, weak strip, actuator or imposed particle trajectory. Declare right-boundary distance and observe whether any particle approaches it. |
| Essential boundaries | Left and right x rollers, fixed bottom x/y, free top. These agree with the reported fixed-bottom/side-roller type. They are not a Coulomb basal-friction model. A bed supporting free runout beyond the original toe needs a separately justified contact design; a fixed grid bottom can influence the deposit. |
| SRF | Independent fresh runs at1 and1.40. At1.40, c=7.142857kPa and phi≈14.57deg; compute the exact angle from the formula, not the rounded value. E, nu, density and psi remain unchanged. |
| Initialization | Zero initial stress and velocity; plasticity active throughout a declared smooth gravity ramp. Ramp duration is an explicit-MPM numerical choice, not the source's implicit step count converted into physical seconds. No elastic settle/plastic activation or reset that discards actual motion. |
| Numerics | A first bounded mechanism pilot may use h1m and2 points per axis (4 PPC), FLIP/USF, mass scale1 and no dynamic damping. This differs from Xie's36 PPC, implicit B-spline and locking treatment; it cannot establish FoS convergence. Physical ramp/hold durations and dt safety factor must be fixed and documented before results, with later sensitivity. |

The source Xie paper now verifies each SRF as an independent analysis; its
gravity is ramped in10 implicit steps below1.38 and100 steps above1.38. That
is useful loading-history evidence, but it supplies no unique physical ramp
duration for an explicit run. Figure7's complete polygon remains visually
unverified. The baseline and reduced trial must share their declared explicit
ramp, grid, particles, dt, domain and reporting times.

## Exact existing implementation map

| Concern | Existing source/function | Reuse and required new owner |
|---|---|---|
| Composable recipe | `src/simulation/components/specifications.lisp`: `make-simulation`, `make-geometry :slope`, `make-boundary :rollers`, `make-loading :gravity`, `make-solver :explicit` | These existing component kinds suffice. A small trusted case should select `:scenario :gravity-slope`; backend-specific duration/ramp settings can live in the parameters object. No global overrides or changes to old cases. |
| Lifecycle | `src/simulation/lifecycle.lisp`: `compile-scenario`, `execute-scenario`, `run-simulation` | Add methods in `scenarios/gravity-slope/adapter.lisp`. Existing `run-simulation` enforces fresh output directories. New configuration validates model, SRF, empty extension and no driver. |
| MC law | `materials/models/plastic/mohr-coulomb-evolution/law.lisp`: `make-evolution-law` | Use `:variant :perfect :points ((0 phi-deg)) :cohesion c-pa :psi 0d0 :stress-measure :cauchy`, with a truthful explicit strain-assumption string. Perfect law has no softening-history fit. `law-values` returns angles in radians. |
| Native material | `materials/models/plastic/mohr-coulomb-evolution/{state,material}.lisp`: `particle-mc-evolution`, `constitutive-model` | Existing dedicated six-plane return, finite-J handling and particle transaction. Keep strict rejection of inadmissible/ambiguous states; no legacy-apex fallback. |
| Factory | `materials/core/definition.lisp`: `make-material :native`; `materials/adapters/native.lisp`: `material-particle-class`, `material-particle-initargs` | Construct `:particle-class 'cl-mpm/models/mc-evolution:particle-mc-evolution` with `:initargs (list :evolution-law law)` and explicit E/nu/density. Do not use `:mc-h` or `:mc-hs` for a perfect law: those adapters check their respective variants. |
| Grid and MPs | `src/geometry/setup.lisp`: `make-simple-sim`, `make-block-mps`; `scenarios/slope-descent/geometry.lisp`: `surface-height`, `make-slope` | New gravity-slope geometry should reuse the stable setup calls and clipping pattern. Separate initial soil width32m from grid width80m: current `make-slope` uses the same width for both. Base height0 preserves D1; do not retain the old5m deformable foundation. |
| Essential BC | `scenarios/slope-descent/geometry.lisp`: `cl-mpm/bc::make-outside-bc-var`, `make-bc-fixed` | Existing order supplies left/right x rollers, top free and bottom fixed. New small geometry owner may use the same calls directly. Audit bottom/top order and particle support. No penalty contact is needed for the bounded onset study. |
| Gravity ramp | `src/transfer/p2g.lisp`: `p2g-force`; `src/transfer/forces.lisp`: `det-ext-force-2d` | Body acceleration uses **sim-gravity** times mass and `mp-gravity-axis`, plus body force. Set `(sim-gravity sim)=-g*ramp(t)` before actual updates; default axis `(0,1,0)` gives downward gravity. Changing only `mp-gravity` does not implement this ramp. Keep body force zero. |
| Explicit advancement | `scenarios/slope-descent/runner.lisp`: `stable-dt`; `src/geometry/setup.lisp`: `estimate-elastic-dt`; `cl-mpm:update-sim` | Native dt uses current particle modulus/density and BC minimum estimates. Advance to the next save time using `min(stable-dt,target-time-current-time)`. Keep one update budget and honest incomplete/error manifest. Do not import the prescribed-strip runner. |
| Force residual | `scenarios/slope-descent/geometry.lisp`: `slope-sim`, its `update-node-forces :after` method | Available residual diagnostic measures free DOFs before fixed BCs erase forces. A new run-local subclass can reuse/inherit it; document the dependency or extract only as a separate reviewed reuse step. Residual zero at ramp start is not equilibrium. |
| Material/VTK output | `materials/diagnostics/native.lisp`: `material-diagnostics`, `validate-material-state`; `src/measurements/material-output.lisp`: `configure-material-output` | Native MC-evolution diagnostics already report kappa, cohesion, phi/psi, plastic volume/work and corrected yield residual. `cl-mpm/output:save-vtk` provides native saved coordinates; add a scenario-owned full F9/J/stress/ID CSV rather than claiming the Wang-only exporter handles this model. |
| Aggregate history | `scenarios/slope-descent/runner.lisp`: `state-statistics`, `material-signature`, `write-gravity-state`; `src/output/retained-history.lisp` | Reuse only MC-compatible read-only measurements and retained stream pattern. A new manifest/history should record actual time, ramp factor, mass/count/J/energy and physical motion. No origin reset is needed for this independent zero-stress gravity run. |
| Windows CLI and provenance | `scripts/run-case.lisp`, `scripts/lisp/native-source-snapshot.lisp`, `windows/cl-mpm.cmd` | Existing CLI freezes trusted case, all loaded sources and mapped native DLL before execution. Add new scenario files to `cl-mpm-framework.asd` serial components so snapshot planning includes them. Use a new output directory every attempt. |

Suggested minimal source files are `scenarios/gravity-slope/{package,
configuration,geometry,measurements,runner,adapter}.lisp` plus two concise
case files and one source/input contract JSON. Keep law creation as a reusable
material helper only if reused; avoid creating a nominal new soil model merely
to wrap a constant existing law. No production file was changed by this audit.

## Required gates and limits

1. Zero-update contracts prove no notch/driver/body force/removed layer,
   initial polygon and analytical mass/quadrature, SRF law values, and explicit
   BC masks. Verify neither geometry nor contacts silently retain the Wang strip.
2. Focused new tests cover SSR c/tan(phi) conversion, native constant Cauchy
   strength under varying J, gravity-ramp force sums, default/old-case
   compatibility and actual tiny native updates. Do not rerun unrelated passed
   Wang or Node suites for an additive recipe without relevant changes.
3. First native pilot is bounded, with physical time, actual VTK/CSV and frozen
   provenance. A constitutive rejection remains a failure to diagnose once;
   do not clamp tension, change psi, or switch model to make the movie continue.
4. Predefine coherent motion of a mass fraction above the bottom support band,
   sustained downslope velocity/displacement after ramp completion, internal
   localization, toe-front advance, stable IDs/mass and positive finite J.
   Neither exit0, yielded particles nor one speed outlier proves a landslide.
5. SRF1.40 onset is not a calibrated runout benchmark. Fixed-base influence,
   coarse particles, explicit inertia, ramp duration, damping, locking, mesh,
   time step and empty-domain extent need follow-up sensitivity. If motion is
   absent, retain that result; it does not justify concealed extra weakening.

Sources: [Griffiths & Lane1999](https://doi.org/10.1680/geot.1999.49.3.387),
[Xie, Navas & Lopez-Querol2023](https://doi.org/10.1002/nag.3599).
All new benchmark execution and physical failure verification remain **NOT_RUN**.
