# Engine fit for an unnotched landslide benchmark

Read-only repository audit, 24 October 2026. Audited branch:
`codex/wang2017-soil2-landslide`, HEAD
`41eb0646f6867c4e7ca62c8923abc967d19d053b`. Live `origin/main` returned
`9e97e001c2eaf9be81c7b7e39e32fa87f2d6f64b` from `git ls-remote`.
No new solver, replay, tests, production changes or paper-reproduction claim.
The failed Wang evidence remains immutable. Primary-paper selection is a
separate review; this note makes no assumptions about its dimensions or values.

## Recommended fit

A separate **gravity-slope scenario** is a good fit for the existing native
engine. Reuse the material factory, particle clipping, explicit updates,
retained-history writer, native source freezing and actual VTK infrastructure.
Declare initialization, basal boundary and physical observation stage in the
new recipe. Do not reuse the Wang actuator or call the old creep demonstration
a reproduction of a rate-independent soil law.

For a homogeneous cohesive, pressure-independent benchmark, existing
`particle-mc-evolution` at **phi=psi=0** supplies a Tresca-type material, including
tabulated cohesion evolution. A new constitutive algorithm is not automatically
needed. Whether this matches the selected journal model, its strain coordinate,
stress measure and flow rule must be decided from that paper first.

## What can be reused, and what needs an adapter

| Concern | Actual repository capability | Required boundary on reuse |
|---|---|---|
| Composition | `src/simulation/lifecycle.lisp`: generic `compile-scenario` / `execute-scenario`; fresh-output protection. `materials/adapters/native.lisp`: native class/initargs and MC H/HS factories. | Add a small named scenario and a declarative case; preserve all old defaults. No global overrides. |
| MC / cohesive soil | `materials/models/plastic/mohr-coulomb-evolution/law.lisp`: `:perfect`, `:h`, `:hs`, explicit cohesion/angle tables, psi and Cauchy/Kirchhoff declaration. `projection.lisp`: six-plane return and accumulated equivalent plastic increment norm. | Constant zero phi/psi and a cohesion table are supported. `mc-kappa` is accumulated `sqrt(2/3)||dev delta_ep||`; native VM scalar is `1.5*mc-kappa`. Map the paper history explicitly. |
| Existing phi=0 controls | `tests/materials/mc-evolution-points.lisp:284–305,405–417` contain analytical Tresca face, permutation and native engineering-shear controls. | These are existing test definitions, not a newly executed gate. Add only missing law/coordinate or contact controls after paper selection; do not repeat unrelated suites. |
| J2 softening clay | `materials/models/viscoplastic/clay-creep/law.lisp` implements Perzyna overstress, Kirchhoff q-strength and accumulated equivalent viscoplastic strain; `particle.lisp` has transactional native state. | It has viscosity and a different yield surface. It is not interchangeable with Tresca, effective-stress soil or a rate-independent softening law. A journal-specific rate-independent J2 law may need a separate adapter/model. |
| Unnotched geometry | `scenarios/slope-descent/geometry.lisp` clips a homogeneous block to a crest/slope/base profile. `scenarios/cliff/geometry.lisp` separates face and toe-notch removal; notch cutting is skipped for zero notch height. Generic clipping hooks also exist. | Existing slope profiles include a deformable base layer. A body on a rigid bed must not silently retain that extra layer. Declare free air/runout extent and no notch, excavation, removed weak strip or hidden perturbation. |
| Gravity-only orchestration | `scenarios/slope-creep/runner.lisp` has actual gravity-only observation, residual/kinetic settling checks and reporting reset; it explicitly accepts only `particle-clay-creep`. | Reuse patterns, not its material-specific runner unchanged. New gravity-slope runner must accept the selected material and no crest actuator. |
| Existing MC cliff runner | `scenarios/cliff/execute.lisp` has elastic gravity initialization, plastic activation and subsequent native dynamics. | It uses fixed-count settling, fixed top/bottom grid nodes, side rollers and built-in settling/dynamic damping. It is not automatically the journal initialization/contact protocol. Inactive top nodes initially lie in air; they are still a finite grid boundary. |
| Wang descent runner | `scenarios/slope-descent/runner.lisp` preserves gravity state and audits residual/kinetic convergence. | It always creates a prescribed strip. Disabling its display or renaming the case does not remove external loading. Prefer the separate gravity recipe. |
| Coulomb basal contact | `src/boundaries/penalty/penalty.lisp:468–626`: compression-only normal penalty, stored tangential contact force, stick/slip cap `|Ft| <= mu*Fn`, grid mapping. Plane/line constructors and contact timestep estimates exist. | Add a run-local flat-bed boundary adapter and contact audit. Do not also fix horizontal basal DOFs, which would prevent sliding independently of mu. Check contact area/sampling and penalty sensitivity. |
| Misleading friction name | `src/boundaries/constraints/bc.lisp:282–309`, `bc-friction`, subtracts tangential motion scaled by `mu*h`; its normal-force term is commented out. | **This is not the basal Coulomb cap above.** Do not use it as evidence of Coulomb friction. |
| SSR alternative | The located `run-strength-reduction` in `src/solvers/dynamic-relaxation/algorithms.lisp:991` is entirely commented out; its default loading function scales gravity. | There is no demonstrated headless SSR scenario to reuse. Add explicit source-based strength-reduction orchestration, equilibrium/failure bracketing and rollback if this benchmark is chosen. SSR collapse onset and dynamic runout are separate claims. |

## Small additive structure

Suggested ownership, subject to the selected paper:

- `cases/benchmarks/<paper>-unnotched.lisp`: the concise component assignments.
- `scenarios/gravity-slope/{package,configuration,geometry,boundary,initialization,measurements,runner,adapter}.lisp`:
  only genuinely needed files; reuse stable helpers rather than copying full old runners.
- `materials/adapters/<paper>.lisp` only if units/history/diagnostics need a
  named mapping. Keep the law under `materials/models/`; a contact coefficient
  belongs to the boundary, not the constitutive strength table.
- A generic per-ID material/contact audit beside the scenario. The current
  `wang2017-output.lisp` is intentionally Wang-only and no-ops for other models;
  it cannot silently provide full F/state proof for a new MC/J2 scenario.

## Gates before an expensive run

1. **Source/input contract:** extract paper geometry, material, stress/strain
   conventions, initialization, contact and failure metrics; flag missing
   quantities as assumptions. Zero-update case validation must prove no notch,
   no actuator, expected body/base geometry, mass/count, boundary DOFs,
   coefficient units and selected law. Do not choose parameters to obtain a
   desired movie.
2. **Material mapping:** use the existing analytical controls as references;
   execute focused new point/native checks only for new mappings. Verify
   simple shear and compression, coordinate/strength knots, residual tail,
   objectivity, finite/J handling, plastic-volume/work signs and rollback.
   J2, Tresca, Wang signed tensor norm and accumulated increment norms must not
   share a mislabeled strain axis. Reject ambiguous/inadmissible returns.
3. **Contact:** tiny actual sliding-block controls for zero friction, sticking,
   sliding cap, reversal and separation; verify normal direction, force/grid
   sum, non-tension, dissipative tangential work, no double essential constraint,
   contact-state ownership and conservative elastic/contact timestep. The
   current slope helper uses only elastic timestep estimates; do not assume it
   accounts for a newly added stiff bed.
4. **Initialization/transition:** implement the paper's protocol explicitly.
   If elastic settling followed by plastic activation is selected, retain
   gravity residual/kinetic history and prove the reporting reset preserves
   stress/F/internal state. This may release an overstressed state; it is not
   evidence of an initially plastic equilibrium. If a retaining wall is used,
   its release must be a declared physical initial condition, never a hidden
   damage seed. Abort failed initialization rather than invent equilibrium.
5. **Bounded pilot:** genuine native updates and saved VTK/CSV with IDs, mass,
   positions/velocities, full F/J, stress, history, current strength and contact
   forces/gaps/work. Save incomplete failures honestly. Verify a short stable
   control and selected constitutive/contact response before a full case.
6. **Physical result:** predefine free-body subsets and measure coherent
   downslope translation, localization/mechanism, velocity distribution,
   toe/front advance and runout after external work stops. Colour, a maximum
   speed, yielded fraction or solver exit0 alone is not a landslide. Use actual
   coordinates/scale1 media and ID alignment. Retain a stable/no-softening
   control where scientifically appropriate. Subsequently examine mesh,
   particles-per-cell, timestep, contact penalty, domain and damping sensitivity
   without changing acceptance tolerances after results.

## Limits that remain explicit

Current single-phase total-stress soil does not solve pore pressure,
consolidation, drainage or coupled saturated-undrained flow. Choosing phi=0 or
nu near0.5 does not add those equations. Near-incompressibility and the current
F-bar-disabled slope recipes also require numerical scrutiny rather than a
claim of incompressibility.

MC/J2 softening is local: no journal-specific internal length or objective
mesh regularization was established by this audit. Dynamic runout can depend
on grid, damping, contact sampling and finite boundaries. Existing mass scaling
must remain explicitly1 unless a separate justified study is declared.

The old Wang100mm result already demonstrates why source/output integrity,
residual strength and a reaction drop are insufficient: its91 saved states are
consistent, yet no coherent free-mass runout was verified. A new unnotched
benchmark should be selected for a complete, inspectable physical specification,
not as an excuse to tune strengths until collapse appears.
